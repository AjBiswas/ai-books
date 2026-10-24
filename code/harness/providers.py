"""Provider adapters (Chapter 5): one interface, many models.

- MockProvider: offline, scripted. Used by every demo and test in the book.
- AnthropicProvider: Claude via the official `anthropic` SDK.
- OpenAICompatProvider: the Chat Completions shape, which OpenAI, vLLM, Ollama and Gemini's
  OpenAI-compatible endpoint all speak. Point `base_url` at the server you want.

SDKs are imported lazily so the harness runs without them installed.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Callable, Iterable

from .tokens import estimate_tokens
from .types import Message, Response, ToolCall, Usage


class Provider(ABC):
    name = "provider"

    @abstractmethod
    def complete(self, *, model: str, system: str, messages: list[Message],
                 tools: list[dict] | None = None, max_tokens: int = 1024, **opts) -> Response:
        """tools: list of {"name", "description", "schema"} dicts (see ToolRegistry.specs)."""


# --------------------------------------------------------------------------- mock

ScriptFn = Callable[[str, list[Message], list[dict] | None], Response | str]


class MockProvider(Provider):
    """A fake model for tests and demos.

    `script` is either a callable (system, messages, tools) -> Response | str, or a list of
    Responses/strings returned in order. Usage is estimated from the text so cost maths works.
    """
    name = "mock"

    def __init__(self, script: ScriptFn | Iterable[Response | str], fail_times: int = 0):
        self._fn = script if callable(script) else None
        self._queue = None if callable(script) else list(script)
        self.calls: list[dict] = []
        self._fail_times = fail_times   # raise this many times first (to test fallbacks)

    def complete(self, *, model, system, messages, tools=None, max_tokens=1024, **opts):
        self.calls.append({"model": model, "system": system, "messages": list(messages), "tools": tools, "opts": opts})
        if self._fail_times > 0:
            self._fail_times -= 1
            raise ConnectionError("mock provider unavailable")
        out = self._fn(system, messages, tools) if self._fn else self._queue.pop(0)
        if isinstance(out, str):
            out = Response(text=out, tool_calls=[], stop_reason="end_turn", usage=Usage(), model=model)
        if out.usage.total == 0:
            prompt = system + "".join(m.content + json.dumps([c.input for c in m.tool_calls]) for m in messages)
            if tools:
                prompt += json.dumps(tools, sort_keys=True)
            out.usage = Usage(input_tokens=estimate_tokens(prompt),
                              output_tokens=estimate_tokens(out.text + json.dumps([c.input for c in out.tool_calls])))
        out.model = model
        return out


def tool_call(name: str, input: dict, id: str | None = None, text: str = "") -> Response:
    """Helper for scripts: a Response asking for one tool call."""
    return Response(text=text, tool_calls=[ToolCall(id or f"call_{name}", name, input)],
                    stop_reason="tool_use", usage=Usage(), model="")


# --------------------------------------------------------------------------- anthropic

class AnthropicProvider(Provider):
    """Claude via the Messages API. Sampling knobs (temperature/top_p/top_k) are not sent:
    current Claude models reject them; depth is controlled with `effort` instead."""
    name = "anthropic"

    def __init__(self, client=None):
        if client is None:
            import anthropic  # lazy
            client = anthropic.Anthropic()
        self.client = client

    @staticmethod
    def to_wire(messages: list[Message]) -> list[dict]:
        out: list[dict] = []
        for m in messages:
            if m.role == "user":
                out.append({"role": "user", "content": m.content})
            elif m.role == "assistant":
                blocks: list[dict] = []
                if m.content:
                    blocks.append({"type": "text", "text": m.content})
                for c in m.tool_calls:
                    blocks.append({"type": "tool_use", "id": c.id, "name": c.name, "input": c.input})
                out.append({"role": "assistant", "content": blocks or m.content})
            elif m.role == "tool":
                block = {"type": "tool_result", "tool_use_id": m.tool_call_id, "content": m.content}
                if m.is_error:
                    block["is_error"] = True
                # All results for one assistant turn go back in a single user message.
                if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list) \
                        and out[-1]["content"] and out[-1]["content"][0].get("type") == "tool_result":
                    out[-1]["content"].append(block)
                else:
                    out.append({"role": "user", "content": [block]})
        return out

    def complete(self, *, model, system, messages, tools=None, max_tokens=16000, **opts):
        kwargs: dict = {"model": model, "max_tokens": max_tokens, "system": system,
                        "messages": self.to_wire(messages)}
        if tools:
            kwargs["tools"] = [{"name": t["name"], "description": t["description"],
                                "input_schema": t["schema"]} for t in tools]
        if opts.get("cache", True):
            kwargs["cache_control"] = {"type": "ephemeral"}   # auto-cache the stable prefix
        if opts.get("effort"):
            kwargs["output_config"] = {"effort": opts["effort"]}
        r = self.client.messages.create(**kwargs)
        text, calls = [], []
        for b in r.content:
            if b.type == "text":
                text.append(b.text)
            elif b.type == "tool_use":
                calls.append(ToolCall(b.id, b.name, dict(b.input)))
        u = r.usage
        usage = Usage(u.input_tokens, u.output_tokens,
                      getattr(u, "cache_read_input_tokens", 0) or 0,
                      getattr(u, "cache_creation_input_tokens", 0) or 0)
        return Response("".join(text), calls, r.stop_reason or "end_turn", usage, model, raw=r)


# --------------------------------------------------------------------------- openai-compatible

class OpenAICompatProvider(Provider):
    """Chat Completions shape: OpenAI, vLLM, Ollama, Gemini (OpenAI-compatible endpoint)."""
    name = "openai-compat"

    def __init__(self, client=None, base_url: str | None = None, api_key: str | None = None):
        if client is None:
            import openai  # lazy
            client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.client = client

    @staticmethod
    def to_wire(system: str, messages: list[Message]) -> list[dict]:
        out: list[dict] = [{"role": "system", "content": system}] if system else []
        for m in messages:
            if m.role == "user":
                out.append({"role": "user", "content": m.content})
            elif m.role == "assistant":
                d: dict = {"role": "assistant", "content": m.content or None}
                if m.tool_calls:
                    d["tool_calls"] = [{"id": c.id, "type": "function",
                                        "function": {"name": c.name, "arguments": json.dumps(c.input)}}
                                       for c in m.tool_calls]
                out.append(d)
            elif m.role == "tool":
                content = ("ERROR: " + m.content) if m.is_error else m.content
                out.append({"role": "tool", "tool_call_id": m.tool_call_id, "content": content})
        return out

    _STOP = {"stop": "end_turn", "tool_calls": "tool_use", "length": "max_tokens", "content_filter": "refusal"}

    def complete(self, *, model, system, messages, tools=None, max_tokens=4096, **opts):
        kwargs: dict = {"model": model, "messages": self.to_wire(system, messages), "max_tokens": max_tokens}
        if tools:
            kwargs["tools"] = [{"type": "function", "function": {
                "name": t["name"], "description": t["description"], "parameters": t["schema"]}} for t in tools]
        if "temperature" in opts:     # still meaningful for self-hosted models
            kwargs["temperature"] = opts["temperature"]
        r = self.client.chat.completions.create(**kwargs)
        choice = r.choices[0]
        calls = [ToolCall(tc.id, tc.function.name, json.loads(tc.function.arguments or "{}"))
                 for tc in (choice.message.tool_calls or [])]
        u = r.usage
        cached = getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", 0) or 0
        usage = Usage(u.prompt_tokens - cached, u.completion_tokens, cached, 0)
        return Response(choice.message.content or "", calls, self._STOP.get(choice.finish_reason, "end_turn"),
                        usage, model, raw=r)

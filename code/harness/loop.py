"""The agent loop (Chapter 6): ask the model, run tools, repeat, and stop for a good reason."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

from .hooks import Deny, HookBus, Modify
from .pricing import PRICES, cost_usd
from .providers import Provider
from .tools import ToolRegistry
from .types import Message, ToolCall, Usage


@dataclass
class AgentConfig:
    model: str
    system: str = "You are a helpful assistant."
    max_steps: int = 10                 # hard cap on model calls
    max_tokens: int = 1024              # per response
    token_budget: int | None = None     # total tokens for the whole run
    permission_mode: str = "default"
    repeat_limit: int = 3               # same tool call this many times = stuck


@dataclass
class RunResult:
    text: str
    stop_reason: str            # done | max_steps | budget | stuck | refusal | max_tokens
    steps: int
    usage: Usage
    cost_usd: float
    transcript: list[Message] = field(default_factory=list)


class Agent:
    def __init__(self, provider: Provider, tools: ToolRegistry | None = None, config: AgentConfig | None = None,
                 hooks: HookBus | None = None, context=None, approver: Callable[[ToolCall], bool] | None = None):
        self.provider = provider
        self.tools = tools or ToolRegistry()
        self.config = config or AgentConfig(model="mock-medium")
        self.hooks = hooks or HookBus()
        self.context = context          # optional ContextManager (Chapter 8)
        self.approver = approver

    def run(self, task: str, history: list[Message] | None = None) -> RunResult:
        cfg = self.config
        messages = list(history or []) + [Message("user", task)]
        usage = Usage()
        seen: dict[str, int] = {}
        last_text = ""

        def result(reason: str, steps: int) -> RunResult:
            cost = cost_usd(cfg.model, usage) if cfg.model in PRICES else 0.0
            self.hooks.emit("stop", reason=reason, usage=usage)
            return RunResult(last_text, reason, steps, usage, cost, messages)

        for step in range(1, cfg.max_steps + 1):
            if cfg.token_budget is not None and usage.total >= cfg.token_budget:
                return result("budget", step - 1)
            to_send = self.context.prepare(messages) if self.context else messages
            self.hooks.emit("pre_request", step=step, messages=to_send)
            resp = self.provider.complete(model=cfg.model, system=cfg.system, messages=to_send,
                                          tools=self.tools.specs() or None, max_tokens=cfg.max_tokens)
            usage = usage + resp.usage
            last_text = resp.text or last_text
            self.hooks.emit("post_response", step=step, response=resp)
            messages.append(Message("assistant", resp.text, tool_calls=resp.tool_calls))

            if resp.stop_reason in ("refusal", "max_tokens") and not resp.tool_calls:
                return result(resp.stop_reason, step)
            if not resp.tool_calls:
                return result("done", step)

            for call in resp.tool_calls:
                key = call.name + json.dumps(call.input, sort_keys=True)
                seen[key] = seen.get(key, 0) + 1
                if seen[key] >= cfg.repeat_limit:
                    messages.append(Message("tool", "Stopped: identical call repeated", call.id, is_error=True))
                    return result("stuck", step)
                verdicts = self.hooks.emit("pre_tool", call=call, messages=messages)
                deny = next((v for v in verdicts if isinstance(v, Deny)), None)
                for v in verdicts:
                    if isinstance(v, Modify):
                        call.input = v.input
                if deny:
                    content, err = f"Blocked by policy: {deny.reason}", True
                else:
                    content, err = self.tools.execute(call, cfg.permission_mode, self.approver)
                self.hooks.emit("post_tool", call=call, content=content, is_error=err)
                messages.append(Message("tool", content, tool_call_id=call.id, is_error=err))
        return result("max_steps", cfg.max_steps)

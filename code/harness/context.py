"""Context engineering (Chapter 8): ordering, retrieval, compaction."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from typing import Callable

from .tokens import estimate_tokens
from .types import Message


def build_system(rules: str, documents: list[str] | None = None) -> str:
    """Stable-to-volatile: rules first, then reference documents. Anything that changes per
    request (date, user name, request id) belongs in the user turn, never here."""
    parts = [rules.strip()]
    for i, d in enumerate(documents or [], 1):
        parts.append(f"<document index=\"{i}\">\n{d.strip()}\n</document>")
    return "\n\n".join(parts)


def serialize(system: str, tools: list[dict] | None, messages: list[Message]) -> str:
    """The byte sequence a provider would see, in render order tools -> system -> messages."""
    body = [json.dumps(tools or [], sort_keys=True), system]
    for m in messages:
        body.append(json.dumps({"r": m.role, "c": m.content, "t": [[c.name, c.input] for c in m.tool_calls],
                                "id": m.tool_call_id}, sort_keys=True, ensure_ascii=False))
    return "\n".join(body)


def shared_prefix_tokens(prev: str, cur: str) -> int:
    """How much of `cur` could come from the prompt cache written by `prev`."""
    n = 0
    for a, b in zip(prev, cur):
        if a != b:
            break
        n += 1
    return estimate_tokens(cur[:n])


def messages_tokens(messages: list[Message]) -> int:
    return sum(estimate_tokens(m.content) + estimate_tokens(json.dumps([c.input for c in m.tool_calls]))
               for m in messages)


def default_summarizer(old: list[Message]) -> str:
    lines = []
    for m in old:
        if m.role == "tool":
            lines.append(f"- tool result: {m.content[:120]}")
        elif m.tool_calls:
            lines.append("- assistant called " + ", ".join(f"{c.name}({json.dumps(c.input)[:60]})" for c in m.tool_calls))
        elif m.content:
            lines.append(f"- {m.role}: {m.content[:160]}")
    return "\n".join(lines)


class ContextManager:
    """Keeps the request under `max_tokens` by replacing old turns with a summary.

    Never splits an assistant tool call from its tool results: the cut point is always
    a plain user turn.
    """

    def __init__(self, max_tokens: int = 8000, keep_recent: int = 6,
                 summarizer: Callable[[list[Message]], str] = default_summarizer):
        self.max_tokens = max_tokens
        self.keep_recent = keep_recent
        self.summarizer = summarizer
        self.compactions = 0

    def prepare(self, messages: list[Message]) -> list[Message]:
        if messages_tokens(messages) <= self.max_tokens or len(messages) <= self.keep_recent + 1:
            return messages
        cut = len(messages) - self.keep_recent
        while cut > 1 and not (messages[cut].role == "user"):
            cut -= 1
        if cut <= 1:
            return messages
        first, old, recent = messages[0], messages[1:cut], messages[cut:]
        self.compactions += 1
        summary = Message("user", "[Summary of earlier work]\n" + self.summarizer(old))
        ack = Message("assistant", "Understood. Continuing from the summary.")
        return [first, summary, ack] + recent


_WORD = re.compile(r"\w+", re.UNICODE)


def _tok(s: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(s)]


class BM25:
    """Keyword retrieval, good enough to teach RAG and often a strong baseline in practice."""

    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.docs = docs
        self.k1, self.b = k1, b
        self.tf = [Counter(_tok(d)) for d in docs]
        self.len = [sum(t.values()) for t in self.tf]
        self.avg = sum(self.len) / max(1, len(docs))
        df = Counter(w for t in self.tf for w in t)
        n = len(docs)
        self.idf = {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}

    def search(self, query: str, k: int = 3) -> list[tuple[float, int]]:
        q = _tok(query)
        scores = []
        for i, tf in enumerate(self.tf):
            s = 0.0
            for w in q:
                if w in tf:
                    f = tf[w]
                    s += self.idf[w] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
            scores.append((s, i))
        return sorted((x for x in scores if x[0] > 0), reverse=True)[:k]

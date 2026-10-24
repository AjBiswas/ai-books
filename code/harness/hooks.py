"""Lifecycle hooks (Chapter 10).

Events: pre_request, post_response, pre_tool, post_tool, stop.
A pre_tool hook may return Deny(reason) to block a call, or Modify(input) to rewrite it.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable

EVENTS = ("pre_request", "post_response", "pre_tool", "post_tool", "stop")


@dataclass
class Deny:
    reason: str


@dataclass
class Modify:
    input: dict


class HookBus:
    def __init__(self):
        self._hooks: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    def on(self, event: str, fn: Callable[..., Any] | None = None):
        assert event in EVENTS, event
        if fn is None:
            def deco(f):
                self._hooks[event].append(f)
                return f
            return deco
        self._hooks[event].append(fn)
        return fn

    def emit(self, event: str, **payload) -> list[Any]:
        return [r for fn in self._hooks[event] if (r := fn(**payload)) is not None]

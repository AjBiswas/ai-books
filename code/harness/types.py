"""Provider-neutral message types (Chapter 5).

Every provider adapter converts to and from these, so the rest of the harness never sees
a vendor-specific shape.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class Usage:
    input_tokens: int = 0          # uncached input, billed at full price
    output_tokens: int = 0
    cache_read_tokens: int = 0     # input served from the prompt cache
    cache_write_tokens: int = 0    # input written to the prompt cache

    def __add__(self, o: "Usage") -> "Usage":
        return Usage(
            self.input_tokens + o.input_tokens,
            self.output_tokens + o.output_tokens,
            self.cache_read_tokens + o.cache_read_tokens,
            self.cache_write_tokens + o.cache_write_tokens,
        )

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens + self.cache_read_tokens + self.cache_write_tokens


@dataclass
class Message:
    role: str                                   # "user" | "assistant" | "tool"
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)   # assistant only
    tool_call_id: str | None = None             # tool only: which call this answers
    is_error: bool = False                      # tool only


@dataclass
class Response:
    text: str
    tool_calls: list[ToolCall]
    stop_reason: str            # "end_turn" | "tool_use" | "max_tokens" | "refusal"
    usage: Usage
    model: str
    raw: Any = None

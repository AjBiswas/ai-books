"""Model routing and fallback (Chapter 11)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")

HARD_HINTS = re.compile(r"\b(prove|architect|design|debug|refactor|analy[sz]e|compare|plan|multi-step|why)\b", re.I)
EASY_HINTS = re.compile(r"\b(classify|translate|extract|summari[sz]e|yes or no|label)\b", re.I)


def complexity(text: str) -> float:
    """0 = trivial, 1 = hard. A cheap heuristic; production routers often use a small classifier."""
    score = min(len(text) / 4000, 0.4)
    score += 0.5 * min(len(HARD_HINTS.findall(text)), 3) / 3
    score -= 0.25 * bool(EASY_HINTS.search(text))
    score += 0.15 * ("```" in text)
    return max(0.0, min(1.0, score + 0.2))


@dataclass
class Tier:
    model: str
    max_complexity: float       # use this tier up to this score


class Router:
    def __init__(self, tiers: list[Tier], fallbacks: dict[str, list[str]] | None = None):
        self.tiers = sorted(tiers, key=lambda t: t.max_complexity)
        self.fallbacks = fallbacks or {}

    def choose(self, text: str, allowed: set[str] | None = None, budget_tight: bool = False) -> str:
        c = complexity(text)
        candidates = [t for t in self.tiers if allowed is None or t.model in allowed]
        if not candidates:
            raise ValueError("no allowed model")
        if budget_tight:
            return candidates[0].model
        for t in candidates:
            if c <= t.max_complexity:
                return t.model
        return candidates[-1].model

    def call_with_fallback(self, model: str, fn: Callable[[str], T],
                           retryable: tuple[type[Exception], ...] = (ConnectionError, TimeoutError)) -> tuple[str, T]:
        chain = [model] + self.fallbacks.get(model, [])
        last: Exception | None = None
        for m in chain:
            try:
                return m, fn(m)
            except retryable as e:
                last = e
        raise RuntimeError(f"all models failed: {chain}") from last

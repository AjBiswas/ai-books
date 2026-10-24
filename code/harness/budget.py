"""Token budgets and FinOps (Chapter 13): rate limits, hierarchical quotas, chargeback."""
from __future__ import annotations

import time
from dataclasses import dataclass, field


class TokenBucket:
    """Requests-or-tokens per second limiter. `capacity` is the burst, `rate` the refill per second."""

    def __init__(self, capacity: float, rate: float, now: float | None = None):
        self.capacity, self.rate = capacity, rate
        self.level = capacity
        self.t = time.monotonic() if now is None else now

    def allow(self, cost: float = 1.0, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        self.level = min(self.capacity, self.level + (now - self.t) * self.rate)
        self.t = now
        if self.level >= cost:
            self.level -= cost
            return True
        return False


@dataclass
class Limit:
    usd: float                  # spend limit for the period
    warn_at: float = 0.8        # soft limit as a fraction


@dataclass
class Check:
    ok: bool
    scope: str = ""             # which scope blocked or warned
    level: str = "ok"           # ok | warn | block
    remaining_usd: float = float("inf")


@dataclass
class Ledger:
    """Scopes are paths like "acme", "acme/payments", "acme/payments/riya".
    A request is charged to every ancestor, and blocked if any ancestor is over its limit."""
    limits: dict[str, Limit] = field(default_factory=dict)
    spent: dict[str, float] = field(default_factory=dict)
    tokens: dict[str, int] = field(default_factory=dict)

    @staticmethod
    def ancestors(path: str) -> list[str]:
        parts = path.split("/")
        return ["/".join(parts[: i + 1]) for i in range(len(parts))]

    def set_limit(self, scope: str, usd: float, warn_at: float = 0.8):
        self.limits[scope] = Limit(usd, warn_at)

    def check(self, path: str, estimated_usd: float = 0.0) -> Check:
        worst = Check(True)
        for scope in self.ancestors(path):
            lim = self.limits.get(scope)
            if not lim:
                continue
            after = self.spent.get(scope, 0.0) + estimated_usd
            remaining = lim.usd - self.spent.get(scope, 0.0)
            if after > lim.usd:
                return Check(False, scope, "block", remaining)
            if after >= lim.warn_at * lim.usd and worst.level == "ok":
                worst = Check(True, scope, "warn", remaining)
            worst.remaining_usd = min(worst.remaining_usd, remaining)
        return worst

    def record(self, path: str, usd: float, tokens: int):
        for scope in self.ancestors(path):
            self.spent[scope] = self.spent.get(scope, 0.0) + usd
            self.tokens[scope] = self.tokens.get(scope, 0) + tokens

    def chargeback(self, depth: int = 2) -> list[tuple[str, float, int]]:
        rows = [(s, self.spent[s], self.tokens[s]) for s in self.spent if s.count("/") == depth - 1]
        return sorted(rows, key=lambda r: -r[1])

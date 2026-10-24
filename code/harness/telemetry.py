"""Observability (Chapter 17): spans with OpenTelemetry GenAI attribute names, cost roll-ups, drift."""
from __future__ import annotations

import json
import math
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str
    parent_id: str | None
    start: float
    end: float = 0.0
    attrs: dict = field(default_factory=dict)
    status: str = "ok"

    @property
    def ms(self) -> float:
        return (self.end - self.start) * 1000


class Tracer:
    def __init__(self, clock=time.perf_counter):
        self.spans: list[Span] = []
        self._stack: list[Span] = []
        self.clock = clock

    @contextmanager
    def span(self, name: str, **attrs):
        parent = self._stack[-1] if self._stack else None
        s = Span(name, parent.trace_id if parent else uuid.uuid4().hex[:16], uuid.uuid4().hex[:8],
                 parent.span_id if parent else None, self.clock(), attrs=dict(attrs))
        self._stack.append(s)
        try:
            yield s
        except Exception as e:
            s.status = f"error: {type(e).__name__}"
            raise
        finally:
            s.end = self.clock()
            self._stack.pop()
            self.spans.append(s)

    def export_jsonl(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            for s in self.spans:
                f.write(json.dumps(s.__dict__, default=str) + "\n")

    def rollup(self, key: str = "gen_ai.request.model") -> dict[str, dict]:
        out: dict[str, dict] = {}
        for s in self.spans:
            if "gen_ai.usage.input_tokens" not in s.attrs:
                continue
            k = s.attrs.get(key, "?")
            r = out.setdefault(k, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "ms": []})
            r["calls"] += 1
            r["input_tokens"] += s.attrs["gen_ai.usage.input_tokens"]
            r["output_tokens"] += s.attrs.get("gen_ai.usage.output_tokens", 0)
            r["cost_usd"] += s.attrs.get("harness.cost_usd", 0.0)
            r["ms"].append(s.ms)
        for r in out.values():
            ms = sorted(r.pop("ms"))
            r["p50_ms"] = ms[len(ms) // 2]
            r["p95_ms"] = ms[min(len(ms) - 1, int(0.95 * len(ms)))]
        return out


def psi(expected: list[float], actual: list[float], bins: int = 10) -> float:
    """Population Stability Index between two samples. Rule of thumb: <0.1 stable,
    0.1-0.25 watch, >0.25 drifted."""
    lo = min(expected + actual)
    hi = max(expected + actual)
    width = (hi - lo) / bins or 1.0

    def hist(xs):
        h = [0] * bins
        for x in xs:
            h[min(bins - 1, int((x - lo) / width))] += 1
        return [(c + 0.5) / (len(xs) + 0.5 * bins) for c in h]   # smoothed

    e, a = hist(expected), hist(actual)
    return sum((ai - ei) * math.log(ai / ei) for ei, ai in zip(e, a))

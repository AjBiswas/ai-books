"""Chapter 17 lab: traces, a cost roll-up, and drift detection."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness.pricing import cost_usd
from harness.telemetry import Tracer, psi
from harness.types import Usage

rng = random.Random(5)
clock = [0.0]
tr = Tracer(clock=lambda: clock[0])
for i in range(300):
    model = rng.choices(["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"], [0.6, 0.3, 0.1])[0]
    with tr.span("agent.run", **{"harness.tenant": "acme"}):
        u = Usage(rng.randint(2_000, 30_000), rng.randint(100, 2_000))
        with tr.span("gen_ai.chat", **{"gen_ai.request.model": model, "gen_ai.usage.input_tokens": u.input_tokens,
                                       "gen_ai.usage.output_tokens": u.output_tokens, "harness.cost_usd": cost_usd(model, u)}):
            clock[0] += {"claude-haiku-5-5": 0.6, "claude-sonnet-5-5": 2.0, "claude-opus-5-5": 4.5}[model] * rng.uniform(0.5, 2.2)
print(f"{'model':18s} {'calls':>5s} {'in tok':>9s} {'out tok':>8s} {'cost $':>8s} {'p50 ms':>7s} {'p95 ms':>7s}")
for m, r in sorted(tr.rollup().items()):
    print(f"{m:18s} {r['calls']:5d} {r['input_tokens']:9,d} {r['output_tokens']:8,d} {r['cost_usd']:8.2f} {r['p50_ms']:7.0f} {r['p95_ms']:7.0f}")

last_month = [rng.gauss(420, 90) for _ in range(2000)]        # answer length in tokens
this_week = [rng.gauss(430, 95) for _ in range(500)]
after_update = [rng.gauss(610, 140) for _ in range(500)]
print(f"\nPSI answer length, normal week:      {psi(last_month, this_week):.3f}")
print(f"PSI answer length, after model update: {psi(last_month, after_update):.3f}  <- investigate")

"""Chapter 16 lab: a release gate. Does the new prompt beat the old one, or is it noise?"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness import MockProvider
from harness.evals import EvalCase, contains, gate, llm_judge, pass_at_k, run_suite

rng = random.Random(11)
cases = [EvalCase(f"t{i:03d}", f"Ticket {i}: customer asks about refund window", "7 days",
                  tags=["hindi" if i % 5 == 0 else "english"]) for i in range(200)]


def system_v1(case):                       # baseline: right 82% of the time
    return "Refunds are accepted within 7 days." if rng.random() < 0.82 else "Refunds take some time."


def system_v2(case):                       # new prompt: better on English, broke Hindi tickets
    if "hindi" in case.tags:
        return "Refunds take some time." if rng.random() < 0.6 else "Refund window: 7 days."
    return "Refund window: 7 days." if rng.random() < 0.93 else "Please contact support."


base = run_suite("v1 baseline", system_v1, cases, contains)
cand = run_suite("v2 candidate", system_v2, cases, contains)
print(base.summary())
print(cand.summary())
print("gate:", gate(base, cand, tolerance=0.02)[1])
hindi = [c.id for c in cases if "hindi" in c.tags]
for rep in (base, cand):
    print(f"  {rep.name:13s} Hindi slice: {sum(rep.scores[i] for i in hindi) / len(hindi):.0%}")

judge = llm_judge(MockProvider(lambda s, m, t: "PASS\nMentions the 7-day window." if "7 days" in m[0].content.split("AI answer:")[1] else "FAIL\nMissing window."),
                  "mock-medium", "Must state the 7-day refund window.")
print("\nLLM judge on one answer:", judge(cases[1], "You can return it within 7 days."))
print("pass@1 / pass@5 with 10 samples, 3 correct:", round(pass_at_k(10, 3, 1), 2), round(pass_at_k(10, 3, 5), 2))

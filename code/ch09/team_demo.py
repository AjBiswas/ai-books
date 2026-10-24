"""Chapter 9 lab: a lead agent splits work across workers with fresh contexts."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness import MockProvider
from harness.multi import Orchestrator
from harness.pricing import cost_usd

FINDINGS = {"pricing": "Rival A cut prices 12%.", "hiring": "Rival B is hiring 300 AI engineers in Hyderabad.",
            "product": "Rival C launched a Kannada voice assistant."}


def script(system, messages, tools):
    if system.startswith("Split"):
        return '["Research competitor pricing", "Research competitor hiring", "Research competitor product launches"]'
    if system.startswith("Combine"):
        return "Market brief: " + " ".join(FINDINGS.values())
    task = messages[-1].content.lower()
    return next(v for k, v in FINDINGS.items() if k in task)


team = Orchestrator(MockProvider(script), lead_model="mock-large", worker_model="mock-small").run(
    "Write a one-paragraph competitor brief for Q3")
for i, (p, o) in enumerate(zip(team.plan, team.worker_outputs), 1):
    print(f"worker {i}: {p:40s} -> {o}")
print("\nlead:", team.answer)
print(f"total tokens {team.usage.total}")

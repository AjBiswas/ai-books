"""Multi-agent orchestration (Chapter 9): a lead splits work, workers run in fresh contexts."""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from .loop import Agent, AgentConfig
from .providers import Provider
from .tools import ToolRegistry
from .types import Message, Usage

PLAN_PROMPT = ("Split the task into at most {n} independent subtasks. "
               "Reply with only a JSON array of strings.")
SYNTH_PROMPT = "Combine the worker results into one answer for the original task."


@dataclass
class TeamResult:
    plan: list[str]
    worker_outputs: list[str]
    answer: str
    usage: Usage


class Orchestrator:
    def __init__(self, provider: Provider, lead_model: str, worker_model: str,
                 worker_tools: ToolRegistry | None = None, max_workers: int = 4):
        self.provider = provider
        self.lead_model = lead_model
        self.worker_model = worker_model
        self.worker_tools = worker_tools or ToolRegistry()
        self.max_workers = max_workers

    def run(self, task: str) -> TeamResult:
        usage = Usage()
        r = self.provider.complete(model=self.lead_model, system=PLAN_PROMPT.format(n=self.max_workers),
                                   messages=[Message("user", task)], max_tokens=512)
        usage = usage + r.usage
        try:
            plan = [str(s) for s in json.loads(r.text)][: self.max_workers]
        except (json.JSONDecodeError, TypeError):
            plan = [task]   # planning failed: fall back to one worker doing everything

        def work(sub: str):
            agent = Agent(self.provider, self.worker_tools,
                          AgentConfig(model=self.worker_model, system="You are a focused worker. Answer briefly.",
                                      max_steps=6))
            return agent.run(sub)   # each worker starts with an empty context

        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            results = list(ex.map(work, plan))
        for res in results:
            usage = usage + res.usage
        joined = "\n\n".join(f"## Subtask {i+1}: {p}\n{res.text}" for i, (p, res) in enumerate(zip(plan, results)))
        s = self.provider.complete(model=self.lead_model, system=SYNTH_PROMPT,
                                   messages=[Message("user", f"Task: {task}\n\n{joined}")], max_tokens=1024)
        usage = usage + s.usage
        return TeamResult(plan, [res.text for res in results], s.text, usage)

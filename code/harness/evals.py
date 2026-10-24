"""Evals (Chapter 16): scorers, suites, confidence intervals, regression gates."""
from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field
from math import comb
from typing import Callable

from .providers import Provider
from .tools import validate
from .types import Message

Scorer = Callable[["EvalCase", str], float]


@dataclass
class EvalCase:
    id: str
    input: str
    expected: str | None = None
    tags: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)


def exact(case: EvalCase, out: str) -> float:
    return float(out.strip().lower() == (case.expected or "").strip().lower())


def contains(case: EvalCase, out: str) -> float:
    return float((case.expected or "").lower() in out.lower())


def regex(pattern: str) -> Scorer:
    return lambda case, out: float(bool(re.search(pattern, out)))


def json_schema(schema: dict) -> Scorer:
    def score(case, out):
        try:
            return float(not validate(schema, json.loads(out)))
        except json.JSONDecodeError:
            return 0.0
    return score


JUDGE_PROMPT = """You are grading an AI answer against a rubric.
Rubric: {rubric}
Question: {q}
Reference answer: {ref}
AI answer: {a}
Reply with exactly PASS or FAIL on the first line, then one sentence of reasons."""


def llm_judge(provider: Provider, model: str, rubric: str) -> Scorer:
    def score(case, out):
        r = provider.complete(model=model, system="You are a strict grader.", max_tokens=200,
                              messages=[Message("user", JUDGE_PROMPT.format(rubric=rubric, q=case.input,
                                                                          ref=case.expected or "-", a=out))])
        return float(r.text.strip().upper().startswith("PASS"))
    return score


def bootstrap_ci(values: list[float], n: int = 2000, alpha: float = 0.05, seed: int = 0) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    means = sorted(sum(rng.choice(values) for _ in values) / len(values) for _ in range(n))
    return means[int(alpha / 2 * n)], means[int((1 - alpha / 2) * n) - 1]


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k from n samples with c correct (Chen et al., 2021)."""
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


@dataclass
class Report:
    name: str
    scores: dict[str, float]          # case id -> score
    mean: float
    ci: tuple[float, float]
    failures: list[str]

    def summary(self) -> str:
        return f"{self.name}: {self.mean:.1%} (95% CI {self.ci[0]:.1%}-{self.ci[1]:.1%}), {len(self.failures)} failed"


def run_suite(name: str, system: Callable[[EvalCase], str], cases: list[EvalCase], scorer: Scorer) -> Report:
    scores = {c.id: scorer(c, system(c)) for c in cases}
    vals = list(scores.values())
    return Report(name, scores, sum(vals) / len(vals), bootstrap_ci(vals), [k for k, v in scores.items() if v < 1])


def gate(baseline: Report, candidate: Report, tolerance: float = 0.02, n: int = 2000, seed: int = 0) -> tuple[bool, str]:
    """Paired bootstrap on per-case differences. Fail if we are 95% sure the candidate is
    worse than baseline by more than `tolerance`."""
    ids = sorted(set(baseline.scores) & set(candidate.scores))
    diffs = [candidate.scores[i] - baseline.scores[i] for i in ids]
    lo, hi = bootstrap_ci(diffs, n=n, seed=seed)
    mean = sum(diffs) / len(diffs)
    ok = lo >= -tolerance
    return ok, f"diff {mean:+.1%} (95% CI {lo:+.1%} to {hi:+.1%}) -> {'PASS' if ok else 'FAIL'}"

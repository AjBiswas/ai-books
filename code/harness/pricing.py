"""Price table and cost maths (Chapter 2).

USD per 1M tokens. Claude prices are Anthropic first-party list prices as of Oct 2026;
cache writes use the 5-minute TTL rate (1.25x input). Always confirm against the provider's
pricing page and your own contract before using these numbers for chargeback.
"""
from __future__ import annotations

from dataclasses import dataclass

from .types import Usage


@dataclass(frozen=True)
class Price:
    input: float
    output: float
    cache_read: float
    cache_write: float


PRICES: dict[str, Price] = {
    "claude-opus-5-5": Price(4.00, 20.00, 0.20, 5.00),
    "claude-sonnet-5-5": Price(2.00, 10.00, 0.20, 2.50),
    "claude-haiku-5-5": Price(0.10, 0.50, 0.01, 0.125),
    # Demo tiers used by MockProvider examples throughout the book.
    "mock-small": Price(0.10, 0.50, 0.01, 0.125),
    "mock-medium": Price(2.00, 10.00, 0.20, 2.50),
    "mock-large": Price(4.00, 20.00, 0.20, 5.00),
    # Self-hosted: an internal transfer price = (GPU-hours x hourly cost) / tokens served.
    # Illustrative only; compute yours with code/ch15/capacity.py and real utilisation.
    "vllm/onprem-70b": Price(0.60, 0.60, 0.0, 0.0),
    # Add your OpenAI / Gemini / self-hosted rates here, e.g.:
    # "gpt-x": Price(...),  "vllm/llama-3.1-70b": Price(...)  # self-hosted: GPU-hour cost / tokens served
}


def cost_usd(model: str, usage: Usage) -> float:
    p = PRICES.get(model)
    if p is None:
        raise KeyError(f"No price for model {model!r}; add it to harness.pricing.PRICES")
    return (
        usage.input_tokens * p.input
        + usage.output_tokens * p.output
        + usage.cache_read_tokens * p.cache_read
        + usage.cache_write_tokens * p.cache_write
    ) / 1_000_000

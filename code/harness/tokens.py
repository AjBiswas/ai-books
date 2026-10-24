"""Token estimation for pre-flight budget checks (Chapter 2).

These are ESTIMATES. Bill and enforce quotas from the provider's reported usage, and count
exactly with the provider's own tokenizer or token-count endpoint when precision matters.
"""
from __future__ import annotations

import unicodedata

# Rough tokens-per-character by script, from measuring common BPE tokenizers on news text.
# Latin text averages ~4 chars/token; Indic scripts often land near 1-2 chars/token.
_TOKENS_PER_CHAR = {
    "LATIN": 0.25,
    "DEVANAGARI": 0.6,
    "TAMIL": 0.7,
    "TELUGU": 0.7,
    "KANNADA": 0.7,
    "BENGALI": 0.6,
    "CJK": 0.9,
    "OTHER": 0.5,
}


def script_of(ch: str) -> str:
    if ch.isascii():
        return "LATIN"
    try:
        name = unicodedata.name(ch)
    except ValueError:
        return "OTHER"
    for s in ("DEVANAGARI", "TAMIL", "TELUGU", "KANNADA", "BENGALI"):
        if name.startswith(s):
            return s
    if name.startswith("CJK"):
        return "CJK"
    if "LATIN" in name:
        return "LATIN"
    return "OTHER"


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    total = 0.0
    for ch in text:
        total += _TOKENS_PER_CHAR[script_of(ch)]
    return max(1, round(total))


def dominant_script(text: str) -> str:
    counts: dict[str, int] = {}
    for ch in text:
        if ch.isspace() or ch.isdigit():
            continue
        s = script_of(ch)
        counts[s] = counts.get(s, 0) + 1
    return max(counts, key=counts.get) if counts else "LATIN"

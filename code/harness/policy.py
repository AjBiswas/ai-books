"""Governance (Chapter 12): PII redaction, tenant policy, data residency."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from .types import Message

# ---------------------------------------------------------------- Aadhaar check digit (Verhoeff)
_D = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 0, 6, 7, 8, 9, 5], [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
      [3, 4, 0, 1, 2, 8, 9, 5, 6, 7], [4, 0, 1, 2, 3, 9, 5, 6, 7, 8], [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
      [6, 5, 9, 8, 7, 1, 0, 4, 3, 2], [7, 6, 5, 9, 8, 2, 1, 0, 4, 3], [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
      [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]]
_P = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 5, 7, 6, 2, 8, 3, 0, 9, 4], [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
      [8, 9, 1, 6, 0, 4, 3, 5, 2, 7], [9, 4, 5, 3, 1, 2, 6, 8, 7, 0], [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
      [2, 7, 9, 3, 8, 0, 6, 4, 1, 5], [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]]
_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def verhoeff_valid(num: str) -> bool:
    c = 0
    for i, ch in enumerate(reversed(num)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c == 0


def verhoeff_check_digit(num: str) -> str:
    c = 0
    for i, ch in enumerate(reversed(num)):
        c = _D[c][_P[(i + 1) % 8][int(ch)]]
    return str(_INV[c])


def luhn_valid(num: str) -> bool:
    total, alt = 0, False
    for ch in reversed(num):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
        alt = not alt
    return total % 10 == 0


# ---------------------------------------------------------------- detectors
PII_PATTERNS: list[tuple[str, re.Pattern, object]] = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), None),
    ("AADHAAR", re.compile(r"\b[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}\b"),
     lambda s: verhoeff_valid(re.sub(r"\D", "", s))),
    ("PAN", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), None),
    ("CARD", re.compile(r"\b(?:\d[ -]?){13,19}\b"), lambda s: luhn_valid(re.sub(r"\D", "", s))),
    ("PHONE_IN", re.compile(r"(?:\+91[ -]?)?\b[6-9]\d{4}[ -]?\d{5}\b"), None),
]


def redact(text: str, vault: dict[str, str] | None = None) -> tuple[str, list[str]]:
    """Replace PII with stable placeholders like [AADHAAR_1a2b]. `vault` maps placeholder ->
    original so an allowed downstream step can restore it. Returns (text, kinds_found)."""
    found: list[str] = []
    for kind, pat, check in PII_PATTERNS:
        def sub(m: re.Match) -> str:
            s = m.group(0)
            if check and not check(s):
                return s
            tag = f"[{kind}_{hashlib.sha256(s.encode()).hexdigest()[:4]}]"
            if vault is not None:
                vault[tag] = s
            found.append(kind)
            return tag
        text = pat.sub(sub, text)
    return text, found


def restore(text: str, vault: dict[str, str]) -> str:
    for tag, original in vault.items():
        text = text.replace(tag, original)
    return text


# ---------------------------------------------------------------- tenant policy
MODEL_REGIONS = {   # where each model may process data; fill from your contracts
    "claude-opus-5-5": {"us", "eu", "in"},
    "claude-sonnet-5-5": {"us", "eu", "in"},
    "claude-haiku-5-5": {"us", "eu", "in"},
    "mock-small": {"us", "eu", "in"},
    "mock-medium": {"us", "eu", "in"},
    "mock-large": {"us", "eu", "in"},
    "vllm/onprem-70b": {"in"},
}


@dataclass
class TenantPolicy:
    tenant: str
    region: str = "in"
    allowed_models: set[str] = field(default_factory=lambda: {"mock-small", "mock-medium", "mock-large"})
    blocked_tools: set[str] = field(default_factory=set)
    pii_mode: str = "redact"             # redact | block | allow
    max_input_tokens: int = 100_000
    retention_days: int = 30
    log_prompts: bool = False            # store raw prompts in the audit log?


@dataclass
class Decision:
    allow: bool
    reasons: list[str]
    messages: list[Message]
    pii_found: list[str]
    vault: dict[str, str]


class PolicyEngine:
    def check(self, policy: TenantPolicy, model: str, messages: list[Message]) -> Decision:
        reasons: list[str] = []
        if model not in policy.allowed_models:
            reasons.append(f"model {model} not allowed for tenant {policy.tenant}")
        if policy.region not in MODEL_REGIONS.get(model, set()):
            reasons.append(f"model {model} cannot process data in region {policy.region}")
        vault: dict[str, str] = {}
        found: list[str] = []
        out = []
        for m in messages:
            if policy.pii_mode == "allow" or m.role == "assistant":
                out.append(m)
                continue
            text, kinds = redact(m.content, vault)
            found += kinds
            out.append(Message(m.role, text, m.tool_calls, m.tool_call_id, m.is_error))
        if found and policy.pii_mode == "block":
            reasons.append(f"PII present ({', '.join(sorted(set(found)))}) and tenant blocks PII")
        return Decision(not reasons, reasons, out if policy.pii_mode == "redact" else messages, found, vault)

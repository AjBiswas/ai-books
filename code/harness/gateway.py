"""The enterprise AI gateway (Chapters 11 and 18).

Every request from every team passes through one door:
  identify -> policy (models, region, PII) -> route -> budget -> rate limit -> call (+fallback)
  -> meter -> audit -> restore PII for the caller.
`GatewayProvider` makes the gateway look like a normal Provider, so an Agent can run through it.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field

from .budget import Ledger, TokenBucket
from .policy import PolicyEngine, TenantPolicy, restore
from .pricing import cost_usd
from .providers import Provider
from .router import Router
from .telemetry import Tracer
from .tokens import estimate_tokens
from .types import Message, Response


class Blocked(Exception):
    def __init__(self, stage: str, reason: str):
        super().__init__(f"[{stage}] {reason}")
        self.stage, self.reason = stage, reason


@dataclass
class Caller:
    tenant: str
    team: str
    user: str

    @property
    def path(self) -> str:
        return f"{self.tenant}/{self.team}/{self.user}"


@dataclass
class Gateway:
    providers: dict[str, Provider]            # provider name -> adapter
    model_provider: dict[str, str]            # model -> provider name
    policies: dict[str, TenantPolicy]
    router: Router
    ledger: Ledger = field(default_factory=Ledger)
    tracer: Tracer = field(default_factory=Tracer)
    rate: dict[str, TokenBucket] = field(default_factory=dict)   # tenant -> bucket (requests)
    audit: list[dict] = field(default_factory=list)
    engine: PolicyEngine = field(default_factory=PolicyEngine)

    def complete(self, caller: Caller, system: str, messages: list[Message], tools=None,
                 model: str | None = None, max_tokens: int = 1024) -> Response:
        policy = self.policies.get(caller.tenant)
        if policy is None:
            raise Blocked("identity", f"unknown tenant {caller.tenant}")
        with self.tracer.span("gateway.request", **{"harness.tenant": caller.tenant, "harness.team": caller.team}) as root:
            text = " ".join(m.content for m in messages[-3:])
            pre = self.ledger.check(caller.path)
            chosen = model or self.router.choose(text, policy.allowed_models, budget_tight=pre.level == "warn")
            decision = self.engine.check(policy, chosen, messages)
            if not decision.allow:
                self._audit(caller, chosen, "blocked:policy", decision.reasons, messages, policy)
                raise Blocked("policy", "; ".join(decision.reasons))
            est_in = estimate_tokens(system) + sum(estimate_tokens(m.content) for m in decision.messages)
            if est_in > policy.max_input_tokens:
                raise Blocked("policy", f"input ~{est_in} tokens exceeds tenant cap {policy.max_input_tokens}")
            est = cost_usd(chosen, _usage(est_in, max_tokens))
            b = self.ledger.check(caller.path, est)
            if not b.ok:
                self._audit(caller, chosen, "blocked:budget", [b.scope], messages, policy)
                raise Blocked("budget", f"{b.scope} is over its limit")
            bucket = self.rate.get(caller.tenant)
            if bucket and not bucket.allow(1):
                raise Blocked("rate", f"tenant {caller.tenant} is over its request rate")

            def call(m: str) -> Response:
                prov = self.providers[self.model_provider[m]]
                with self.tracer.span("gen_ai.chat", **{"gen_ai.request.model": m, "gen_ai.system": prov.name}) as s:
                    r = prov.complete(model=m, system=system, messages=decision.messages, tools=tools, max_tokens=max_tokens)
                    s.attrs.update({"gen_ai.usage.input_tokens": r.usage.input_tokens + r.usage.cache_read_tokens,
                                    "gen_ai.usage.output_tokens": r.usage.output_tokens,
                                    "harness.cost_usd": cost_usd(m, r.usage)})
                    return r

            used, resp = self.router.call_with_fallback(chosen, call)
            spend = cost_usd(used, resp.usage)
            self.ledger.record(caller.path, spend, resp.usage.total)
            root.attrs.update({"gen_ai.request.model": used, "harness.cost_usd": spend,
                               "harness.pii": ",".join(sorted(set(decision.pii_found)))})
            self._audit(caller, used, "ok", [b.level], messages, policy, resp, spend)
            if decision.vault:
                resp.text = restore(resp.text, decision.vault)
            return resp

    def _audit(self, caller, model, outcome, notes, messages, policy, resp=None, spend=0.0):
        prompt = json.dumps([m.content for m in messages], ensure_ascii=False)
        self.audit.append({
            "ts": time.time(), "tenant": caller.tenant, "team": caller.team, "user": caller.user,
            "model": model, "outcome": outcome, "notes": notes,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "prompt": prompt if policy.log_prompts else None,
            "usage": resp.usage.__dict__ if resp else None, "cost_usd": round(spend, 6),
            "retention_days": policy.retention_days,
        })


def _usage(inp: int, out: int):
    from .types import Usage
    return Usage(inp, out)


class GatewayProvider(Provider):
    """Lets an Agent use the gateway as if it were a model provider."""
    name = "gateway"

    def __init__(self, gateway: Gateway, caller: Caller, pin_model: bool = False):
        self.gateway, self.caller, self.pin_model = gateway, caller, pin_model

    def complete(self, *, model, system, messages, tools=None, max_tokens=1024, **opts):
        return self.gateway.complete(self.caller, system, messages, tools,
                                     model=model if self.pin_model else None, max_tokens=max_tokens)

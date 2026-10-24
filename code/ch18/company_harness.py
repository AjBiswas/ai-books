"""Chapter 18 capstone: the whole company harness, end to end.

Tenants -> gateway (policy, PII, routing, budget, rate limit, fallback, audit) -> agent loop
(tools, hooks, injection guards, context compaction) -> evals gate -> observability roll-up.

Runs offline. To go live, replace the MockProviders with AnthropicProvider() and
OpenAICompatProvider(base_url="http://your-vllm:8000/v1").
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness import Agent, AgentConfig, MockProvider, ToolRegistry
from harness.budget import TokenBucket
from harness.context import ContextManager
from harness.evals import EvalCase, gate, run_suite
from harness.gateway import Blocked, Caller, Gateway, GatewayProvider
from harness.hooks import HookBus
from harness.policy import TenantPolicy
from harness.providers import tool_call
from harness.router import Router, Tier
from harness.security import EgressGuard, install_guards

# ---------------------------------------------------------------- 1. tools the company exposes
reg = ToolRegistry()
ORDERS = {"ORD-100231": {"status": "delivered", "amount_inr": 1499}, "ORD-100232": {"status": "in transit", "amount_inr": 899}}


@reg.tool("get_order", "Look up an order", {"type": "object", "additionalProperties": False, "required": ["order_id"],
          "properties": {"order_id": {"type": "string", "pattern": "^ORD-\\d{6}$"}}})
def get_order(order_id):
    return ORDERS.get(order_id, {"error": "not found"})


@reg.tool("refund", "Refund a delivered order", {"type": "object", "required": ["order_id"],
          "properties": {"order_id": {"type": "string"}}}, risk="write")
def refund(order_id):
    return {"refunded": ORDERS[order_id]["amount_inr"], "order_id": order_id}


# ---------------------------------------------------------------- 2. the "model" (scripted for offline runs)
def support_model(system, messages, tools):
    last = messages[-1]
    if last.role == "user":
        oid = next((w.strip(".,?") for w in last.content.split() if w.startswith("ORD-")), None)
        return tool_call("get_order", {"order_id": oid}) if oid else "Please share your order ID (ORD-xxxxxx)."
    data = json.loads(last.content)
    if "status" in data and data["status"] == "delivered" and "refund" in messages[0].content.lower():
        return tool_call("refund", {"order_id": next(w.strip(".,?") for w in messages[0].content.split() if w.startswith("ORD-"))})
    if "refunded" in data:
        return f"Done. INR {data['refunded']} will reach you in 5-7 working days."
    return f"Your order is {data.get('status', 'not found')}."


cloud = MockProvider(support_model, fail_times=1)
onprem = MockProvider(support_model)

# ---------------------------------------------------------------- 3. the gateway with tenant policies
gw = Gateway(
    providers={"cloud": cloud, "onprem": onprem},
    model_provider={"mock-small": "cloud", "mock-medium": "cloud", "mock-large": "cloud", "vllm/onprem-70b": "onprem"},
    policies={
        "retail": TenantPolicy("retail", region="in", allowed_models={"mock-small", "mock-medium"}),
        "bank": TenantPolicy("bank", region="in", allowed_models={"vllm/onprem-70b"}, pii_mode="redact", retention_days=3650),
        # CI/eval traffic gets its own tenant so a test run never eats customers' rate limit or budget.
        "ci": TenantPolicy("ci", region="in", allowed_models={"mock-small", "mock-medium"}, retention_days=7),
    },
    router=Router([Tier("mock-small", 0.35), Tier("mock-medium", 1.0), Tier("vllm/onprem-70b", 1.0)],
                  fallbacks={"mock-small": ["mock-medium"]}),
    rate={"retail": TokenBucket(capacity=50, rate=10)},
)
gw.ledger.set_limit("retail", 50.0)
gw.ledger.set_limit("bank", 200.0)


def make_agent(caller: Caller) -> Agent:
    hooks = HookBus()
    install_guards(hooks, reg, EgressGuard({"acme.in"}))
    return Agent(GatewayProvider(gw, caller), reg,
                 AgentConfig(model="mock-medium", system="You are Acme's support agent. Use tools. Be brief.",
                             max_steps=6, token_budget=20_000),
                 hooks=hooks, context=ContextManager(max_tokens=6000))


print("=== live traffic ===")
for caller, text in [
    (Caller("retail", "support", "cust-881"), "Where is ORD-100232?"),
    (Caller("retail", "support", "cust-412"), "Please refund ORD-100231, it arrived broken."),
    (Caller("bank", "loans", "officer-7"), "Customer PAN ABCDE1234F asks about ORD-100231"),
    (Caller("unknown", "x", "y"), "hi"),
]:
    try:
        r = make_agent(caller).run(text)
        print(f"[{caller.tenant:7s}] {text[:46]:46s} -> {r.text}  ({r.stop_reason}, {r.steps} steps)")
    except Blocked as e:
        print(f"[{caller.tenant:7s}] {text[:46]:46s} -> BLOCKED at {e.stage}: {e.reason}")

print("\n=== what the bank's model actually saw ===")
print(onprem.calls[0]["messages"][0].content)

print("\n=== release gate before shipping a new prompt ===")
cases = [EvalCase(f"c{i}", f"Where is {oid}?", st) for i, (oid, st) in enumerate(
    [("ORD-100232", "in transit"), ("ORD-100231", "delivered")] * 15)]
run = lambda c: make_agent(Caller("ci", "evals", "pipeline")).run(c.input).text
base = run_suite("current", run, cases, lambda c, o: float(c.expected in o))
cand = run_suite("candidate", lambda c: run(c).replace("in transit", "on its way"), cases, lambda c, o: float(c.expected in o))
print(base.summary())
print(cand.summary())
print("gate:", gate(base, cand)[1])

print("\n=== observability & chargeback ===")
for m, r in sorted(gw.tracer.rollup().items()):
    print(f"  {m:16s} calls={r['calls']:3d} in={r['input_tokens']:6d} out={r['output_tokens']:5d} cost=${r['cost_usd']:.4f}")
for scope, usd, tok in gw.ledger.chargeback(1):
    print(f"  tenant {scope:8s} ${usd:.4f}  {tok:,} tokens")
print(f"  audit records: {len(gw.audit)} (raw prompts stored: {sum(a['prompt'] is not None for a in gw.audit)})")

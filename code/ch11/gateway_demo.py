"""Chapter 11 lab: one gateway, three tenants, routing and fallback."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness import Message, MockProvider
from harness.gateway import Blocked, Caller, Gateway
from harness.policy import TenantPolicy
from harness.router import Router, Tier

echo = lambda s, m, t: "answer"
gw = Gateway(
    providers={"cloud": MockProvider(echo, fail_times=1), "onprem": MockProvider(echo)},
    model_provider={"mock-small": "cloud", "mock-medium": "cloud", "mock-large": "cloud", "vllm/onprem-70b": "onprem"},
    policies={
        "retail": TenantPolicy("retail", region="eu", allowed_models={"mock-small", "mock-medium", "mock-large"}),
        "bank": TenantPolicy("bank", region="in", allowed_models={"vllm/onprem-70b"}, pii_mode="block"),
        "hr": TenantPolicy("hr", region="in", allowed_models={"mock-small", "mock-medium"}),
    },
    router=Router([Tier("mock-small", 0.35), Tier("mock-medium", 0.65), Tier("mock-large", 1.0), Tier("vllm/onprem-70b", 1.0)],
                  fallbacks={"mock-small": ["mock-medium"], "mock-medium": ["mock-small"], "mock-large": ["mock-medium"]}),
)
requests = [
    (Caller("hr", "people", "asha"), "Classify this leave request: sick leave, 2 days"),
    (Caller("hr", "people", "asha"), "Analyze why attrition rose and design a multi-step plan to fix it"),
    (Caller("retail", "web", "li"), "Design and debug the architecture; analyze why checkout fails under load"),
    (Caller("bank", "loans", "ravi"), "Summarise this loan file"),
    (Caller("bank", "loans", "ravi"), "Customer PAN ABCDE1234F wants a top-up"),
]
for caller, text in requests:
    try:
        r = gw.complete(caller, "You are helpful.", [Message("user", text)])
        print(f"{caller.tenant:7s} OK      model={r.model:16s} {text[:48]}")
    except Blocked as e:
        print(f"{caller.tenant:7s} BLOCKED {e.stage:6s} {e.reason[:70]}")
print("\nNote: the first cloud call failed and fell back to the next model in its chain.")

"""Chapter 8 lab: retrieval, prompt layout, and compaction."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness import Message
from harness.context import BM25, ContextManager, build_system, messages_tokens, serialize, shared_prefix_tokens
from harness.types import ToolCall

policies = [
    "Leave policy: employees get 24 days of paid leave per calendar year; up to 8 carry forward.",
    "Travel policy: economy class for flights under 6 hours; business class above 6 hours with VP approval.",
    "Laptop policy: laptops are refreshed every 3 years; lost devices must be reported within 24 hours.",
    "Work from home: up to 2 days per week with manager approval.",
]
bm = BM25(policies)
q = "Can I fly business class to London?"
print("Query:", q)
for score, i in bm.search(q, k=2):
    print(f"  {score:5.2f}  {policies[i][:70]}...")

rules = "You are Acme's HR assistant. Answer only from the documents. Say 'I don't know' if unsure."
good = [serialize(build_system(rules, policies), None, [Message("user", f"Today is 2026-10-{d}. {q}")]) for d in (24, 25)]
bad = [serialize(f"Today is 2026-10-{d}. " + build_system(rules, policies), None, [Message("user", q)]) for d in (24, 25)]
print("\nCache reuse on the second request:")
print(f"  date at the END   -> {shared_prefix_tokens(*good):4d} tokens reusable")
print(f"  date at the START -> {shared_prefix_tokens(*bad):4d} tokens reusable")

msgs = [Message("user", "Audit all 30 expense reports")]
for i in range(30):
    msgs += [Message("assistant", "", [ToolCall(f"c{i}", "read_report", {"id": i})]),
             Message("tool", f"report {i}: total INR {1000 + 37 * i}; flagged={i % 7 == 0}; " + "details " * 40, tool_call_id=f"c{i}"),
             Message("user", f"next ({i})")]
cm = ContextManager(max_tokens=1500, keep_recent=6)
out = cm.prepare(msgs)
print(f"\nCompaction: {len(msgs)} messages / ~{messages_tokens(msgs):,} tokens -> {len(out)} messages / ~{messages_tokens(out):,} tokens")

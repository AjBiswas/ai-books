"""Chapter 7 lab: what the harness says back when a tool call is wrong."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness import ToolRegistry
from harness.types import ToolCall

reg = ToolRegistry()


@reg.tool("refund", "Refund an order", {"type": "object", "additionalProperties": False, "required": ["order_id", "amount_inr"],
          "properties": {"order_id": {"type": "string", "pattern": "^ORD-\\d{6}$"},
                         "amount_inr": {"type": "integer", "minimum": 1, "maximum": 50000}}}, risk="write")
def refund(order_id, amount_inr):
    return {"ok": True, "order_id": order_id, "refunded": amount_inr}


@reg.tool("slow_report", "A report that hangs", {"type": "object"}, timeout_s=0.2)
def slow_report():
    time.sleep(1)


@reg.tool("delete_account", "Delete a customer account", {"type": "object", "properties": {"id": {"type": "string"}}},
          risk="dangerous")
def delete_account(id):
    return "deleted"


cases = [
    ("good call", ToolCall("1", "refund", {"order_id": "ORD-123456", "amount_inr": 499})),
    ("made-up tool", ToolCall("2", "issue_refund", {"order_id": "ORD-123456"})),
    ("bad arguments", ToolCall("3", "refund", {"order_id": "123", "amount_inr": 90000, "note": "vip"})),
    ("hangs", ToolCall("4", "slow_report", {})),
    ("dangerous", ToolCall("5", "delete_account", {"id": "C-9"})),
]
for label, call in cases:
    out, err = reg.execute(call, mode="default", approver=lambda c: False)
    print(f"{label:14s} {'ERROR' if err else 'ok   '} {out}")

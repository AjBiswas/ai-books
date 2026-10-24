"""Book 1, Chapter 41 lab: a durable, policy-checked agent workflow that survives a crash.

- Harness-as-code: the workflow, limits and policies are plain data you can version and test.
- State management: every finished step is written to a checkpoint file (here JSON; in production
  a database or a durable-execution engine such as Temporal).
- Control plane: a policy check runs before every step; risky steps need human approval.
- Durable execution: run 1 crashes in the middle; run 2 resumes from the checkpoint and does not
  repeat (or double-charge) the steps that already finished.
Run:  python durable_workflow.py      (standard library only)
"""
import json
import os
import pathlib
import tempfile

# ---- harness-as-code: this dict would live in a reviewed, versioned file ----
HARNESS = {
    "workflow": "refund_order",
    "steps": ["fetch_order", "check_policy", "issue_refund", "email_customer", "close_ticket"],
    "limits": {"max_refund_inr": 5000, "max_steps": 10},
    "needs_approval": ["issue_refund"],          # human approval gate for money movement
    "idempotent": ["fetch_order", "check_policy", "email_customer", "close_ticket"],
}

STATE = pathlib.Path(tempfile.gettempdir()) / "ch41_refund_ORD-77.json"
LEDGER = []                                       # pretend payment system: we must never pay twice


def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {"done": [], "data": {}, "log": []}


def save(s):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(s, indent=1))
    os.replace(tmp, STATE)                        # atomic: a crash never leaves half a file


# ---- the steps (in real life: tool calls and model calls) ----
def fetch_order(s):
    s["data"]["order"] = {"id": "ORD-77", "amount_inr": 1899, "customer": "asha@example.com"}


def check_policy(s):
    s["data"]["eligible"] = s["data"]["order"]["amount_inr"] <= HARNESS["limits"]["max_refund_inr"]


def issue_refund(s):
    LEDGER.append(("refund", s["data"]["order"]["id"], s["data"]["order"]["amount_inr"]))
    s["data"]["refund_id"] = "RF-5512"


def email_customer(s, crash=False):
    if crash:
        raise ConnectionError("mail server timed out")   # the crash, mid-workflow
    s["data"]["emailed"] = True


def close_ticket(s):
    s["data"]["closed"] = True


def control_plane(step, s, approved):
    if step == "issue_refund" and not s["data"].get("eligible"):
        return "deny: amount above refund limit"
    if step in HARNESS["needs_approval"] and step not in approved:
        return "wait: human approval required"
    return "allow"


def run(label, crash_on=None, approved=()):
    s = load()
    print(f"--- {label} (checkpoint has {len(s['done'])} finished steps)")
    for step in HARNESS["steps"]:
        if step in s["done"]:
            print(f"   skip   {step:15} already done")
            continue
        decision = control_plane(step, s, approved)
        if decision != "allow":
            print(f"   {decision.split(':')[0]:6} {step:15} {decision.split(': ')[1]}")
            return
        try:
            fn = globals()[step]
            fn(s, crash=True) if step == crash_on else fn(s)
        except Exception as e:
            print(f"   CRASH  {step:15} {e}")
            return
        s["done"].append(step)
        s["log"].append(step)
        save(s)                                   # checkpoint after every step
        print(f"   done   {step}")
    print(f"   finished: {s['data']}")


if STATE.exists():
    STATE.unlink()
run("run 1: waits for approval")
run("run 2: approved, but the mail server crashes", crash_on="email_customer", approved={"issue_refund"})
run("run 3: resume after the crash", approved={"issue_refund"})
print(f"\npayments made: {LEDGER}   <- exactly one refund, even though the workflow ran three times")

"""Book 1, Chapter 45 lab: automatic prompt optimisation, DSPy-style, from scratch.

Task: route support messages to billing / delivery / account / other.
Instead of hand-tweaking, a program tries several instructions and several few-shot example sets,
scores each on a DEV set, keeps the best, and reports it on a held-out TEST set it never saw.
That is the core loop libraries such as DSPy automate (with smarter search).
Setup:  ollama pull qwen3:4b
Run:    python optimise_prompt.py      (about 60 short model calls)
"""
import itertools
import json
import urllib.request

LABELS = ["billing", "delivery", "account", "other"]
TRAIN = [("I was charged twice for one order", "billing"), ("Where is my parcel? It said 2 days", "delivery"),
         ("I can't log in, reset link never arrives", "account"), ("Do you have a store in Goa?", "other")]
DEV = [("Refund hasn't reached my card yet", "billing"), ("Courier marked delivered but nothing came", "delivery"),
       ("Please change the email on my profile", "account"), ("Are you hiring interns?", "other"),
       ("Why is there a GST line on my invoice?", "billing"), ("The box arrived crushed", "delivery"),
       ("Delete my account and data", "account"), ("What are your shop timings on Sunday?", "other")]
TEST = [("Coupon didn't apply and I paid full price", "billing"), ("Tracking hasn't moved for a week", "delivery"),
        ("Two-factor code not coming on my new phone", "account"), ("Can I sell my products on your site?", "other"),
        ("EMI was deducted but order shows unpaid", "billing"), ("Delivery guy asked for extra money", "delivery"),
        ("My account got locked after a password change", "account"), ("Do you ship to Nepal?", "delivery")]

INSTRUCTIONS = [
    "Classify the message.",
    "Classify the customer message into exactly one category: billing, delivery, account, other. Answer with the category only.",
    ("You route customer support messages. Categories: billing = payments, refunds, invoices, charges; "
     "delivery = shipping, couriers, tracking, damaged parcels; account = login, profile, passwords, data; "
     "other = anything else. Answer with one lowercase word."),
]
SHOTS = {"no examples": [], "4 examples": TRAIN}


def predict(instruction, shots, text):
    msgs = [{"role": "system", "content": instruction}]
    for x, y in shots:
        msgs += [{"role": "user", "content": x}, {"role": "assistant", "content": y}]
    msgs.append({"role": "user", "content": text})
    body = {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0, "num_predict": 4096}, "messages": msgs}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        out = json.loads(r.read())["message"]["content"].strip().lower()
    return next((l for l in LABELS if l in out), out[:12])


def score(instruction, shots, data):
    return sum(predict(instruction, shots, x) == y for x, y in data) / len(data)


results = []
for (i, ins), (sname, shots) in itertools.product(enumerate(INSTRUCTIONS, 1), SHOTS.items()):
    s = score(ins, shots, DEV)
    results.append((s, i, sname))
    print(f"instruction {i} + {sname:11}  dev accuracy {s:.0%}")

best_s, best_i, best_shots = max(results)
worst_s, worst_i, worst_shots = min(results)
print(f"\nbest on dev:  instruction {best_i} + {best_shots} ({best_s:.0%})")
print(f"test (unseen): best {score(INSTRUCTIONS[best_i - 1], SHOTS[best_shots], TEST):.0%}"
      f"   vs worst {score(INSTRUCTIONS[worst_i - 1], SHOTS[worst_shots], TEST):.0%}")

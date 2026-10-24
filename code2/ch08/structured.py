"""Book 2, Chapter 8 lab: "please reply in JSON" vs. schema-constrained decoding.

Ollama's `format` field accepts a JSON Schema and constrains generation to it.
Run:  python structured.py
"""
import json
import urllib.request

SCHEMA = {"type": "object", "additionalProperties": False,
          "required": ["name", "city", "issue", "urgency"],
          "properties": {"name": {"type": "string"}, "city": {"type": "string"},
                         "issue": {"type": "string", "enum": ["refund", "delivery", "login", "other"]},
                         "urgency": {"type": "integer", "minimum": 1, "maximum": 5}}}

TICKETS = [
    "Hi, Ananya here from Pune. My parcel is 6 days late!!! Need it before Diwali.",
    "this is rahul (Indore). cant login since morning, OTP never comes. pls help asap",
    "Namaste, Suresh from Chennai. The mixer arrived broken, I want my money back.",
    "Kavya, Kochi. Just asking about your store timings, no rush.",
    "Sir mera naam Imran hai, Lucknow se. Order cancel kiya tha, paisa abhi tak nahi aaya.",
]


def ask(ticket, constrained):
    prompt = ("Extract name, city, issue (refund|delivery|login|other) and urgency (1-5) from this "
              f"customer message. Reply with only JSON.\n\n{ticket}")
    body = {"model": "qwen3:4b", "stream": False, "think": False, "options": {"temperature": 0},
            "messages": [{"role": "user", "content": prompt}]}
    if constrained:
        body["format"] = SCHEMA
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["message"]["content"]


def valid(text):
    try:
        d = json.loads(text.split("</think>")[-1].strip())
    except json.JSONDecodeError:
        return False, None
    ok = (set(d) == set(SCHEMA["required"]) and d["issue"] in SCHEMA["properties"]["issue"]["enum"]
          and isinstance(d["urgency"], int) and 1 <= d["urgency"] <= 5)
    return ok, d


for constrained in (False, True):
    good = 0
    print("== with JSON-schema constraint ==" if constrained else "== prompt only: 'reply with only JSON' ==")
    for t in TICKETS:
        ok, d = valid(ask(t, constrained))
        good += ok
        print(f"  {'valid  ' if ok else 'INVALID'} {json.dumps(d, ensure_ascii=False) if d else '(not parseable JSON)'}")
    print(f"  -> {good}/{len(TICKETS)} valid\n")

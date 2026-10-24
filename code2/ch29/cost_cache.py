"""Book 1, Chapter 29 lab: three ways to spend less: prefix caching, a response cache, and routing.

1) Prefix (KV) cache: the same long system prompt sent twice. The engine keeps the processed
   prefix, so the second call reads far fewer new tokens and starts faster.
2) Response cache: an identical question is answered from memory, with no model call at all.
3) Routing: easy questions to a cheap path, hard ones to the expensive model (here: a rule).
Setup:  ollama pull qwen3:4b
Run:    python cost_cache.py
"""
import hashlib
import json
import time
import urllib.request

POLICY = "Acme support policy.\n" + "\n".join(f"Rule {i}: customers in zone {i} get delivery in {i % 5 + 1} days." for i in range(1, 120))


def call(system, user):
    body = {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0, "num_predict": 4096},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    t0 = time.perf_counter()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.loads(r.read())
    return d, time.perf_counter() - t0


print("1) prefix cache (same long system prompt, different questions)")
for q in ("Delivery time for zone 7?", "Delivery time for zone 12?"):
    d, secs = call(POLICY, q + " Answer with the number of days only.")
    print(f"   {q:28} prompt tokens {d['prompt_eval_count']:5}  prompt processing {d['prompt_eval_duration'] / 1e9:5.2f}s  "
          f"answer {d['message']['content'].strip()!r}")

print("\n2) response cache")
CACHE = {}


def cached(q):
    key = hashlib.sha256(q.strip().lower().encode()).hexdigest()
    if key in CACHE:
        return CACHE[key], 0.0, "HIT"
    d, secs = call("Answer in one short sentence.", q)
    CACHE[key] = d["message"]["content"].strip()
    return CACHE[key], secs, "miss"


for q in ("What are your store hours?", "what are your store hours?  "):
    a, secs, status = cached(q)
    print(f"   {status:4} {secs:5.1f}s  {q!r} -> {a[:60]}")

print("\n3) routing rule")
for q in ("hi", "Order ORD-9 arrived damaged and the replacement is also broken, what are my options under the consumer law?"):
    route = "small/cheap model" if len(q.split()) < 8 and "?" not in q else "large model"
    print(f"   {route:18} <- {q[:70]}")

"""Book 1, Chapter 10 lab: pack the context window on purpose.

Candidate pieces (policy text, chat history, tool results, a long irrelevant document) compete for a
fixed token budget. The packer ranks by relevance to the question, keeps required pieces, fits the
budget, and puts the most important material at the start and end. Then we ask the model with the
packed context and with "everything" (which overflows Ollama's 4,096-token window here).
Setup:  ollama pull qwen3:4b ; ollama pull all-minilm
Run:    python context_packing.py
"""
import json
import math
import urllib.request

API = "http://localhost:11434/api"


def post(path, body):
    req = urllib.request.Request(f"{API}/{path}", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())


def toks(text):                       # rough rule of thumb: ~4 characters per token in English
    return len(text) // 4 + 1


def embed(texts):
    return post("embed", {"model": "all-minilm", "input": texts})["embeddings"]


def cos(a, b):
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


Q = "Can I get a refund for order ORD-4411? I opened the box but never used it."
PIECES = [
    ("instructions", True, "You are Acme's support assistant. Answer only from the context. Quote the policy line you used."),
    ("refund policy", False, "Refund policy: unused items can be returned within 10 days of delivery for a full refund. Opened packaging is fine if the item is unused."),
    ("order lookup", False, "Tool result get_order(ORD-4411): delivered 2026-10-17, item: Bluetooth speaker, status: delivered."),
    ("today", True, "Today's date is 2026-10-24."),
    ("shipping policy", False, "Shipping policy: free shipping above INR 499; express delivery costs INR 99."),
    ("old chat", False, "Earlier today the customer asked about store timings; we said 10:00-21:00."),
    ("annual report", False, "Acme annual report: " + "Revenue grew across regions with strong festive demand. " * 400),
]
BUDGET = 300

qv = embed([Q])[0]
vecs = embed([p[2][:2000] for p in PIECES])
scored = sorted(((1.0 if req else cos(qv, v), name, req, text) for (name, req, text), v in zip(PIECES, vecs)), reverse=True)
packed, used = [], 0
print(f"budget {BUDGET} tokens")
for score, name, req, text in scored:
    t = toks(text)
    keep = req or (score > 0.2 and used + t <= BUDGET)
    used += t if keep else 0
    print(f"   {'KEEP' if keep else 'drop'}  {name:15} relevance {score:.2f}  {t:5d} tokens")
    if keep:
        packed.append((name, text))
order = [p for p in packed if p[0] == "instructions"] + [p for p in packed if p[0] not in ("instructions",)]
context = "\n".join(f"[{n}] {t}" for n, t in order)
print(f"packed: {used} tokens of {sum(toks(p[2]) for p in PIECES)} available")


def ask(ctx):
    out = post("chat", {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0, "num_predict": 4096},
                        "messages": [{"role": "user", "content": f"{ctx}\n\nCustomer: {Q}"}]})
    return out["message"]["content"].strip(), out["prompt_eval_count"]


ans, n = ask(context)
print(f"\nPACKED context ({n} tokens read): {ans}")
everything = "\n".join(f"[{n_}] {t}" for n_, _, t in PIECES[::-1])
ans, n = ask(everything)
print(f"\nEVERYTHING ({n} tokens read; the window is 4,096, so the start was cut off): {ans}")

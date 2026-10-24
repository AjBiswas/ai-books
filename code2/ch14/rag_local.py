"""Book 2, Chapter 14 lab: a complete RAG pipeline on your laptop.

chunk -> embed (all-minilm) -> hybrid search (vector + keyword) -> answer with citations (qwen3:4b)
Setup:  ollama pull all-minilm ; ollama pull qwen3:4b
Run:    python rag_local.py
"""
import json
import math
import re
import time
import urllib.request

API = "http://localhost:11434/api"


def post(path, body):
    req = urllib.request.Request(f"{API}/{path}", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def embed(texts):
    return post("embed", {"model": "all-minilm", "input": texts})["embeddings"]


def cos(a, b):
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


DOC = """# Acme HR Handbook
## Leave
Employees get 24 days of paid leave per calendar year. Up to 8 unused days carry forward to the next year.
## Travel
Book economy class for flights under 6 hours. Business class is allowed above 6 hours with VP approval.
## Laptops
Laptops are refreshed every 3 years. Report a lost laptop to IT within 24 hours.
## Work from home
Up to 2 days per week with manager approval. Core hours are 11:00 to 16:00 IST.
## Expenses
Submit expense claims within 30 days with receipts. Meals are reimbursed up to INR 1,500 per day while travelling."""

# 1) chunk by heading, keep the heading as a citation
chunks = []
for sec in re.split(r"\n## ", DOC)[1:]:
    title, body = sec.split("\n", 1)
    chunks.append({"id": title.strip(), "text": f"{title.strip()}: {body.strip()}"})

# 2) embed once (in a real system: store these in a vector database)
vectors = embed([c["text"] for c in chunks])


def keyword_score(q, text):
    qw = set(re.findall(r"\w+", q.lower()))
    tw = re.findall(r"\w+", text.lower())
    return sum(1 for w in tw if w in qw and len(w) > 3) / (1 + len(tw) ** 0.5)


def retrieve(q, k=2):
    qv = embed([q])[0]
    vec = [cos(qv, v) for v in vectors]
    kw = [keyword_score(q, c["text"]) for c in chunks]
    # 3) hybrid: reciprocal rank fusion of the two rankings
    rank = lambda xs: {i: r for r, i in enumerate(sorted(range(len(xs)), key=lambda i: -xs[i]))}
    rv, rk = rank(vec), rank(kw)
    fused = sorted(range(len(chunks)), key=lambda i: -(1 / (60 + rv[i]) + 1 / (60 + rk[i])))
    return [(chunks[i], vec[i]) for i in fused[:k]]


def answer(q):
    hits = retrieve(q)
    ctx = "\n".join(f'<doc id="{c["id"]}">{c["text"]}</doc>' for c, _ in hits)
    prompt = (f"Answer using ONLY the documents. Cite the doc id in square brackets. "
              f"If the documents don't contain the answer, say \"I don't know\".\n\n{ctx}\n\nQuestion: {q}")
    t0 = time.perf_counter()
    out = post("chat", {"model": "qwen3:4b", "stream": False, "think": False, "options": {"temperature": 0},
                        "messages": [{"role": "user", "content": prompt}]})
    text = out["message"]["content"].split("</think>")[-1].strip()
    return hits, text, time.perf_counter() - t0


for q in ["Can I fly business class to London?", "How much can I spend on food when travelling?", "What is the dress code?"]:
    hits, text, dt = answer(q)
    print(f"Q: {q}")
    print("   retrieved:", ", ".join(f'{c["id"]} ({s:.2f})' for c, s in hits))
    print(f"   A ({dt:.0f}s): {text}")

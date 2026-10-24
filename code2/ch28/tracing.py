"""Book 1, Chapter 28 lab: trace one request through a small AI pipeline.

Every step (retrieve, model call, check) becomes a span with a parent, timing, tokens and cost.
Spans are written as JSON lines (the shape OpenTelemetry-style tools collect) and printed as a tree.
Setup:  ollama pull qwen3:4b ; ollama pull all-minilm
Run:    python tracing.py
"""
import contextlib
import json
import pathlib
import tempfile
import time
import urllib.request
import uuid

SPANS = []
STACK = []


@contextlib.contextmanager
def span(name, **attrs):
    s = {"id": uuid.uuid4().hex[:6], "parent": STACK[-1]["id"] if STACK else None, "name": name, "attrs": attrs, "start": time.perf_counter()}
    STACK.append(s)
    try:
        yield s
    finally:
        STACK.pop()
        s["ms"] = round((time.perf_counter() - s.pop("start")) * 1000)
        SPANS.append(s)


def post(path, body):
    req = urllib.request.Request(f"http://localhost:11434/api/{path}", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())


DOCS = ["Returns: 10 days for unused items.", "Shipping: free above INR 499.", "Warranty: 1 year on electronics."]
q = "Is shipping free for a 600 rupee order?"
with span("handle_request", user="u-17", question=q):
    with span("retrieve", k=1) as s:
        vecs = post("embed", {"model": "all-minilm", "input": DOCS + [q]})["embeddings"]
        dot = [sum(a * b for a, b in zip(v, vecs[-1])) for v in vecs[:-1]]
        best = DOCS[dot.index(max(dot))]
        s["attrs"]["picked"] = best
    with span("llm_call", model="qwen3:4b") as s:
        out = post("chat", {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0, "num_predict": 4096},
                            "messages": [{"role": "user", "content": f"Context: {best}\nQuestion: {q}\nAnswer in one sentence."}]})
        s["attrs"].update(prompt_tokens=out["prompt_eval_count"], output_tokens=out["eval_count"],
                          cost_usd=round((out["prompt_eval_count"] * 0.15 + out["eval_count"] * 0.6) / 1e6, 6))
        answer = out["message"]["content"].strip()
    with span("output_check") as s:
        s["attrs"]["passed"] = "499" in answer or "free" in answer.lower()

print("answer:", answer, "\n")
TRACE = pathlib.Path(tempfile.gettempdir()) / "trace.jsonl"
with open(TRACE, "w") as f:
    for s in SPANS:
        f.write(json.dumps(s) + "\n")
by_parent = {}
for s in SPANS:
    by_parent.setdefault(s["parent"], []).append(s)


def show(parent, depth):
    for s in sorted(by_parent.get(parent, []), key=lambda x: x["name"] != "retrieve"):
        print(f"{'   ' * depth}{s['name']:16} {s['ms']:6} ms  {json.dumps(s['attrs'])[:90]}")
        show(s["id"], depth + 1)


show(None, 0)
print("\n(spans also written to trace.jsonl)")

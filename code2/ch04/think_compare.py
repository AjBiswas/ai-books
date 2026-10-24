"""Book 2, Chapter 4 lab: what "thinking" costs on a laptop model.

Same question, three ways. Run:  python think_compare.py
"""
import json
import time
import urllib.request

URL = "http://localhost:11434/api/chat"
Q = "In one sentence: what is a context window?"


def run(label, content, think):
    body = {"model": "qwen3:4b", "stream": False, "options": {"temperature": 0.2},
            "messages": [{"role": "user", "content": content}]}
    if think is not None:
        body["think"] = think
    t0 = time.perf_counter()
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        out = json.loads(r.read())
    dt = time.perf_counter() - t0
    msg = out["message"]
    answer = msg.get("content", "").split("</think>")[-1].strip()
    print(f"{label:34s} {dt:5.1f}s  {out.get('eval_count', 0):4d} output tokens  "
          f"thinking field: {len(msg.get('thinking') or '')} chars")
    print(f"{'':34s} answer: {answer[:110]}")


run("think=True (reasoning separated)", Q, True)
run("think=False", Q, False)
run("'/no_think' in the prompt", Q + " /no_think", None)

"""Book 1, Chapter 30 lab: streaming, and why it makes an app feel faster.

The same request twice: once waiting for the whole answer, once streaming tokens as they arrive.
We measure time-to-first-visible-token versus total time. With a thinking model, the stream also
shows when the hidden reasoning ends and the visible answer begins: show a "thinking..." state.
Setup:  ollama pull qwen3:4b
Run:    python streaming.py
"""
import json
import time
import urllib.request

BODY = {"model": "qwen3:4b", "think": True, "options": {"temperature": 0, "num_predict": 4096},
        "messages": [{"role": "user", "content": "Give 3 short tips for a safe UPI payment, one line each."}]}


def request(stream):
    body = dict(BODY, stream=stream)
    return urllib.request.urlopen(urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(),
                                                         headers={"Content-Type": "application/json"}), timeout=900)


t0 = time.perf_counter()
with request(False) as r:
    json.loads(r.read())
print(f"without streaming: the user stares at a spinner for {time.perf_counter() - t0:.1f}s, then sees everything")

t0 = time.perf_counter()
first_think = first_answer = None
answer = ""
with request(True) as r:
    for line in r:
        chunk = json.loads(line)
        msg = chunk.get("message", {})
        if msg.get("thinking") and first_think is None:
            first_think = time.perf_counter() - t0
        if msg.get("content"):
            if first_answer is None:
                first_answer = time.perf_counter() - t0
            answer += msg["content"]
total = time.perf_counter() - t0
print(f"with streaming:    'thinking...' can show at {first_think:.1f}s, the first answer word at {first_answer:.1f}s, done at {total:.1f}s")
print("\n" + answer.strip())

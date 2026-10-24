"""Book 1, Chapter 31 lab: a resilient model client: fallbacks and a circuit breaker.

The primary "provider" is a model that isn't installed (it fails every time). The client tries it,
falls back to the local qwen3:4b, and after 3 failures the circuit breaker opens: the broken
primary is skipped entirely for a cool-down period instead of wasting time on every request.
Setup:  ollama pull qwen3:4b
Run:    python resilient.py
"""
import json
import time
import urllib.error
import urllib.request

CHAIN = ["primary-model-that-is-down:latest", "qwen3:4b"]


class Breaker:
    def __init__(self, threshold=3, cooldown_s=60):
        self.fails, self.opened_at, self.threshold, self.cooldown = 0, None, threshold, cooldown_s

    def allow(self):
        return self.opened_at is None or time.time() - self.opened_at > self.cooldown

    def record(self, ok):
        self.fails = 0 if ok else self.fails + 1
        if self.fails >= self.threshold and self.opened_at is None:
            self.opened_at = time.time()
            print("      circuit OPEN for primary: skipping it for 60s")


BREAKERS = {m: Breaker() for m in CHAIN}


def ask(q):
    for model in CHAIN:
        if not BREAKERS[model].allow():
            continue
        try:
            body = {"model": model, "stream": False, "think": True, "options": {"temperature": 0, "num_predict": 4096},
                    "messages": [{"role": "user", "content": q + " One short sentence."}]}
            t0 = time.perf_counter()
            req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=900) as r:
                ans = json.loads(r.read())["message"]["content"].strip()
            BREAKERS[model].record(True)
            return model, ans, time.perf_counter() - t0
        except urllib.error.HTTPError as e:
            print(f"      {model} failed: HTTP {e.code}")
            BREAKERS[model].record(False)
    return None, "Sorry, the assistant is unavailable. Please try again shortly.", 0


for i, q in enumerate(["What is GST?", "What is TDS?", "What is an IFSC code?", "What is a PAN card?"], 1):
    print(f"request {i}: {q}")
    model, ans, secs = ask(q)
    print(f"   served by {model} in {secs:.0f}s: {ans[:80]}")

"""Book 1, Chapter 4 lab: talk to a model running on your own laptop through Ollama.

Setup (once):  install Ollama from ollama.com, then:  ollama pull qwen3:4b
Run:           python local_model.py
Uses only the Python standard library.
"""
import json
import time
import urllib.request

OLLAMA = "http://localhost:11434"
MODEL = "qwen3:4b"


def chat(messages, model=MODEL, think=False, stream=False):
    body = json.dumps({"model": model, "messages": messages, "stream": stream, "think": think,
                       "options": {"temperature": 0.2}}).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        if not stream:
            return json.loads(r.read())
        for line in r:                       # one JSON object per line while streaming
            yield json.loads(line)


if __name__ == "__main__":
    q = [{"role": "user", "content": "In one sentence: what is a context window?"}]

    t0 = time.perf_counter()
    first, text = None, ""
    for chunk in chat(q, stream=True):
        piece = chunk.get("message", {}).get("content", "")
        if piece and first is None:
            first = time.perf_counter() - t0
        text += piece
        if chunk.get("done"):
            stats = chunk
    total = time.perf_counter() - t0
    out_tok = stats.get("eval_count", 0)
    gen_s = stats.get("eval_duration", 1) / 1e9
    print("answer:", text.strip())
    print(f"time to first token: {first:.2f}s | total: {total:.2f}s | "
          f"output tokens: {out_tok} | speed: {out_tok / gen_s:.1f} tokens/s")
    print(f"prompt tokens: {stats.get('prompt_eval_count')} | cost: $0.00 (your laptop)")

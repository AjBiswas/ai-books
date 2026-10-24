"""Book 1, Chapter 44 lab (part 2): put a model behind your own OpenAI-style API.

A small service in front of the inference engine (here Ollama; in production vLLM or similar):
API-key check, a /healthz probe for Kubernetes, an OpenAI-compatible /v1/chat/completions route,
and usage numbers (tokens, tokens per second) in every response. The script starts the server,
calls it as a client would, and prints what happened.
Setup:  ollama pull qwen3:4b
Run:    python serve_proxy.py      (standard library only)
"""
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ENGINE = os.environ.get("ENGINE_URL", "http://localhost:11434/api/chat")
KEYS = {"sk-team-alpha": "team-alpha"}
PORT = 8790


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/healthz":                     # liveness/readiness probe
            return self.send(200, {"status": "ok"})
        self.send(404, {"error": "not found"})

    def do_POST(self):
        key = self.headers.get("Authorization", "").removeprefix("Bearer ")
        if key not in KEYS:
            return self.send(401, {"error": "invalid API key"})
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        body = {"model": req.get("model", "qwen3:4b"), "stream": False, "think": True, "messages": req["messages"],
                "options": {"temperature": req.get("temperature", 0), "num_predict": 4096}}   # thinking model: budget covers reasoning + answer
        t0 = time.perf_counter()
        r = urllib.request.urlopen(urllib.request.Request(ENGINE, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}), timeout=900)
        out = json.loads(r.read())
        gen_s = out["eval_duration"] / 1e9
        self.send(200, {
            "object": "chat.completion", "model": body["model"],
            "choices": [{"index": 0, "message": {"role": "assistant", "content": out["message"]["content"].strip()}, "finish_reason": out.get("done_reason")}],
            "usage": {"prompt_tokens": out["prompt_eval_count"], "completion_tokens": out["eval_count"],
                      "total_tokens": out["prompt_eval_count"] + out["eval_count"]},
            "x_metrics": {"team": KEYS[key], "latency_s": round(time.perf_counter() - t0, 2), "tokens_per_s": round(out["eval_count"] / gen_s, 1)},
        })


if "--serve" in sys.argv:                              # container mode: just serve
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()

server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{PORT}"


def call(path, payload=None, key=None):
    data = json.dumps(payload).encode() if payload else None
    headers = {"Content-Type": "application/json", **({"Authorization": f"Bearer {key}"} if key else {})}
    try:
        with urllib.request.urlopen(urllib.request.Request(base + path, data=data, headers=headers), timeout=900) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


print("GET  /healthz                ->", call("/healthz"))
msg = {"model": "qwen3:4b", "messages": [{"role": "user", "content": "In one sentence: what does a load balancer do?"}]}
print("POST /v1/chat/completions (no key)  ->", call("/v1/chat/completions", msg))
status, resp = call("/v1/chat/completions", msg, key="sk-team-alpha")
print(f"POST /v1/chat/completions (key)     -> {status}")
print("   answer: ", resp["choices"][0]["message"]["content"])
print("   usage:  ", resp["usage"])
print("   metrics:", resp["x_metrics"])
server.shutdown()

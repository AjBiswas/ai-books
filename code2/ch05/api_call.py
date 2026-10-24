"""Book 1, Chapter 5 lab: a production-shaped API call: timeout, retries with backoff, usage and cost.

Uses the OpenAI-compatible endpoint that Ollama exposes (/v1/chat/completions), so the same code
works against a paid provider by changing BASE_URL, the model name and the key.
The first call goes to a wrong port on purpose, to show the retry logic.
Setup:  ollama pull qwen3:4b
Run:    python api_call.py
"""
import json
import random
import time
import urllib.error
import urllib.request

BASE_URL = "http://localhost:11434/v1"
PRICE_PER_M = {"input": 0.15, "output": 0.60}     # pretend prices in USD per million tokens


def call(base_url, messages, retries=3, timeout=900):
    body = json.dumps({"model": "qwen3:4b", "messages": messages, "temperature": 0}).encode()
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(f"{base_url}/chat/completions", data=body,
                                         headers={"Content-Type": "application/json", "Authorization": "Bearer local-no-key"})
            t0 = time.perf_counter()
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read()), time.perf_counter() - t0
        except (urllib.error.URLError, TimeoutError) as e:
            wait = min(8, 0.5 * 2 ** attempt) + random.uniform(0, 0.3)   # exponential backoff + jitter
            print(f"   attempt {attempt} failed ({type(e).__name__}: {getattr(e, 'reason', e)}); waiting {wait:.1f}s")
            if attempt == retries:
                raise
            time.sleep(wait)


print("1) wrong address: retries, then gives up cleanly")
try:
    call("http://localhost:9", [{"role": "user", "content": "hi"}], retries=2, timeout=2)
except Exception as e:
    print(f"   gave up: {type(e).__name__}  -> show the user a friendly error, log the details")

print("\n2) real call")
resp, secs = call(BASE_URL, [{"role": "system", "content": "You are a concise assistant for an Indian bank."},
                             {"role": "user", "content": "In two sentences, what is a UPI mandate?"}])
u = resp["usage"]
cost = (u["prompt_tokens"] * PRICE_PER_M["input"] + u["completion_tokens"] * PRICE_PER_M["output"]) / 1e6
print(f"   answer: {resp['choices'][0]['message']['content'].strip()}")
print(f"   finish_reason: {resp['choices'][0]['finish_reason']}   time: {secs:.1f}s")
print(f"   usage: {u}   (completion tokens include the model's hidden reasoning)")
print(f"   cost at the pretend price: ${cost:.6f}  -> x 1 million calls a month = ${cost * 1e6:,.0f}")

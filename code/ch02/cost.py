"""Chapter 2 lab: what does one agent task cost, and what does caching save?"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness.pricing import cost_usd
from harness.tokens import dominant_script, estimate_tokens
from harness.types import Usage

# 1) Same message, two languages
en = "Hello, my order has not arrived yet. Please tell me when it will be delivered."
hi = "नमस्ते, मेरा ऑर्डर अभी तक नहीं आया है। कृपया बताइए कि यह कब डिलीवर होगा।"
for label, t in [("English", en), ("Hindi", hi)]:
    print(f"{label:8s} {dominant_script(t):10s} ~{estimate_tokens(t):3d} tokens")

# 2) A 10-step agent task: 12k-token stable prefix (system + tools + docs), history grows 800 tokens per step
PREFIX, STEP, OUT = 12_000, 800, 300
model = "claude-sonnet-5-5"
no_cache, with_cache = Usage(), Usage()
for step in range(10):
    history = step * STEP
    no_cache = no_cache + Usage(PREFIX + history, OUT)
    if step == 0:
        with_cache = with_cache + Usage(history, OUT, 0, PREFIX)          # write prefix once
    else:
        # prefix + previous history read from cache; only the newest step is fresh
        with_cache = with_cache + Usage(STEP, OUT, PREFIX + history - STEP, 0)
print(f"\n10-step task on {model}")
print(f"  without caching: {no_cache.input_tokens:>7,} input tokens  ${cost_usd(model, no_cache):.4f}")
print(f"  with caching:    {with_cache.input_tokens + with_cache.cache_read_tokens + with_cache.cache_write_tokens:>7,} input tokens  ${cost_usd(model, with_cache):.4f}")
print(f"  saving: {1 - cost_usd(model, with_cache) / cost_usd(model, no_cache):.0%}")

# 3) Monthly bill for a support bot: 20,000 conversations x 6 turns
per_conv = Usage(6 * 3_000, 6 * 250)
for m in ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"]:
    print(f"  {m:18s} ${cost_usd(m, per_conv) * 20_000:>9,.2f} / month")

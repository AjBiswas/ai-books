"""Chapter 15 lab: how many GPUs does a self-hosted model need?

Memory = weights + KV cache + ~10% overhead. Throughput figures are rough planning numbers;
benchmark your own hardware with vLLM before buying.
"""
import math

MODELS = {  # params (billions), layers, kv_heads, head_dim
    "Llama-3.1-8B": (8, 32, 8, 128),
    "Llama-3.1-70B": (70, 80, 8, 128),
    "Qwen2.5-72B": (72, 80, 8, 128),
}
BYTES = {"bf16": 2, "fp8": 1, "int4": 0.5}
GPU_GB = 80


def plan(name, wq, kvq, ctx, users):
    p, layers, kvh, hd = MODELS[name]
    weights = p * 1e9 * BYTES[wq] / 1e9
    kv_per_tok = 2 * layers * kvh * hd * BYTES[kvq]
    kv = kv_per_tok * ctx * users / 1e9
    total = (weights + kv) * 1.10
    gpus = max(1, 2 ** math.ceil(math.log2(math.ceil(total / GPU_GB))))   # tensor-parallel sizes are powers of 2
    return weights, kv, total, gpus


print(f"{'model':15s} {'weights':>7s} {'KV':>4s} {'ctx':>6s} {'users':>5s} {'weights GB':>10s} {'KV GB':>8s} {'total GB':>9s} {'80GB GPUs':>9s}")
for name, wq, kvq, ctx, users in [
    ("Llama-3.1-8B", "bf16", "bf16", 8_192, 32),
    ("Llama-3.1-70B", "bf16", "bf16", 8_192, 32),
    ("Llama-3.1-70B", "fp8", "fp8", 8_192, 32),
    ("Llama-3.1-70B", "fp8", "fp8", 32_768, 32),
    ("Llama-3.1-70B", "int4", "fp8", 32_768, 64),
    ("Qwen2.5-72B", "fp8", "fp8", 16_384, 48),
]:
    w, kv, t, g = plan(name, wq, kvq, ctx, users)
    print(f"{name:15s} {wq:>7s} {kvq:>4s} {ctx:>6,} {users:>5d} {w:>10.0f} {kv:>8.0f} {t:>9.0f} {g:>9d}")

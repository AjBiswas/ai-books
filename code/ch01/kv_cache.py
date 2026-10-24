"""Chapter 1 lab: KV-cache memory calculator for capacity planning.

bytes_per_token = 2 (K and V) * n_layers * n_kv_heads * head_dim * bytes_per_value

Run:  python kv_cache.py
"""

MODELS = {
    # name: (n_layers, n_kv_heads, head_dim)  -- published configs
    "Llama-3.1-8B": (32, 8, 128),
    "Llama-3.1-70B": (80, 8, 128),
    "Qwen2.5-72B": (80, 8, 128),
    "Mistral-7B-v0.1": (32, 8, 128),
    "Hypothetical 70B, no GQA (64 KV heads)": (80, 64, 128),
}

DTYPE_BYTES = {"fp16/bf16": 2, "fp8": 1}


def kv_bytes_per_token(n_layers, n_kv_heads, head_dim, bytes_per_value=2):
    return 2 * n_layers * n_kv_heads * head_dim * bytes_per_value


def human(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.1f} PB"


if __name__ == "__main__":
    ctx = 128_000
    concurrent = 32
    print(f"Context {ctx:,} tokens, {concurrent} concurrent sequences\n")
    print(f"{'model':42s} {'dtype':10s} {'per token':>12s} {'per seq':>12s} {'x concurrency':>14s}")
    for name, cfg in MODELS.items():
        for dt, b in DTYPE_BYTES.items():
            per_tok = kv_bytes_per_token(*cfg, b)
            print(f"{name:42s} {dt:10s} {human(per_tok):>12s} {human(per_tok*ctx):>12s} {human(per_tok*ctx*concurrent):>14s}")

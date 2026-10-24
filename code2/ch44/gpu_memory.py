"""Book 1, Chapter 44 lab (part 1): will this model fit on that GPU? Back-of-envelope memory maths.

memory = weights + KV cache + overhead
  weights  = parameters x bytes per parameter (16-bit = 2 bytes, 8-bit = 1, 4-bit = 0.5)
  KV cache = 2 (K and V) x layers x kv_heads x head_dim x bytes x tokens in flight (all users)
Run:  python gpu_memory.py      (standard library only)
"""
MODELS = {   # name: (params in billions, layers, kv_heads, head_dim)   (typical published configs)
    "8B (Llama-3.1-8B shape)": (8.0, 32, 8, 128),
    "70B (Llama-3.1-70B shape)": (70.6, 80, 8, 128),
}
GPUS = {"laptop RTX 4060 (8 GB)": 8, "L4 (24 GB)": 24, "A100 (80 GB)": 80, "H100 (80 GB)": 80}


def need_gb(params_b, layers, kv_heads, head_dim, weight_bytes, users, ctx):
    weights = params_b * 1e9 * weight_bytes
    kv = 2 * layers * kv_heads * head_dim * 2 * users * ctx          # KV cache kept in 16-bit
    return (weights + kv) * 1.1 / 1e9                                 # +10% runtime overhead


print(f"{'model':28} {'precision':9} {'users x context':16} {'needs':>8}   fits on")
for name, cfg in MODELS.items():
    for prec, wb in (("16-bit", 2), ("8-bit", 1), ("4-bit", 0.5)):
        for users, ctx in ((1, 8_000), (32, 8_000)):
            gb = need_gb(*cfg, wb, users, ctx)
            fits = [g for g, mem in GPUS.items() if mem >= gb]
            where = fits[0] if fits else f"{-(-gb // 80):.0f}x 80 GB GPUs"
            print(f"{name:28} {prec:9} {users:>3} x {ctx:>6,}    {gb:7.1f} GB   {where}")

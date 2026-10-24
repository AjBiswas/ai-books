"""Book 1, Chapter 23 lab: why LoRA works. A weight update is often low-rank.

We fake a "fine-tuning update" dW that is mostly low-rank plus noise, then see how well
a rank-r LoRA (dW ~= B @ A) captures it, and how many parameters that needs.
Run:  python lora_math.py      Needs: numpy
"""
import numpy as np

rng = np.random.default_rng(0)
d = 4096                                  # hidden size of a 7-8B model layer
true_rank = 8
dW = rng.normal(size=(d, true_rank)) @ rng.normal(size=(true_rank, d)) / np.sqrt(d)
dW += 0.02 * rng.normal(size=(d, d)) / np.sqrt(d)     # a little full-rank noise

U, S, Vt = np.linalg.svd(dW, full_matrices=False)
full = d * d
print(f"full update: {full:,} parameters per {d}x{d} matrix")
print(f"{'rank r':>7s} {'LoRA params':>12s} {'% of full':>9s} {'update captured':>16s}")
for r in [1, 2, 4, 8, 16, 64]:
    approx = (U[:, :r] * S[:r]) @ Vt[:r]                   # best rank-r: B = U*S, A = Vt
    captured = 1 - np.linalg.norm(dW - approx) / np.linalg.norm(dW)
    params = 2 * d * r
    print(f"{r:7d} {params:12,d} {100 * params / full:8.2f}% {100 * captured:15.1f}%")

# Memory for fine-tuning an 8B model: full vs LoRA vs QLoRA (rough, Adam optimiser)
P = 8e9
lora_P = 0.005 * P                        # ~0.5% trainable with LoRA on attention + MLP
print("\nRough GPU memory to fine-tune an 8B model")
print(f"  full fine-tune (bf16 weights + grads + Adam fp32 states): {P*2/1e9 + P*2/1e9 + P*8/1e9:6.0f} GB")
print(f"  LoRA  (bf16 frozen weights + small adapters):             {P*2/1e9 + lora_P*12/1e9:6.0f} GB")
print(f"  QLoRA (4-bit frozen weights + small adapters):            {P*0.5/1e9 + lora_P*12/1e9:6.0f} GB")

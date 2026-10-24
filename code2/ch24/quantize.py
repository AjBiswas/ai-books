"""Book 1, Chapter 24 lab: quantisation by hand. Squeeze weights into 8 and 4 bits; measure the cost.

Weights are stored as small integers plus one scale per group of 32 (the idea behind GGUF Q4/Q8).
We measure memory saved, how far the weights moved, and how much a layer's output changes.
Run:  python quantize.py      (needs only numpy)
"""
import numpy as np

rng = np.random.default_rng(0)
W = rng.normal(0, 0.02, (4096, 4096)).astype(np.float32)   # one layer of a 7B-class model
x = rng.normal(0, 1, (8, 4096)).astype(np.float32)          # 8 tokens going through it
y = x @ W


def quantise(W, bits, group=32):
    q_max = 2 ** (bits - 1) - 1                               # 127 for 8-bit, 7 for 4-bit
    g = W.reshape(-1, group)
    scale = np.abs(g).max(1, keepdims=True) / q_max           # one scale per group of 32
    q = np.clip(np.round(g / scale), -q_max, q_max).astype(np.int8)
    return q, scale.astype(np.float16)


def dequantise(q, scale, shape):
    return (q.astype(np.float32) * scale.astype(np.float32)).reshape(shape)


print(f"{'format':8} {'size of this layer':>19} {'weight error':>13} {'output error':>13}")
print(f"{'fp32':8} {W.nbytes / 2**20:16.1f} MB {'0':>13} {'0':>13}")
print(f"{'fp16':8} {W.astype(np.float16).nbytes / 2**20:16.1f} MB "
      f"{np.abs(W - W.astype(np.float16)).mean() / np.abs(W).mean():12.3%} "
      f"{np.abs(y - x @ W.astype(np.float16).astype(np.float32)).mean() / np.abs(y).mean():12.3%}")
for bits in (8, 4, 2):
    q, s = quantise(W, bits)
    Wq = dequantise(q, s, W.shape)
    size = W.size * bits / 8 + s.size * 2                     # packed integers + fp16 scales
    werr = np.abs(W - Wq).mean() / np.abs(W).mean()
    oerr = np.abs(y - x @ Wq).mean() / np.abs(y).mean()
    print(f"{'int' + str(bits):8} {size / 2**20:16.1f} MB {werr:12.1%} {oerr:12.1%}")
print("\n7B model in fp16 = ~14 GB; in 4-bit = ~4 GB: the difference between 'no' and 'yes' on a laptop.")

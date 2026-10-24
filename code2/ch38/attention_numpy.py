"""Book 1, Chapter 38 lab: one transformer block, forward pass, in plain numpy.

Follow 6 tokens through: embeddings + positions -> layer norm -> causal self-attention
(several heads) -> residual -> layer norm -> MLP -> residual. Shapes are printed at every
stage. Weights are random, so the attention pattern is not meaningful yet; Chapter 39 trains them.
Run:  python attention_numpy.py      (needs only numpy)
"""
import numpy as np

rng = np.random.default_rng(42)
tokens = ["Haron", " reads", " the", " long", " contract", "."]
T, d, H = len(tokens), 16, 2          # 6 tokens, 16 numbers per token, 2 attention heads
dh = d // H                           # 8 numbers per head

vocab = {t: i for i, t in enumerate(tokens)}
E = rng.normal(0, 0.5, (len(vocab), d))          # token embedding table
Ppos = rng.normal(0, 0.5, (T, d))                # position embedding table
Wq, Wk, Wv, Wo = (rng.normal(0, d ** -0.5, (d, d)) for _ in range(4))
W1, W2 = rng.normal(0, d ** -0.5, (d, 4 * d)), rng.normal(0, (4 * d) ** -0.5, (4 * d, d))


def layer_norm(x):
    return (x - x.mean(-1, keepdims=True)) / np.sqrt(x.var(-1, keepdims=True) + 1e-5)


def softmax(z):
    z = z - z.max(-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(-1, keepdims=True)


x = E[[vocab[t] for t in tokens]] + Ppos
print(f"1. embeddings + positions   x      {x.shape}   one row of {d} numbers per token")

h = layer_norm(x)
q, k, v = h @ Wq, h @ Wk, h @ Wv
print(f"2. queries, keys, values    q,k,v  {q.shape}   'what I look for / what I offer / what I pass on'")

q, k, v = (m.reshape(T, H, dh).transpose(1, 0, 2) for m in (q, k, v))   # split into heads
scores = q @ k.transpose(0, 2, 1) / np.sqrt(dh)                          # (H, T, T)
mask = np.triu(np.ones((T, T), dtype=bool), 1)                           # no peeking at the future
scores[:, mask] = -np.inf
att = softmax(scores)
print(f"3. attention weights        att    {att.shape}   per head: who looks at whom")

out = (att @ v).transpose(1, 0, 2).reshape(T, d) @ Wo
x = x + out                                                              # residual: add, don't replace
print(f"4. after attention + residual       {x.shape}")

m = np.maximum(0, layer_norm(x) @ W1) @ W2                               # MLP: widen to {4d}, then back
x = x + m
print(f"5. after MLP + residual             {x.shape}   ready for the next block")

params = sum(a.size for a in (Wq, Wk, Wv, Wo, W1, W2))
print(f"\nweights in this one block: {params:,}  (a 7B model has ~32 blocks with d = 4096)")

print("\nhead 1 attention (each row sums to 1; zeros above the diagonal = causal mask)")
print("            " + "".join(f"{t.strip()[:7]:>8}" for t in tokens))
for t, row in zip(tokens, att[0]):
    print(f"{t.strip():>10}  " + "".join(f"{p:8.2f}" for p in row))

"""Book 1, Chapter 39 lab: train a tiny GPT from scratch, in plain numpy, on your laptop.

A character-level language model with the real parts of a GPT: token + position embeddings,
one causal self-attention layer, an MLP, residual connections and a softmax over the vocabulary.
No deep-learning library: the backward pass is written by hand and checked numerically.
Training text: haron.txt (about 1,900 characters). Takes a minute or two on a laptop CPU.
Run:  python tiny_gpt.py      (needs only numpy)
"""
import os
import time

import numpy as np

text = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "haron.txt"), encoding="utf-8").read()
chars = sorted(set(text))
V, T, d, B = len(chars), 32, 48, 32          # vocab, context length, width, batch size
stoi = {c: i for i, c in enumerate(chars)}
data = np.array([stoi[c] for c in text])
print(f"text: {len(text)} characters, vocabulary: {V} characters, context: {T}, width: {d}")

rng = np.random.default_rng(0)
s = 0.08
P = {
    "E": rng.normal(0, s, (V, d)), "pos": rng.normal(0, s, (T, d)),
    "Wq": rng.normal(0, s, (d, d)), "Wk": rng.normal(0, s, (d, d)), "Wv": rng.normal(0, s, (d, d)), "Wo": rng.normal(0, s, (d, d)),
    "W1": rng.normal(0, s, (d, 4 * d)), "b1": np.zeros(4 * d), "W2": rng.normal(0, s, (4 * d, d)), "b2": np.zeros(d),
    "Wout": rng.normal(0, s, (d, V)), "bout": np.zeros(V),
}
print(f"parameters: {sum(p.size for p in P.values()):,}")
MASK = np.triu(np.ones((T, T), dtype=bool), 1)


def softmax(z):
    z = z - z.max(-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(-1, keepdims=True)


def forward(P, idx, targets=None):
    n = idx.shape[1]
    x0 = P["E"][idx] + P["pos"][:n]
    q, k, v = x0 @ P["Wq"], x0 @ P["Wk"], x0 @ P["Wv"]
    sc = q @ k.transpose(0, 2, 1) / np.sqrt(d)
    sc[:, MASK[:n, :n]] = -1e9                       # causal mask: no looking ahead
    a = softmax(sc)
    o = a @ v
    x1 = x0 + o @ P["Wo"]                            # residual 1
    hpre = x1 @ P["W1"] + P["b1"]
    h = np.maximum(0, hpre)
    x2 = x1 + h @ P["W2"] + P["b2"]                  # residual 2
    logits = x2 @ P["Wout"] + P["bout"]
    cache = (idx, x0, q, k, v, a, o, x1, hpre, h, x2, logits)
    if targets is None:
        return logits, None, cache
    p = softmax(logits)
    loss = -np.mean(np.log(np.take_along_axis(p, targets[..., None], -1) + 1e-12))
    return logits, loss, cache


def backward(P, cache, targets):
    idx, x0, q, k, v, a, o, x1, hpre, h, x2, logits = cache
    Bn, n = idx.shape
    g = {}
    dl = softmax(logits)
    np.put_along_axis(dl, targets[..., None], np.take_along_axis(dl, targets[..., None], -1) - 1, -1)
    dl /= Bn * n                                     # d(loss)/d(logits)
    g["Wout"] = np.einsum("btd,btv->dv", x2, dl); g["bout"] = dl.sum((0, 1))
    dx2 = dl @ P["Wout"].T
    dm = dx2                                         # MLP branch
    g["W2"] = np.einsum("btf,btd->fd", h, dm); g["b2"] = dm.sum((0, 1))
    dhpre = (dm @ P["W2"].T) * (hpre > 0)
    g["W1"] = np.einsum("btd,btf->df", x1, dhpre); g["b1"] = dhpre.sum((0, 1))
    dx1 = dx2 + dhpre @ P["W1"].T                    # residual: gradient flows straight through
    g["Wo"] = np.einsum("btd,bte->de", o, dx1)
    do = dx1 @ P["Wo"].T
    da = do @ v.transpose(0, 2, 1)
    dv = a.transpose(0, 2, 1) @ do
    ds = a * (da - (da * a).sum(-1, keepdims=True)) / np.sqrt(d)   # back through softmax
    dq = ds @ k
    dk = ds.transpose(0, 2, 1) @ q
    g["Wq"] = np.einsum("btd,bte->de", x0, dq)
    g["Wk"] = np.einsum("btd,bte->de", x0, dk)
    g["Wv"] = np.einsum("btd,bte->de", x0, dv)
    dx0 = dx1 + dq @ P["Wq"].T + dk @ P["Wk"].T + dv @ P["Wv"].T
    g["E"] = np.zeros_like(P["E"]); np.add.at(g["E"], idx, dx0)
    g["pos"] = np.zeros_like(P["pos"]); g["pos"][:n] = dx0.sum(0)
    return g


def batch():
    ix = rng.integers(0, len(data) - T - 1, B)
    return np.stack([data[i:i + T] for i in ix]), np.stack([data[i + 1:i + T + 1] for i in ix])


def sample(P, start="haron ", n=120, temp=0.7):
    out = [stoi[c] for c in start]
    for _ in range(n):
        ctx = np.array([out[-T:]])
        logits, _, _ = forward(P, ctx)
        p = softmax(logits[0, -1] / temp)
        out.append(int(rng.choice(V, p=p)))
    return "".join(chars[i] for i in out)


# 1) trust the maths: compare backprop with a numerical gradient on a few weights
xb, yb = batch()
_, loss, cache = forward(P, xb, yb)
g = backward(P, cache, yb)
worst = 0.0
for name in ("Wq", "W1", "E"):
    i, j = 1, 2
    P[name][i, j] += 1e-5
    num = (forward(P, xb, yb)[1] - loss) / 1e-5
    P[name][i, j] -= 1e-5
    worst = max(worst, abs(num - g[name][i, j]))
print(f"gradient check: largest difference backprop vs numerical = {worst:.1e}")

print("\nbefore training:\n  " + sample(P).replace("\n", " ")[:120])

# 2) train with Adam
m = {k_: np.zeros_like(v_) for k_, v_ in P.items()}
vv = {k_: np.zeros_like(v_) for k_, v_ in P.items()}
lr, b1_, b2_ = 3e-3, 0.9, 0.999
t0 = time.perf_counter()
for step in range(1, 2001):
    xb, yb = batch()
    _, loss, cache = forward(P, xb, yb)
    g = backward(P, cache, yb)
    for k_ in P:
        m[k_] = b1_ * m[k_] + (1 - b1_) * g[k_]
        vv[k_] = b2_ * vv[k_] + (1 - b2_) * g[k_] ** 2
        P[k_] -= lr * (m[k_] / (1 - b1_ ** step)) / (np.sqrt(vv[k_] / (1 - b2_ ** step)) + 1e-8)
    if step in (1, 100, 250, 500, 1000, 1500, 2000):
        print(f"step {step:4d}  loss {loss:.3f}   ({time.perf_counter() - t0:.0f}s)")

print(f"\n(a random guess over {V} characters would score loss {np.log(V):.2f})")
print("\nafter training:")
for start in ("haron ", "the user asks about the "):
    print("  " + sample(P, start).replace("\n", " | "))

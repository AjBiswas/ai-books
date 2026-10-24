"""Chapter 1 lab: causal multi-head self-attention from scratch, with a KV cache.

Run:  python attention.py
Needs: numpy
"""
import numpy as np

rng = np.random.default_rng(0)


def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)  # subtract max for numerical stability
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


class CausalSelfAttention:
    """One attention layer: d_model split across n_heads heads of size d_head."""

    def __init__(self, d_model=64, n_heads=4):
        assert d_model % n_heads == 0
        self.h, self.dh = n_heads, d_model // n_heads
        s = 1 / np.sqrt(d_model)
        self.Wq = rng.normal(0, s, (d_model, d_model))
        self.Wk = rng.normal(0, s, (d_model, d_model))
        self.Wv = rng.normal(0, s, (d_model, d_model))
        self.Wo = rng.normal(0, s, (d_model, d_model))

    def _split(self, x):  # (T, d_model) -> (h, T, dh)
        T = x.shape[0]
        return x.reshape(T, self.h, self.dh).transpose(1, 0, 2)

    def forward(self, x, cache=None):
        """x: (T, d_model) new tokens. cache: dict with past 'k','v' of shape (h, T_past, dh).

        Returns (output, updated_cache, attention_weights).
        """
        q, k, v = self._split(x @ self.Wq), self._split(x @ self.Wk), self._split(x @ self.Wv)
        if cache is not None:
            k = np.concatenate([cache["k"], k], axis=1)
            v = np.concatenate([cache["v"], v], axis=1)
        T_new, T_all = q.shape[1], k.shape[1]

        scores = q @ k.transpose(0, 2, 1) / np.sqrt(self.dh)  # (h, T_new, T_all)
        # Causal mask: query i (absolute position T_all-T_new+i) may only see keys <= its position.
        offset = T_all - T_new
        mask = np.triu(np.ones((T_new, T_all), dtype=bool), k=offset + 1)
        scores = np.where(mask, -np.inf, scores)
        w = softmax(scores, axis=-1)
        out = (w @ v).transpose(1, 0, 2).reshape(T_new, -1) @ self.Wo
        return out, {"k": k, "v": v}, w


if __name__ == "__main__":
    attn = CausalSelfAttention(d_model=64, n_heads=4)
    T = 6
    x = rng.normal(size=(T, 64))

    # 1) Prefill: process the whole prompt at once.
    full_out, _, w = attn.forward(x)
    print("Head 0 attention weights (rows = query, cols = key):")
    print(np.round(w[0], 2))

    # 2) Decode: feed tokens one at a time, reusing the KV cache.
    cache, outs = None, []
    for t in range(T):
        o, cache, _ = attn.forward(x[t : t + 1], cache)
        outs.append(o)
    step_out = np.vstack(outs)

    print("\nPrefill output == incremental (KV-cached) output:", np.allclose(full_out, step_out))
    print("Cached K shape (heads, tokens, d_head):", cache["k"].shape)

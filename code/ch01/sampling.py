"""Chapter 1 lab: the decoding knobs a harness exposes -- temperature, top-k, top-p, min-p.

Run:  python sampling.py
Needs: numpy
"""
import numpy as np


def softmax(x):
    x = x - x.max()
    e = np.exp(x)
    return e / e.sum()


def sample_distribution(logits, temperature=1.0, top_k=0, top_p=1.0, min_p=0.0):
    """Return the final probability distribution the sampler draws from.

    Order matches most inference servers (vLLM, llama.cpp): temperature, then truncation.
    """
    logits = np.asarray(logits, dtype=np.float64)
    if temperature <= 0:  # greedy: all mass on the argmax
        p = np.zeros_like(logits)
        p[np.argmax(logits)] = 1.0
        return p

    p = softmax(logits / temperature)
    keep = np.ones_like(p, dtype=bool)

    if top_k > 0:
        kth = np.sort(p)[-top_k]
        keep &= p >= kth

    if top_p < 1.0:
        order = np.argsort(-p)
        cum = np.cumsum(p[order])
        # keep the smallest prefix whose mass reaches top_p (always keep the first token)
        cutoff = np.searchsorted(cum, top_p) + 1
        nucleus = np.zeros_like(keep)
        nucleus[order[:cutoff]] = True
        keep &= nucleus

    if min_p > 0:
        keep &= p >= min_p * p.max()

    p = np.where(keep, p, 0.0)
    return p / p.sum()


if __name__ == "__main__":
    vocab = ["Paris", "Lyon", "the", "France", "a", "Marseille", "banana", "<eos>"]
    logits = [6.0, 3.1, 2.8, 2.5, 2.0, 1.9, -1.0, 0.5]

    for cfg in [
        dict(temperature=0),
        dict(temperature=0.7),
        dict(temperature=1.0),
        dict(temperature=1.5),
        dict(temperature=1.0, top_p=0.9),
        dict(temperature=1.5, min_p=0.05),
    ]:
        p = sample_distribution(logits, **cfg)
        entropy = max(0.0, -(p[p > 0] * np.log2(p[p > 0])).sum())
        top = ", ".join(f"{vocab[i]}={p[i]:.3f}" for i in np.argsort(-p)[:4] if p[i] > 0)
        print(f"{str(cfg):45s} H={entropy:4.2f} bits | {top}")

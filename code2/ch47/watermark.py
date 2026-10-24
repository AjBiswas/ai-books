"""Book 1, Chapter 47 lab (part 1): a statistical text watermark, and how editing weakens it.

The "green list" idea (Kirchenbauer et al., 2023): before choosing each word, a secret key and the
previous word split the vocabulary into green and red halves; the generator gently prefers green
words. Normal text is ~50% green by chance. Watermarked text is far greener, which a detector
holding the key can test with a z-score. No model internals are needed to detect it.
To stay self-contained, the "language model" here is a toy that picks from a 1,000-word vocabulary.
Run:  python watermark.py      (needs only numpy)
"""
import hashlib

import numpy as np

V, GAMMA, DELTA, N = 1000, 0.5, 2.5, 200     # vocab, green share, green boost, words per text
KEY = b"provider-secret"
rng = np.random.default_rng(7)
base_logits = rng.normal(0, 2, V)            # the toy model's word preferences


def green(prev):
    seed = int.from_bytes(hashlib.sha256(KEY + prev.to_bytes(4, "little")).digest()[:8], "little")
    return np.random.default_rng(seed).permutation(V)[: int(GAMMA * V)]


def generate(watermark):
    out = [0]
    for _ in range(N):
        logits = base_logits + rng.normal(0, 1, V)          # context-dependent wobble
        if watermark:
            logits[green(out[-1])] += DELTA
        p = np.exp(logits - logits.max()); p /= p.sum()
        out.append(int(rng.choice(V, p=p)))
    return out


def z_score(words):
    hits = sum(w in set(green(prev)) for prev, w in zip(words, words[1:]))
    n = len(words) - 1
    return hits / n, (hits - GAMMA * n) / np.sqrt(n * GAMMA * (1 - GAMMA))


def paraphrase(words, share):
    """Replace a share of the words with random ones (what light or heavy editing does)."""
    w = list(words)
    for i in rng.choice(np.arange(1, len(w)), int(share * (len(w) - 1)), replace=False):
        w[i] = int(rng.integers(V))
    return w


human = generate(watermark=False)
ai = generate(watermark=True)
print("text                          green share   z-score   verdict (z > 4 = watermarked)")
for label, words in [("human-written (no watermark)", human), ("AI with watermark", ai),
                     ("AI, 20% of words edited", paraphrase(ai, 0.2)), ("AI, 50% of words edited", paraphrase(ai, 0.5)),
                     ("AI, 80% of words edited", paraphrase(ai, 0.8))]:
    g, z = z_score(words)
    print(f"{label:30} {g:6.0%}      {z:6.1f}    {'WATERMARKED' if z > 4 else 'not detected'}")

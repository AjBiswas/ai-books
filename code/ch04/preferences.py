"""Chapter 4 lab: how preference training shapes behaviour, and how a reward model gets hacked.

A toy policy chooses between 4 answer styles. We learn a reward model from human comparisons
(Bradley-Terry), then optimise the policy with a DPO-style update. Needs numpy.
"""
import numpy as np

rng = np.random.default_rng(0)
styles = ["short + correct", "long + correct", "long + padded", "confident + wrong"]
true_quality = np.array([0.9, 1.0, 0.4, -1.0])        # what people actually value
length = np.array([1.0, 3.0, 5.0, 1.5])               # answer length (arbitrary units)

# --- 1) Human labellers compare pairs; they also like longer answers (a real, documented bias)
def human_prefers(a, b):
    score = lambda i: true_quality[i] + 0.6 * length[i]
    p = 1 / (1 + np.exp(-(score(a) - score(b)) * 3))
    return rng.random() < p

pairs = [(a, b) for a in range(4) for b in range(4) if a != b] * 200
wins = [(a, b) if human_prefers(a, b) else (b, a) for a, b in pairs]

# --- 2) Fit a Bradley-Terry reward model r(style) on features [quality signal, length]
X = np.stack([true_quality + rng.normal(0, 0.3, 4), length], axis=1)
w = np.zeros(2)
for _ in range(500):
    grad = np.zeros(2)
    for win, lose in wins:
        d = X[win] - X[lose]
        grad += d * (1 - 1 / (1 + np.exp(-w @ d)))
    w += 0.5 * grad / len(wins)
reward = X @ w
print("reward model weights  [quality, length] =", np.round(w, 2))
for s, r in zip(styles, reward):
    print(f"  reward({s:18s}) = {r:+.2f}")

# --- 3) Optimise the policy against the reward model (RLHF-style), with a KL leash to the start
ref = np.full(4, 0.25)


def train(beta, steps, lr=0.05):
    pol = np.zeros(4)
    for _ in range(steps):
        p = np.exp(pol) / np.exp(pol).sum()
        # gradient of  E_p[r] - beta * KL(p || ref)  with respect to the logits
        lr_term = np.log(p / ref)
        grad = p * (reward - p @ reward) - beta * p * (lr_term - p @ lr_term)
        pol += lr * grad
    return np.exp(pol) / np.exp(pol).sum()


print("\nOptimising harder and harder against the reward model (weak KL leash, beta=0.05):")
print(f"  {'steps':>5s}  {'reward':>6s}  {'TRUE quality':>12s}   P(padded)")
for steps in [0, 10, 30, 100, 400]:
    p = train(0.05, steps)
    print(f"  {steps:5d}  {p @ reward:+6.2f}  {p @ true_quality:+12.2f}   {p[2]:.2f}")
p = train(2.0, 400)
print(f"Strong KL leash (beta=2.0), 400 steps: reward {p @ reward:+.2f}, TRUE quality {p @ true_quality:+.2f}, P(padded) {p[2]:.2f}")

# --- 4) DPO loss for one preference pair, the closed form used in practice
def dpo_loss(pi_w, pi_l, ref_w, ref_l, beta=0.1):
    z = beta * ((np.log(pi_w) - np.log(ref_w)) - (np.log(pi_l) - np.log(ref_l)))
    return -np.log(1 / (1 + np.exp(-z)))
print("\nDPO loss before update:", round(dpo_loss(0.25, 0.25, 0.25, 0.25), 4),
      "| after preferring the winner:", round(dpo_loss(0.6, 0.1, 0.25, 0.25), 4))

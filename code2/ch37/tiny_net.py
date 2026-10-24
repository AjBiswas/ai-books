"""Book 1, Chapter 37 lab (part 2): a two-layer neural network learns XOR with backpropagation.

XOR can't be drawn with one straight line, so a single neuron fails; a hidden layer fixes it.
Every gradient is written by hand (backpropagation = the chain rule, layer by layer),
and checked against a slow numerical estimate so you can trust it.
Run:  python tiny_net.py      (needs only numpy)
"""
import numpy as np

X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
Y = np.array([[0], [1], [1], [0]], dtype=float)

rng = np.random.default_rng(1)
P = {"W1": rng.normal(0, 1, (2, 4)), "b1": np.zeros(4), "W2": rng.normal(0, 1, (4, 1)), "b2": np.zeros(1)}


def sigmoid(z):
    return 1 / (1 + np.exp(-z))


def forward(P):
    h = np.tanh(X @ P["W1"] + P["b1"])                # hidden layer: 4 neurons
    p = sigmoid(h @ P["W2"] + P["b2"])                # output: probability of "1"
    loss = -np.mean(Y * np.log(p) + (1 - Y) * np.log(1 - p))
    return h, p, loss


def backward(P, h, p):
    n = len(X)
    dz2 = (p - Y) / n                                 # loss -> output pre-activation
    g = {"W2": h.T @ dz2, "b2": dz2.sum(0)}
    dh = dz2 @ P["W2"].T                              # pass the blame back to the hidden layer
    dz1 = dh * (1 - h ** 2)                           # through tanh
    g["W1"] = X.T @ dz1
    g["b1"] = dz1.sum(0)
    return g


# gradient check: nudge one weight and see how the loss moves
h, p, loss = forward(P)
g = backward(P, h, p)
eps = 1e-5
P["W1"][0, 0] += eps
numeric = (forward(P)[2] - loss) / eps
P["W1"][0, 0] -= eps
print(f"gradient check  backprop {g['W1'][0, 0]:+.6f}   numerical {numeric:+.6f}")

for step in range(2001):
    h, p, loss = forward(P)
    g = backward(P, h, p)
    for k in P:
        P[k] -= 1.0 * g[k]
    if step in (0, 100, 500, 1000, 2000):
        print(f"step {step:4d}  loss {loss:.4f}   predictions {np.round(p.ravel(), 2)}")

print("\ninputs     target  prediction")
for xi, yi, pi in zip(X, Y, forward(P)[1]):
    print(f"{xi.astype(int)}   {int(yi[0])}       {pi[0]:.3f}")

"""Book 1, Chapter 37 lab (part 1): gradient descent learns a straight line.

The model is y = w*x + b. It starts knowing nothing (w=0, b=0) and must discover
the hidden rule y = 2x + 1 from examples, by following the slope of the loss downhill.
Run:  python learn_line.py      (needs only numpy)
"""
import numpy as np

rng = np.random.default_rng(0)
x = rng.uniform(-3, 3, 50)
y = 2 * x + 1 + rng.normal(0, 0.2, 50)        # the hidden rule, plus a little noise

w, b, lr = 0.0, 0.0, 0.05                     # start knowing nothing; lr = step size
for step in range(101):
    pred = w * x + b
    err = pred - y
    loss = np.mean(err ** 2)                  # mean squared error: how wrong we are
    dw = np.mean(2 * err * x)                 # slope of the loss with respect to w
    db = np.mean(2 * err)                     # ... and with respect to b
    w -= lr * dw                              # step downhill
    b -= lr * db
    if step in (0, 1, 2, 5, 10, 20, 50, 100):
        print(f"step {step:3d}  loss {loss:7.3f}   w {w:5.2f}  b {b:5.2f}")

print(f"\nlearned: y = {w:.2f}x + {b:.2f}   (hidden rule: y = 2x + 1)")

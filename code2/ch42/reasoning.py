"""Book 1, Chapter 42 lab (part 1): self-consistency and a tiny tree of thoughts.

Self-consistency: ask the same question several times with some randomness, take the majority answer.
Tree of thoughts (lite): propose several different approaches, let the model score each one,
then expand only the most promising. Both spend more compute at answer time to be more reliable.
Setup:  ollama pull qwen3:4b
Run:    python reasoning.py
"""
import collections
import json
import re
import urllib.request


def chat(prompt, temperature=0.0, seed=0):
    body = {"model": "qwen3:4b", "stream": False, "think": True,
            "options": {"temperature": temperature, "seed": seed, "num_predict": 4096},
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["message"]["content"]


def final_number(text):
    nums = re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    return nums[-1] if nums else "?"


Q = ("A shop sells pens in packs of 12 for 90 rupees and single pens for 9 rupees each. "
     "What is the cheapest price, in rupees, for exactly 30 pens? Think briefly, then end with 'ANSWER: <number>'.")
print("1) self-consistency (correct answer: 2 packs + 6 singles = 234)")
votes = []
for seed in range(5):
    a = final_number(chat(Q, temperature=0.9, seed=seed))
    votes.append(a)
    print(f"   sample {seed + 1}: {a}")
winner, n = collections.Counter(votes).most_common(1)[0]
print(f"   majority: {winner} ({n} of 5 votes)")

print("\n2) tree of thoughts (lite)")
TASK = "Plan a 1-day team offsite in Pune for 12 people with a budget of 30,000 rupees, including lunch."
ideas = chat(f"{TASK}\nPropose 3 very different approaches, one line each, numbered 1-3. No details.", temperature=0.7, seed=1)
lines = [l.strip() for l in ideas.splitlines() if re.match(r"\s*[1-3][.)]", l)][:3]
for l in lines:
    print("   branch", l[:110])
scores = []
for l in lines:
    s = chat(f"{TASK}\nApproach: {l}\nRate how likely this fits the budget and works for 12 people, 1-10. Reply with just the number.")
    scores.append(int(final_number(s)) if final_number(s).isdigit() else 0)
best = lines[scores.index(max(scores))]
print(f"   scores: {scores} -> expand branch: {best[:80]}")
plan = chat(f"{TASK}\nUse this approach: {best}\nGive a 4-line plan with a cost per line and a total.")
print("   " + plan.strip().replace("\n", "\n   "))

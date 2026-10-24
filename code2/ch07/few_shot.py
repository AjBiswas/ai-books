"""Book 1, Chapter 7 lab: zero-shot versus few-shot on a task with house rules.

Task: tag Hinglish customer reviews as positive / negative / mixed, where the company's rule is
"any complaint about delivery makes it at least mixed". Examples teach the rule better than words.
Setup:  ollama pull qwen3:4b
Run:    python few_shot.py
"""
import json
import urllib.request

RULE = "Tag the review as positive, negative or mixed. Reply with one word."
SHOTS = [("Product mast hai, bas delivery 4 din late aayi", "mixed"),
         ("Bekaar quality, paisa waste", "negative"),
         ("Ekdum badhiya, time pe aaya, packing bhi achhi", "positive")]
TESTS = [("Phone accha hai but courier wale ne box phaad diya", "mixed"),
         ("Sabse best purchase, family ko bhi pasand aaya", "positive"),
         ("Kaam ka nahi, return bhi nahi ho raha", "negative"),
         ("Taste zabardast, lekin parcel do din der se mila", "mixed"),
         ("Size chhota nikla, wapas karna pada", "negative"),
         ("Superb sound quality, delivery boy bhi polite tha", "positive")]


def tag(review, shots):
    msgs = [{"role": "system", "content": RULE}]
    for x, y in shots:
        msgs += [{"role": "user", "content": x}, {"role": "assistant", "content": y}]
    msgs.append({"role": "user", "content": review})
    body = {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0, "num_predict": 4096}, "messages": msgs}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        out = json.loads(r.read())["message"]["content"].strip().lower()
    return next((w for w in ("positive", "negative", "mixed") if w in out), out[:10])


for label, shots in (("zero-shot", []), ("few-shot (3 examples)", SHOTS)):
    got = [tag(x, shots) for x, _ in TESTS]
    right = sum(g == y for g, (_, y) in zip(got, TESTS))
    print(f"{label:22} {right}/{len(TESTS)} correct   {got}")
print(f"{'expected':22}               {[y for _, y in TESTS]}")

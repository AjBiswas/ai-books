"""Book 1, Chapter 25 lab: generate synthetic test data, then filter it.

A grid of personas x topics x moods drives generation, so the data is varied on purpose.
Every sample is then checked: valid JSON, label from the allowed set, not a near-duplicate.
Setup:  ollama pull qwen3:4b
Run:    python synthetic_data.py
"""
import difflib
import itertools
import json
import re
import urllib.request

PERSONAS = ["college student in Indore writing Hinglish", "retired bank manager in Chennai, formal English"]
TOPICS = ["refund", "late delivery", "login problem"]
MOODS = ["calm", "angry"]
LABELS = {"refund": "billing", "late delivery": "delivery", "login problem": "account"}


def chat(prompt, seed):
    body = {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0.9, "seed": seed, "num_predict": 4096},
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["message"]["content"]


kept, rejected = [], []
for seed, (persona, topic, mood) in enumerate(itertools.product(PERSONAS, TOPICS, MOODS)):
    raw = chat(f"Write one realistic customer support message. Writer: {persona}. Topic: {topic}. Mood: {mood}. "
               f'Max 2 sentences. Reply ONLY as JSON: {{"text": "...", "label": "{LABELS[topic]}"}}', seed)
    try:
        item = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
        assert item["label"] in LABELS.values(), "bad label"
        assert 5 <= len(item["text"].split()) <= 60, "bad length"
        dup = max((difflib.SequenceMatcher(None, item["text"].lower(), k["text"].lower()).ratio() for k in kept), default=0)
        assert dup < 0.8, f"near-duplicate ({dup:.2f})"
        kept.append(item)
        print(f"KEEP  [{item['label']:8}] {item['text']}")
    except Exception as e:
        rejected.append(str(e))
        print(f"DROP  {e}")
print(f"\n{len(kept)} kept, {len(rejected)} dropped. Next: a human spot-checks 10%, then the set becomes an eval (Ch 26).")

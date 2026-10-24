"""Book 1, Chapter 42 lab (part 2): episodic memory for an assistant.

Each finished conversation becomes an "episode": a one-line summary written by the model, stored
with its date and an embedding. Next session, the assistant recalls the most relevant past episodes
and puts only those in the context. This is how "continual learning" is usually faked today: the
model's weights never change; its memory does.
Setup:  ollama pull qwen3:4b ; ollama pull all-minilm
Run:    python episodic_memory.py
"""
import json
import math
import sqlite3
import urllib.request

API = "http://localhost:11434/api"


def post(path, body):
    req = urllib.request.Request(f"{API}/{path}", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())


def chat(prompt):
    return post("chat", {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0, "num_predict": 4096},
                         "messages": [{"role": "user", "content": prompt}]})["message"]["content"].strip()


def embed(text):
    return post("embed", {"model": "all-minilm", "input": [text]})["embeddings"][0]


def cos(a, b):
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE episodes (day TEXT, summary TEXT, vec TEXT)")

PAST = [
    ("2026-09-03", "User: my laptop battery drains in 2 hours. Assistant: suggested battery report; user found Teams using 40% CPU and disabled it at startup."),
    ("2026-09-19", "User: need a vegetarian restaurant near Koregaon Park for 6 people Friday. Assistant: booked 'Green Leaf' 8 pm, table for 6."),
    ("2026-10-07", "User: my laptop is slow again after the Windows update. Assistant: rolled back the graphics driver; speed back to normal."),
]
for day, convo in PAST:
    summary = chat(f"Summarise this support conversation in one line, keeping the problem and the fix:\n{convo}")
    db.execute("INSERT INTO episodes VALUES (?,?,?)", (day, summary, json.dumps(embed(summary))))
    print(f"stored {day}: {summary}")

question = "My laptop is crawling again today, what should I try first?"
qv = embed(question)
ranked = sorted(((cos(qv, json.loads(v)), d, s) for d, s, v in db.execute("SELECT day, summary, vec FROM episodes")), reverse=True)
print(f"\nnew session: {question}")
for sim, d, s in ranked:
    print(f"   recall {sim:.2f}  {d}  {s[:70]}")
memory = "\n".join(f"- {d}: {s}" for sim, d, s in ranked[:2] if sim > 0.3)
answer = chat(f"Relevant past episodes with this user:\n{memory}\n\nUser: {question}\nAnswer in 2 sentences, using the history.")
print(f"\nanswer with memory: {answer}")

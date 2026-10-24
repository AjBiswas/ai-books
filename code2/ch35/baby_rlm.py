"""Book 1, Chapter 35 lab: a baby recursive language model (RLM) versus stuffing the context.

A long delivery log (about 9,000 tokens) is far bigger than the 4,096-token window Ollama gives
qwen3:4b by default. Stuffing it in silently cuts off the start. The RLM-style approach keeps the
log in a Python variable, splits it with code, asks the model about each chunk, and combines the
short notes. (A full RLM lets the model write this splitting code itself; here we write it for it.)
Setup:  ollama pull qwen3:4b
Run:    python baby_rlm.py      (about 10 model calls)
"""
import json
import random
import time
import urllib.request

random.seed(4)
cities = ["Pune", "Delhi", "Mumbai", "Chennai", "Indore", "Jaipur"]
lines = []
for i in range(1, 361):
    city = random.choice(cities)
    late = random.random() < 0.08
    lines.append(f"ORD-{1000 + i} | {city} | {'LATE by ' + str(random.randint(2, 6)) + ' days' if late else 'on time'}")
context = "\n".join(lines)                                  # the long input, kept OUTSIDE the prompt
truth = {c: sum(1 for l in lines if f"| {c} |" in l and "LATE" in l) for c in cities}
QUESTION = "How many LATE orders are there for each city?"


def llm_query(text, question):
    body = {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0, "num_predict": 4096},
            "messages": [{"role": "user", "content": f"{text}\n\n{question}"}]}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        d = json.loads(r.read())
    return d["message"]["content"].strip(), d["prompt_eval_count"]


print(f"log: {len(lines)} lines, ~{len(context) // 4:,} tokens; true late counts: {truth}\n")

t0 = time.perf_counter()
ans, read = llm_query(context, QUESTION + " Reply as JSON {city: count}.")
print(f"STUFFED: model actually read {read} tokens (the rest was cut off) in {time.perf_counter() - t0:.0f}s\n   {ans[:200]}\n")

t0 = time.perf_counter()
chunks = [lines[i:i + 40] for i in range(0, len(lines), 40)]    # code does the splitting
notes = []
for n, ch in enumerate(chunks, 1):
    note, _ = llm_query("\n".join(ch), "List ONLY the lines that contain LATE, as 'ORD-id city'. If none, reply NONE.")
    notes.append(note)
late_lines = [l for note in notes for l in note.splitlines() if "ORD-" in l]
final, _ = llm_query("\n".join(late_lines), QUESTION + " Count carefully. Reply as JSON {city: count}.")
print(f"RLM-STYLE: {len(chunks)} chunk calls + 1 combine call in {time.perf_counter() - t0:.0f}s, every call small")
print(f"   late lines found: {len(late_lines)} (true: {sum(truth.values())})")
print(f"   {final[:200]}")

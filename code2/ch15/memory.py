"""Book 1, Chapter 15 lab: long-term memory that survives between sessions.

Session 1: the model extracts durable facts about the user from a chat into a JSON memory file.
Session 2 (a fresh conversation): the memory is loaded into the context and used.
The user then asks to forget one fact, and it is deleted on purpose.
Setup:  ollama pull qwen3:4b
Run:    python memory.py
"""
import json
import pathlib
import re
import tempfile
import urllib.request

MEM = pathlib.Path(tempfile.gettempdir()) / "ch15_memory_asha.json"


def chat(messages):
    body = {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0, "num_predict": 4096}, "messages": messages}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["message"]["content"].strip()


session1 = ("User: Hi, I'm Asha. I'm vegetarian and allergic to peanuts. I live in Pune and usually order on weekends.\n"
            "Assistant: Nice to meet you, Asha! How can I help?\n"
            "User: Just browsing today, it's raining a lot here.")
raw = chat([{"role": "user", "content": "Extract durable facts about the user worth remembering for future orders "
             "(not temporary things like today's weather). Reply with a JSON list of short strings only.\n\n" + session1}])
facts = json.loads(re.search(r"\[.*\]", raw, re.S).group(0))
MEM.write_text(json.dumps(facts, indent=1))
print("session 1 saved to memory:", facts)

memory = json.loads(MEM.read_text())
q = "Suggest a snack I can order for Saturday evening."
ans = chat([{"role": "system", "content": "Known facts about this user:\n- " + "\n- ".join(memory)},
            {"role": "user", "content": q + " One line."}])
print(f"\nsession 2 (new chat) asks: {q}\n   answer: {ans}")

memory = [f for f in memory if "pune" not in f.lower()]
MEM.write_text(json.dumps(memory, indent=1))
print("\nuser: 'please forget where I live' -> memory now:", memory)

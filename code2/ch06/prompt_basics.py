"""Book 1, Chapter 6 lab: a vague prompt versus a clear one, same model, same task.

The clear prompt says who the reader is, what to include, the format, the length and what to do
when information is missing. Compare the two answers.
Setup:  ollama pull qwen3:4b
Run:    python prompt_basics.py
"""
import json
import urllib.request

NOTES = "Meeting 23 Oct: launch moved from 1 Nov to 15 Nov (vendor delay). Priya owns vendor follow-up. Budget unchanged. Next sync 30 Oct."


def ask(prompt):
    body = {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0, "num_predict": 4096},
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["message"]["content"].strip()


vague = f"Write an update about this.\n{NOTES}"
clear = (f"Write a WhatsApp update for the sales team (non-technical) from these meeting notes.\n"
         f"Include: what changed, why, who owns the next step, and the next meeting date.\n"
         f"Format: 3 short bullet points, under 50 words total, no greeting.\n"
         f"If something isn't in the notes, leave it out; don't invent details.\n\nNotes: {NOTES}")
for label, p in (("VAGUE", vague), ("CLEAR", clear)):
    out = ask(p)
    print(f"--- {label} prompt ({len(out.split())} words)\n{out}\n")

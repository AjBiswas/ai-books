"""Book 1, Chapter 20 lab: two agents, a writer and a reviewer, with separate instructions.

The writer drafts a product description. The reviewer checks it against a rule list and replies
APPROVED or a numbered list of problems. The orchestrator loops at most 3 rounds.
Setup:  ollama pull qwen3:4b
Run:    python writer_reviewer.py
"""
import json
import urllib.request

FACTS = "Steel water bottle, 750 ml, keeps drinks cold 24 h and hot 12 h, BPA-free lid, price INR 899, 1-year warranty."
RULES = ("1. Under 60 words. 2. Mentions price and warranty. 3. No claims beyond the facts (no 'best', no medical claims). "
         "4. Ends with a call to action.")


def agent(system, user):
    body = {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0.3, "num_predict": 4096},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["message"]["content"].strip()


WRITER = "You write lively e-commerce product descriptions for Indian shoppers."
REVIEWER = f"You are a strict compliance reviewer. Rules: {RULES} Reply 'APPROVED' or a numbered list of rule violations only."

draft = agent(WRITER, f"Write a product description. Facts: {FACTS}")
for round_ in range(1, 4):
    print(f"--- round {round_} draft ({len(draft.split())} words)\n{draft}")
    verdict = agent(REVIEWER, f"Facts: {FACTS}\n\nDraft:\n{draft}")
    print(f"reviewer: {verdict}\n")
    if verdict.upper().startswith("APPROVED"):
        break
    draft = agent(WRITER, f"Facts: {FACTS}\n\nYour draft:\n{draft}\n\nReviewer feedback:\n{verdict}\n\nRewrite to fix every point. Reply with the description only.")

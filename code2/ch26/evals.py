"""Book 1, Chapter 26 lab: a small eval suite with two kinds of graders.

System under test: a prompt that answers HR questions from a policy.
Graders: (1) exact checks in code (must contain a number, must say "I don't know" when the policy
is silent) and (2) an LLM-as-judge with a written rubric for faithfulness.
Change the prompt, re-run, compare the score: that's regression testing for AI.
Setup:  ollama pull qwen3:4b
Run:    python evals.py
"""
import json
import re
import urllib.request

POLICY = "Leave: 24 paid days per year; up to 8 unused days carry forward. Work from home: up to 2 days a week with manager approval."
CASES = [
    {"q": "How many paid leave days do I get?", "must": "24"},
    {"q": "Can I carry forward 10 unused days?", "must": "8"},
    {"q": "How many WFH days are allowed per week?", "must": "2"},
    {"q": "What is the dress code?", "must": "don't know"},
    {"q": "Is there a gym allowance?", "must": "don't know"},
]
PROMPTS = {
    "v1 (loose)": "Answer the employee's question.",
    "v2 (grounded)": "Answer ONLY from the policy. If the policy doesn't cover it, reply exactly: I don't know.",
}


def chat(system, user):
    body = {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0, "num_predict": 4096},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["message"]["content"].strip()


def judge(q, answer):
    v = chat("You grade answers. Rubric: PASS only if every claim in the answer is supported by the policy, "
             "or the answer says it doesn't know. Otherwise FAIL. Reply PASS or FAIL.",
             f"Policy: {POLICY}\nQuestion: {q}\nAnswer: {answer}")
    return "PASS" in v.upper()


for name, system in PROMPTS.items():
    exact = faithful = 0
    for c in CASES:
        a = chat(f"{system}\nPolicy: {POLICY}", c["q"])
        ok = c["must"].lower() in a.lower().replace("’", "'")
        fj = judge(c["q"], a)
        exact += ok
        faithful += fj
        print(f"   {name:14} {'ok ' if ok else 'BAD'} {'faithful' if fj else 'UNFAITHFUL':10} {c['q'][:38]:38} -> {a[:60]!r}")
    print(f"{name}: exact {exact}/{len(CASES)}, judge-faithful {faithful}/{len(CASES)}\n")

"""Book 1, Chapter 17 lab: an agent loop with stop rules, a step limit and a token budget.

The agent may call two tools (a calculator and an exchange-rate lookup) by replying with JSON.
The harness runs the tools, counts tokens, and stops on: a final answer, the step limit,
or the budget. Every lap is printed so you can watch the loop think.
Setup:  ollama pull qwen3:4b
Run:    python agent_budget.py
"""
import json
import re
import urllib.request

RATES = {"USD": 84.1, "EUR": 91.3, "AED": 22.9}            # INR per unit (made-up snapshot)
TOOLS = {
    "rate": lambda a: RATES.get(a["currency"].upper(), "unknown currency"),
    "calc": lambda a: round(eval(a["expr"], {"__builtins__": {}}), 2) if re.fullmatch(r"[\d\s.+\-*/()]+", a["expr"]) else "bad expression",
}
SYSTEM = ("You are a travel-money agent. Tools: rate(currency) -> INR per unit; calc(expr) -> arithmetic.\n"
          'To use a tool reply ONLY with JSON: {"tool": "rate", "args": {"currency": "USD"}} or {"tool": "calc", "args": {"expr": "2*3"}}.\n'
          'When you know the answer reply ONLY with JSON: {"final": "<answer>"}. One JSON object per reply.')
MAX_STEPS, BUDGET = 6, 20_000


def chat(messages):
    body = {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0, "num_predict": 4096}, "messages": messages}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.loads(r.read())
    return d["message"]["content"].strip(), d["prompt_eval_count"] + d["eval_count"]


task = "I have 250 USD and 400 AED. How many rupees is that in total?"
messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": task}]
spent = 0
print(f"task: {task}")
for step in range(1, MAX_STEPS + 1):
    reply, used = chat(messages)
    spent += used
    try:
        act = json.loads(re.search(r"\{.*\}", reply, re.S).group(0))
    except Exception:
        act = {"error": "not JSON"}
    if "final" in act:
        print(f"step {step}: FINAL -> {act['final']}   (tokens so far {spent:,})")
        break
    if "tool" in act and act["tool"] in TOOLS:
        result = TOOLS[act["tool"]](act.get("args", {}))
        print(f"step {step}: {act['tool']}({act.get('args')}) -> {result}   (tokens so far {spent:,})")
        messages += [{"role": "assistant", "content": reply}, {"role": "user", "content": f"Tool result: {result}"}]
    else:
        print(f"step {step}: unusable reply -> asking again")
        messages += [{"role": "assistant", "content": reply}, {"role": "user", "content": "Reply with exactly one JSON object as instructed."}]
    if spent > BUDGET:
        print(f"STOP: token budget {BUDGET:,} exceeded"); break
else:
    print(f"STOP: step limit {MAX_STEPS} reached")
print(f"check: 250 x 84.1 + 400 x 22.9 = {250 * 84.1 + 400 * 22.9:,.2f}")

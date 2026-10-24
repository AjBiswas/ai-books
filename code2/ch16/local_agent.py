"""Book 2, Chapter 17 lab: a tool-calling agent running fully on your laptop.

The model (qwen3:4b via Ollama) decides which tool to call; Python runs it; we loop.
Run:  python local_agent.py
"""
import json
import time
import urllib.request

ORDERS = {"ORD-100231": {"status": "delivered", "amount_inr": 1499},
          "ORD-100232": {"status": "in transit", "eta": "2 days"}}


def get_order(order_id: str):
    return ORDERS.get(order_id.strip().upper(), {"error": f"no order {order_id}"})


def convert_inr(amount_inr: float, to: str):
    rates = {"USD": 0.012, "EUR": 0.011}
    return {"amount": round(amount_inr * rates.get(to.upper(), 0), 2), "currency": to.upper()}


TOOLS = {"get_order": get_order, "convert_inr": convert_inr}
SPECS = [
    {"type": "function", "function": {"name": "get_order", "description": "Look up an order by ID like ORD-100231",
     "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}}},
    {"type": "function", "function": {"name": "convert_inr", "description": "Convert an INR amount to USD or EUR",
     "parameters": {"type": "object", "properties": {"amount_inr": {"type": "number"}, "to": {"type": "string"}},
                    "required": ["amount_inr", "to"]}}},
]


def chat(messages):
    body = {"model": "qwen3:4b", "stream": False, "think": False, "tools": SPECS,
            "options": {"temperature": 0}, "messages": messages}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["message"]


def run(task, max_steps=6):
    messages = [{"role": "system", "content": "You are a support agent. Use tools for facts. Be brief."},
                {"role": "user", "content": task}]
    t0 = time.perf_counter()
    for step in range(1, max_steps + 1):
        msg = chat(messages)
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            print(f"  step {step}: answer -> {msg['content'].split('</think>')[-1].strip()}")
            break
        for c in calls:
            name, args = c["function"]["name"], c["function"]["arguments"]
            result = TOOLS[name](**args) if name in TOOLS else {"error": "unknown tool"}
            print(f"  step {step}: {name}({json.dumps(args)}) -> {json.dumps(result)}")
            messages.append({"role": "tool", "tool_name": name, "content": json.dumps(result)})
    print(f"  ({time.perf_counter() - t0:.0f}s on this laptop, $0)")


for task in ["Where is my order ORD-100232?",
             "I paid for ORD-100231. How much is that in USD?"]:
    print("Task:", task)
    run(task)

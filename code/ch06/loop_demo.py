"""Chapter 6 lab: the agent loop, step by step, plus the three ways it can go wrong."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness import Agent, AgentConfig, MockProvider, ToolRegistry
from harness.hooks import HookBus
from harness.providers import tool_call

reg = ToolRegistry()


@reg.tool("search_flights", "Find flights", {"type": "object", "properties": {
    "from_city": {"type": "string"}, "to_city": {"type": "string"}, "date": {"type": "string"}},
    "required": ["from_city", "to_city", "date"]})
def search_flights(from_city, to_city, date):
    return [{"flight": "6E-512", "dep": "07:10", "price_inr": 4890}, {"flight": "AI-803", "dep": "09:45", "price_inr": 5620}]


@reg.tool("book_flight", "Book a flight", {"type": "object", "properties": {"flight": {"type": "string"}},
          "required": ["flight"]}, risk="write")
def book_flight(flight):
    return {"pnr": "Q7XK2P", "flight": flight}


def script(system, messages, tools):
    last = messages[-1]
    if last.role == "user":
        return tool_call("search_flights", {"from_city": "Pune", "to_city": "Bengaluru", "date": "2026-10-25"},
                         text="I'll search flights first.")
    if '"pnr"' in last.content:
        return f"Booked! PNR {json.loads(last.content)['pnr']}."
    return tool_call("book_flight", {"flight": "6E-512"}, text="Cheapest is 6E-512. Booking it.")


hooks = HookBus()
hooks.on("post_response", lambda step, response: print(
    f"step {step}: model says {response.text!r}" + (f" -> calls {response.tool_calls[0].name}" if response.tool_calls else "")))
hooks.on("post_tool", lambda call, content, is_error: print(f"        tool {call.name} returned {content[:60]}..."))
r = Agent(MockProvider(script), reg, AgentConfig(model="mock-medium"), hooks=hooks).run("Book the cheapest Pune-Bengaluru flight tomorrow")
print(f"stop={r.stop_reason} steps={r.steps} tokens={r.usage.total} cost=${r.cost_usd:.5f}")

print("\nFailure modes the loop must catch:")
loop = MockProvider(lambda s, m, t: tool_call("search_flights", {"from_city": "Pune", "to_city": "Goa", "date": "x"}))
print("  repeating the same call  ->", Agent(loop, reg, AgentConfig(model="mock-medium")).run("go").stop_reason)
wander = MockProvider(lambda s, m, t: tool_call("search_flights", {"from_city": "Pune", "to_city": f"city{len(m)}", "date": "x"}))
print("  never finishing          ->", Agent(wander, reg, AgentConfig(model="mock-medium", max_steps=5)).run("go").stop_reason)
print("  overspending             ->", Agent(wander, reg, AgentConfig(model="mock-medium", token_budget=400)).run("go").stop_reason)

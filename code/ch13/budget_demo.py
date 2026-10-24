"""Chapter 13 lab: a month of spend against nested budgets, with chargeback."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness.budget import Ledger, TokenBucket

led = Ledger()
led.set_limit("acme", 5000)                    # whole company, USD per month
led.set_limit("acme/banking-client", 2500)
led.set_limit("acme/retail-client", 1500)
led.set_limit("acme/internal-hr", 300)
led.set_limit("acme/internal-hr/chatbot", 120)

rng = random.Random(3)
teams = {"acme/banking-client/kyc-agent": 70, "acme/retail-client/support-bot": 45, "acme/internal-hr/chatbot": 5}
events = []
for day in range(1, 31):
    for path, daily in teams.items():
        spend = daily * rng.uniform(0.6, 1.4)
        chk = led.check(path, spend)
        if not chk.ok:
            events.append(f"day {day:2d}: BLOCK {path} ({chk.scope} limit reached) -> route to cheaper tier / ask owner")
            continue
        if chk.level == "warn" and not any(chk.scope in e and "WARN" in e for e in events):
            events.append(f"day {day:2d}: WARN  {chk.scope} passed 80% of budget")
        led.record(path, spend, int(spend * 150_000))
for e in events[:6]:
    print(e)
print("\nChargeback (month):")
for scope, usd, tokens in led.chargeback(2):
    print(f"  {scope:24s} ${usd:9,.2f}  {tokens/1e6:8.1f}M tokens")

b = TokenBucket(capacity=5, rate=2, now=0)
burst = [b.allow(now=0) for _ in range(8)]
print("\nRate limit, 8 requests at once (burst 5, 2/s):", "".join("Y" if x else "n" for x in burst))

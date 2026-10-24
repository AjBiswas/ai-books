"""Book 1, Chapter 40 lab (part 2): test-driven development with a local coding model.

The human writes the tests first (the spec). The model writes code. We run the tests;
if any fail, the failure output goes back to the model; at most 4 rounds. This loop is
the heart of every coding agent.
Setup:  ollama pull qwen3:4b
Run:    python tdd_loop.py
"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

TESTS = '''
from solution import parse_duration
import pytest

def test_hours_and_minutes():
    assert parse_duration("1h 30m") == 5400

def test_minutes_only():
    assert parse_duration("45m") == 2700

def test_seconds_and_spaces():
    assert parse_duration(" 2h 5s ") == 7205

def test_any_order():
    assert parse_duration("10s 1m") == 70

def test_rejects_garbage():
    with pytest.raises(ValueError):
        parse_duration("soon")

def test_rejects_empty():
    with pytest.raises(ValueError):
        parse_duration("")
'''

SPEC = ("Write a Python module that defines parse_duration(text: str) -> int, returning the number of seconds "
        "in strings like '1h 30m', '45m', '2h 5s'. Units are h, m, s. Raise ValueError for anything else. "
        "Reply with ONLY the code in one ```python block.")


def chat(messages):
    body = {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0.2, "num_predict": 4096}, "messages": messages}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["message"]["content"]


def code_from(reply):
    m = re.search(r"```(?:python)?\n(.*?)```", reply, re.S)
    return (m.group(1) if m else reply).strip()


work = pathlib.Path(tempfile.mkdtemp())
(work / "test_solution.py").write_text(TESTS, encoding="utf-8")
messages = [{"role": "user", "content": SPEC + "\n\nThe tests it must pass:\n" + TESTS}]
for round_ in range(1, 5):
    t0 = time.perf_counter()
    reply = chat(messages)
    (work / "solution.py").write_text(code_from(reply), encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "--tb=line", str(work)], capture_output=True, text=True, cwd=work)
    summary = r.stdout.strip().splitlines()[-1]
    print(f"round {round_}: model {time.perf_counter() - t0:.0f}s -> {summary}")
    if r.returncode == 0:
        print("\nfinal code:\n" + code_from(reply))
        break
    failures = "\n".join(l for l in r.stdout.splitlines() if "Error" in l or "assert" in l)[:1500]
    print("   failures fed back:\n   " + failures.replace("\n", "\n   "))
    messages += [{"role": "assistant", "content": reply},
                 {"role": "user", "content": "These tests failed:\n" + failures + "\nFix the code. Reply with ONLY the full code."}]
else:
    print("gave up after 4 rounds: a human takes over")

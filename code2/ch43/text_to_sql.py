"""Book 1, Chapter 43 lab: text-to-SQL on a real (tiny) database, safely.

Pipeline: schema + a few example rows go in the context -> the model writes ONE SELECT ->
a guard rejects anything that isn't a read-only single SELECT -> run it on a read-only
connection -> if SQLite returns an error, feed it back once for repair -> show rows.
Setup:  ollama pull qwen3:4b
Run:    python text_to_sql.py
"""
import json
import re
import sqlite3
import time
import urllib.request

DB = sqlite3.connect(":memory:")
DB.executescript("""
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, city TEXT);
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(id),
                     amount_inr INTEGER, status TEXT, created_at TEXT);
INSERT INTO customers VALUES (1,'Asha','Pune'),(2,'Ravi','Mumbai'),(3,'Meera','Pune'),(4,'John','Delhi');
INSERT INTO orders VALUES
 (101,1,1899,'delivered','2026-09-02'),(102,1,450,'refunded','2026-09-15'),(103,2,7200,'delivered','2026-09-20'),
 (104,3,999,'delivered','2026-10-01'),(105,3,2500,'cancelled','2026-10-03'),(106,4,3100,'delivered','2026-10-05'),
 (107,2,640,'delivered','2026-10-11'),(108,1,2100,'delivered','2026-10-18');
""")
SCHEMA = "\n".join(r[0] for r in DB.execute("SELECT sql FROM sqlite_master WHERE type='table'"))
SAMPLE = "orders.status is one of: delivered, refunded, cancelled. Dates are 'YYYY-MM-DD' text."


def chat(prompt):
    body = {"model": "qwen3:4b", "stream": False, "think": True,
            "options": {"temperature": 0, "num_predict": 4096}, "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["message"]["content"]


def extract_sql(text):
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip().rstrip(";")


def guard(sql):
    s = sql.strip().lower()
    if not s.startswith(("select", "with")) or ";" in s:
        return "only one read-only SELECT is allowed"
    if re.search(r"\b(insert|update|delete|drop|alter|create|attach|pragma)\b", s):
        return "write or admin keyword found"
    return None


def ask(question):
    prompt = (f"SQLite schema:\n{SCHEMA}\nNotes: {SAMPLE}\n\nWrite ONE SQLite SELECT query that answers: {question}\n"
              "Reply with only the SQL in a ```sql block.")
    t0 = time.perf_counter()
    sql = extract_sql(chat(prompt))
    for attempt in (1, 2):
        problem = guard(sql)
        if problem:
            print(f"   BLOCKED: {problem}: {sql}")
            return
        try:
            rows = DB.execute(sql).fetchall()
            print(f"   SQL ({time.perf_counter() - t0:.0f}s): {' '.join(sql.split())}")
            print(f"   rows: {rows}")
            return
        except sqlite3.Error as e:
            print(f"   error on attempt {attempt}: {e}")
            sql = extract_sql(chat(prompt + f"\n\nYour query:\n{sql}\nfailed with: {e}\nFix it."))


DB.execute("PRAGMA query_only = ON")          # belt and braces: the connection itself is read-only
for q in ["Total delivered revenue per city, highest first",
          "Which customers have more than one delivered order?",
          "How many orders were placed in October 2026?",
          "Delete all cancelled orders"]:
    print(f"Q: {q}")
    ask(q)

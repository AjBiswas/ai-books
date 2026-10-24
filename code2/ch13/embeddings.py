"""Book 1, Chapter 13 lab: embeddings and cosine similarity with a local model.

Uses Ollama's /api/embed. A dedicated embedding model (e.g. `ollama pull nomic-embed-text`
or `bge-m3`) gives better results; this demo uses whatever model you set in MODEL.
Run:  python embeddings.py
"""
import json
import math
import sys
import urllib.request

MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3:4b"


def embed(texts):
    req = urllib.request.Request("http://localhost:11434/api/embed",
                                 data=json.dumps({"model": MODEL, "input": texts}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["embeddings"]


def cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


sentences = [
    "How do I reset my password?",
    "I forgot my login credentials",
    "Mera password bhool gaya, kya karun?",
    "What is the refund policy for damaged items?",
    "The cricket match was exciting yesterday",
]
vecs = embed(sentences)
print(f"model={MODEL}  dimensions={len(vecs[0])}")
q = 0
print(f'query: "{sentences[q]}"')
for i in sorted(range(1, len(sentences)), key=lambda i: -cos(vecs[q], vecs[i])):
    print(f"  {cos(vecs[q], vecs[i]):.3f}  {sentences[i]}")

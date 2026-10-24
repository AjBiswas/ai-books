"""Book 1, Chapter 2 lab: count real tokens, and watch temperature change the answers.

1) The same meaning costs different numbers of tokens in English, Hinglish and Hindi script.
   (Ollama reports how many tokens it read as prompt_eval_count.)
2) The same question at temperature 0 and at 1.2, three times each.
Setup:  ollama pull qwen3:4b
Run:    python tokens_temperature.py
"""
import json
import urllib.request

API = "http://localhost:11434/api"


def post(path, body):
    req = urllib.request.Request(f"{API}/{path}", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())


def count_tokens(text):
    raw = f"<|im_start|>user\n{text}<|im_end|>\n"            # count just the text, no chat template extras
    base = post("generate", {"model": "qwen3:4b", "prompt": "<|im_start|>user\n<|im_end|>\n", "raw": True, "stream": False, "options": {"num_predict": 1}})
    full = post("generate", {"model": "qwen3:4b", "prompt": raw, "raw": True, "stream": False, "options": {"num_predict": 1}})
    return full["prompt_eval_count"] - base["prompt_eval_count"]


print("1) same meaning, different token counts")
for label, text in [("English", "Please book a train ticket from Pune to Mumbai for tomorrow morning."),
                    ("Hinglish", "Kal subah ke liye Pune se Mumbai ka train ticket book kar do."),
                    ("Hindi script", "कृपया कल सुबह के लिए पुणे से मुंबई का ट्रेन टिकट बुक कर दो।")]:
    print(f"   {label:13} {count_tokens(text):3d} tokens   {len(text):3d} characters")

print("\n2) temperature")
for temp in (0.0, 1.2):
    names = []
    for seed in (1, 2, 3):
        out = post("chat", {"model": "qwen3:4b", "stream": False, "think": True,
                            "options": {"temperature": temp, "seed": seed, "num_predict": 4096},
                            "messages": [{"role": "user", "content": "Suggest one name for a chai shop. Reply with the name only."}]})
        names.append(out["message"]["content"].strip().strip('"*'))
    print(f"   temperature {temp}: {names}")

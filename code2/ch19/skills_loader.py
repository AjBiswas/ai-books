"""Book 1, Chapter 19 lab: skills with progressive disclosure.

Three skills live in folders, each with a SKILL.md whose first lines are a short description.
Only the descriptions go into every request. When a task arrives, the model picks a skill, and only
then is that skill's full body loaded. Compare the tokens with "load every skill always".
Setup:  ollama pull qwen3:4b
Run:    python skills_loader.py
"""
import json
import pathlib
import tempfile
import urllib.request

SKILLS = {
    "gst-invoice": ("Check Indian GST invoices for required fields and correct tax maths.",
                    "Required: GSTIN of seller and buyer, invoice number and date, HSN/SAC code, taxable value, "
                    "CGST+SGST (same state) or IGST (different states), total. 18% GST on 1,000 = 180. " * 6),
    "leave-policy": ("Answer questions about Acme's employee leave rules.",
                     "24 paid days a year, 8 carry forward, sick leave needs a note after 2 days, maternity 26 weeks. " * 6),
    "sql-review": ("Review SQL queries for safety and performance.",
                   "Reject writes in read paths, require WHERE on UPDATE/DELETE, prefer indexed columns, avoid SELECT *. " * 6),
}
root = pathlib.Path(tempfile.mkdtemp())
for name, (desc, body) in SKILLS.items():
    (root / name).mkdir()
    (root / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {desc}\n---\n{body}", encoding="utf-8")


def toks(t):
    return len(t) // 4 + 1


def chat(prompt):
    body = {"model": "qwen3:4b", "stream": False, "think": True, "options": {"temperature": 0, "num_predict": 4096},
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["message"]["content"].strip()


catalogue = "\n".join(f"- {p.parent.name}: {p.read_text().split('description: ')[1].splitlines()[0]}" for p in sorted(root.glob("*/SKILL.md")))
everything = "\n\n".join(p.read_text() for p in sorted(root.glob("*/SKILL.md")))
print(f"always-on catalogue: {toks(catalogue)} tokens   vs   every skill in full: {toks(everything)} tokens\n{catalogue}\n")

task = "Is this invoice OK? Seller in Maharashtra, buyer in Karnataka, taxable value 10,000, CGST 900, SGST 900."
pick = chat(f"Skills available:\n{catalogue}\n\nTask: {task}\nWhich skill is needed? Reply with the skill name only.").strip("`'\" ")
print(f"task: {task}\nmodel picks skill: {pick}")
body = (root / pick / "SKILL.md").read_text() if (root / pick / "SKILL.md").exists() else ""
print(f"loaded {pick}/SKILL.md: +{toks(body)} tokens (only now)")
print("answer:", chat(f"Skill instructions:\n{body}\n\nTask: {task}\nAnswer in 2 sentences."))

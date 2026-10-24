"""Build "Becoming an AI Engineer" (Book 1).

Each chapter's content lives in src/chNN.html (opener + article + one <script>).
This script wraps it with the shared head, top bar and prev/next links, and writes index.html.
Run:  python build.py
"""
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

PARTS = [
    ("Part I", "Start here", "Shuruaat"),
    ("Part II", "Talking to models", "Model se baat"),
    ("Part III", "Giving models knowledge", "Model ko gyaan dena"),
    ("Part IV", "Agents", "Agents"),
    ("Part V", "Changing the model itself", "Model ko hi badalna"),
    ("Part VI", "Production", "Production"),
    ("Part VII", "Your career", "Aapka career"),
    ("Part VIII", "Frontier and reference", "Frontier aur reference"),
]

# (num, part index, title en, title hi, subtitle en, subtitle hi)
CHAPTERS = [
    (1, 0, "What an AI Engineer Does", "AI Engineer Kya Karta Hai", "The role, the skills map, and how this book gets you there", "Role, skills ka naksha, aur yeh book wahan kaise pahunchaayegi"),
    (2, 0, "How LLMs Work", "LLM kaise kaam karte hain", "Tokens, next-word guessing, context, temperature", "Tokens, agla word guess karna, context, temperature"),
    (3, 0, "The Model Zoo", "Models ka Chidiyaghar", "Closed vs open models, free vs paid, and which to pick when", "Closed vs open models, free vs paid, aur kab kaunsa chunein"),
    (4, 0, "Models on Your Laptop", "Laptop par Models", "Ollama, LM Studio, llama.cpp, GGUF and what your hardware can run", "Ollama, LM Studio, llama.cpp, GGUF aur aapka hardware kya chala sakta hai"),
    (5, 0, "Your First API Call", "Pehli API Call", "Keys, SDKs, streaming, errors, rate limits and cost", "Keys, SDKs, streaming, errors, rate limits aur kharch"),
    (6, 1, "Prompt Engineering Basics", "Prompt Engineering ki Buniyaad", "Clear instructions, context, examples and format", "Saaf instructions, context, examples aur format"),
    (7, 1, "Advanced Prompting", "Advanced Prompting", "Few-shot, step-by-step, chaining, self-checks, meta-prompting", "Few-shot, step-by-step, chaining, self-checks, meta-prompting"),
    (8, 1, "Structured Outputs", "Structured Outputs", "JSON, schemas and constrained decoding", "JSON, schemas aur constrained decoding"),
    (9, 1, "Reasoning Models", "Sochne Wale Models", "Thinking, effort and when it's worth paying for", "Thinking, effort aur kab iska paisa dena faayde ka hai"),
    (10, 1, "Context Engineering", "Context Engineering", "What goes into the window, in what order, and what stays out", "Window mein kya jaaye, kis order mein, aur kya bahar rahe"),
    (11, 1, "Reverse & Forward Engineering", "Reverse aur Forward Engineering", "Prompt leaks, probing, distillation; and building forward from a spec", "Prompt leaks, probing, distillation; aur spec se aage banana"),
    (12, 1, "Multimodal AI", "Multimodal AI", "Images, documents, voice, and image and video generation", "Images, documents, awaaz, aur image aur video banana"),
    (13, 2, "Embeddings & Vector Databases", "Embeddings aur Vector Databases", "Meaning as numbers, similarity search, vector DBs", "Matlab numbers mein, similarity search, vector DBs"),
    (14, 2, "RAG from Zero to Production", "RAG: Zero se Production", "Chunk, embed, retrieve, rerank, answer, evaluate", "Chunk, embed, retrieve, rerank, jawab, evaluate"),
    (15, 2, "Memory", "Memory", "Short-term, long-term, and forgetting on purpose", "Short-term, long-term, aur jaan-boojh kar bhoolna"),
    (16, 3, "Tool Calling", "Tool Calling", "How a model asks your code to act", "Model aapke code se kaam kaise karwata hai"),
    (17, 3, "Building Agents", "Agents Banana", "The loop, frameworks, and when not to build an agent", "Loop, frameworks, aur kab agent nahi banana"),
    (18, 3, "MCP: The Universal Plug", "MCP: Universal Plug", "What it is, why it exists, life without it, and building a server", "Yeh kya hai, kyun bana, iske bina kya hota, aur server banana"),
    (19, 3, "Skills, Plugins & Sub-agents", "Skills, Plugins aur Sub-agents", "How you “add skills” to a model without retraining it", "Bina retrain kiye model mein “skills” kaise jodte hain"),
    (20, 3, "Multi-Agent Systems & A2A", "Multi-Agent Systems aur A2A", "Teams of agents and how agents talk to other agents", "Agents ki teams aur agents doosre agents se kaise baat karte hain"),
    (21, 3, "Computer-Use & Browser Agents", "Computer-Use aur Browser Agents", "Agents that see the screen and click", "Screen dekhne aur click karne wale agents"),
    (22, 3, "AI Coding Assistants", "AI Coding Assistants", "Claude Code, Cursor, Copilot, Codex; vibe coding vs spec-driven", "Claude Code, Cursor, Copilot, Codex; vibe coding vs spec-driven"),
    (23, 4, "Fine-Tuning", "Fine-Tuning", "When to do it, LoRA and QLoRA, SFT and DPO, datasets", "Kab karein, LoRA aur QLoRA, SFT aur DPO, datasets"),
    (24, 4, "Small Models, Distillation & Quantisation", "Chhote Models, Distillation aur Quantisation", "Making models smaller, cheaper and faster", "Models ko chhota, sasta aur tez banana"),
    (25, 4, "Synthetic Data", "Synthetic Data", "Using models to make training and test data", "Models se training aur test data banana"),
    (26, 5, "Evals", "Evals", "How you know your AI app actually works", "Kaise pata chale ki aapki AI app sach mein chalti hai"),
    (27, 5, "Guardrails & Security", "Guardrails aur Security", "Prompt injection, jailbreaks, PII, output checks", "Prompt injection, jailbreaks, PII, output checks"),
    (28, 5, "LLMOps & Observability", "LLMOps aur Observability", "Versioning prompts, tracing, monitoring, feedback loops", "Prompts ka versioning, tracing, monitoring, feedback loops"),
    (29, 5, "Cost & Speed", "Kharch aur Speed", "Caching, routing, batching, streaming, smaller models", "Caching, routing, batching, streaming, chhote models"),
    (30, 5, "Front-End for AI Apps", "AI Apps ka Front-End", "Streaming UIs, chat UX, generative UI and human-in-the-loop", "Streaming UI, chat UX, generative UI aur human-in-the-loop"),
    (31, 5, "Shipping to Production", "Production mein Bhejna", "Backend architecture, deployment, scaling, reliability", "Backend architecture, deployment, scaling, bharosemandi"),
    (32, 5, "Responsible AI & the Law", "Zimmedaar AI aur Kanoon", "Bias, privacy, copyright, and the rules you must follow", "Bias, privacy, copyright, aur maanne laayak niyam"),
    (33, 6, "The Hot-Topics Radar", "Hot Topics Radar", "Every buzzword of 2026, explained in one line and placed on a map", "2026 ka har buzzword, ek line mein samjha aur naksha par"),
    (34, 6, "Your Roadmap & Portfolio", "Aapka Roadmap aur Portfolio", "A 90-day plan, five portfolio projects, and interviews", "90 din ka plan, paanch portfolio projects, aur interviews"),
    (35, 7, "Research Frontier: Beyond the Plain LLM", "Research Frontier: Saade LLM se Aage", "RLM, NCM, diffusion, state-space and concept models, and how to judge the hype", "RLM, NCM, diffusion, state-space aur concept models, aur hype ko kaise parkhein"),
    (36, 7, "The AI Dictionary", "AI Shabdkosh", "Every term from LLM to NCM in plain words, with a study order", "LLM se NCM tak har shabd aasaan bhasha mein, padhne ke kram ke saath"),
]

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="claude:viewport-fit-sides" content="cover">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&family=JetBrains+Mono:wght@400;500;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap">
<script>(function(){{var r=document.documentElement,t=null;try{{t=localStorage.getItem("harness-book-theme")}}catch(e){{}}r.setAttribute("data-theme",t||(window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"))}})()</script>
<link rel="stylesheet" href="book.css">
</head>
<body>
<div class="page">
<div class="topbar">
  <div class="crumbs"><a href="index.html"><span class="l-en">Contents</span><span class="l-hi">Vishay-suchi</span></a><span>{part} · Chapter {nn}</span></div>
  <div class="langtog" role="group" aria-label="Language"><button type="button" data-setlang="en" aria-pressed="true">English</button><button type="button" data-setlang="hi" aria-pressed="false">Hinglish</button></div>
</div>
"""

OPENER = """<section class="opener col">
  <div class="eyebrow"><span class="l-en">Chapter {nn} · {part_en}</span><span class="l-hi">Chapter {nn} · {part_hi}</span></div>
  <h1><span class="l-en">{t_en}</span><span class="l-hi">{t_hi}</span></h1>
"""


def esc(s):
    return html.escape(s, quote=False)


def build():
    os.makedirs(os.path.join(HERE, "src"), exist_ok=True)
    ready = []
    for num, pi, t_en, t_hi, s_en, s_hi in CHAPTERS:
        src = os.path.join(HERE, "src", f"ch{num:02d}.html")
        if not os.path.exists(src):
            continue
        ready.append(num)
        frag = open(src, encoding="utf-8").read()
        body, script = frag.split("<script>", 1)
        script = "<script>" + script
        prev_ = next((c for c in reversed(CHAPTERS) if c[0] < num and os.path.exists(os.path.join(HERE, "src", f"ch{c[0]:02d}.html"))), None)
        next_ = next((c for c in CHAPTERS if c[0] > num and os.path.exists(os.path.join(HERE, "src", f"ch{c[0]:02d}.html"))), None)
        pager = '<nav class="pager">'
        pager += (f'<a href="ch{prev_[0]:02d}.html">Ch {prev_[0]}</a>' if prev_ else '<a href="index.html"><span class="l-en">Contents</span><span class="l-hi">Vishay-suchi</span></a>')
        pager += (f'<a href="ch{next_[0]:02d}.html"><span class="l-en">Ch {next_[0]} · {esc(next_[2])}</span><span class="l-hi">Ch {next_[0]} · {esc(next_[3])}</span></a>'
                  if next_ else '<a href="index.html"><span class="l-en">Back to contents</span><span class="l-hi">Vishay-suchi par wapas</span></a>')
        pager += "</nav>\n"
        i = body.rfind("</article>")
        body = body[:i] + pager + body[i:]
        part = PARTS[pi]
        page = (HEAD.format(title=f"Ch {num} · {t_en}", part=part[0], nn=f"{num:02d}")
                + OPENER.format(nn=f"{num:02d}", part_en=esc(part[1]), part_hi=esc(part[2]), t_en=esc(t_en), t_hi=esc(t_hi))
                + body + "</div>\n<script src=\"book.js\"></script>\n" + script + "\n</body>\n</html>\n")
        open(os.path.join(HERE, f"ch{num:02d}.html"), "w", encoding="utf-8").write(page)

    # index
    out = [INDEX_TOP]
    for pi, (pn, p_en, p_hi) in enumerate(PARTS):
        out.append(f'<section class="part"><h2><span class="pn">{pn}</span><span class="l-en">{esc(p_en)}</span><span class="l-hi">{esc(p_hi)}</span></h2><ol class="chapters">')
        for num, cpi, t_en, t_hi, s_en, s_hi in CHAPTERS:
            if cpi != pi:
                continue
            inner = (f'<span class="l-en">{esc(t_en)}</span><span class="l-hi">{esc(t_hi)}</span>'
                     f'<span><span class="l-en">{esc(s_en)}</span><span class="l-hi">{esc(s_hi)}</span></span>')
            if num in ready:
                out.append(f'<li><span class="cn">{num:02d}</span><a class="ct" href="ch{num:02d}.html">{inner}</a>'
                           f'<span class="st ready"><span class="l-en">Ready</span><span class="l-hi">Taiyaar</span></span></li>')
            else:
                out.append(f'<li><span class="cn">{num:02d}</span><span class="ct">{inner}</span>'
                           f'<span class="st planned"><span class="l-en">Planned</span><span class="l-hi">Aane wala</span></span></li>')
        out.append("</ol></section>")
    out.append("</div>\n</div>\n<script src=\"book.js\"></script>\n")
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write("\n".join(out))
    print(f"built {len(ready)} chapters: {ready}")


INDEX_TOP = """<title>Becoming an AI Engineer</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&family=JetBrains+Mono:wght@400;500;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap">
<script>(function(){var r=document.documentElement,t=null;try{t=localStorage.getItem("harness-book-theme")}catch(e){}r.setAttribute("data-theme",t||(window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"))})()</script>
<link rel="stylesheet" href="book.css">
<style>
  .cover-grid { display: grid; grid-template-columns: 1fr 11rem; gap: 2rem; align-items: center; }
  .cover-grid svg { width: 11rem; height: auto; }
  @media (max-width: 640px) { .cover-grid { grid-template-columns: 1fr; } .cover-grid svg { width: 7rem; } }
</style>
<div class="page wide">
<div class="topbar">
  <div class="crumbs"><span><span class="l-en">Book 1 · A storybook course</span><span class="l-hi">Book 1 · Kahani wala course</span></span></div>
  <div class="langtog" role="group" aria-label="Language"><button type="button" data-setlang="en" aria-pressed="true">English</button><button type="button" data-setlang="hi" aria-pressed="false">Hinglish</button></div>
</div>
<header class="cover">
  <div class="cover-grid">
    <div>
      <div class="eyebrow"><span class="l-en">With Haron as your mentor · 36 chapters · A to Z</span><span class="l-hi">Haron aapka mentor · 36 chapters · A se Z</span></div>
      <h1><span class="l-en">Becoming an AI Engineer</span><span class="l-hi">AI Engineer Banna</span></h1>
      <p class="lede l-en">Everything an AI engineer works with in 2026, from your first prompt to shipping agents in production: prompting, context engineering, RAG, MCP, skills, agents, fine-tuning, local models on your laptop, evals, security, cost, and the career path. Every idea has a picture, an animation, a simple example, and code you can run.</p>
      <p class="lede l-hi">2026 mein AI engineer jis cheez ke saath kaam karta hai, sab kuch: pehle prompt se lekar production mein agents ship karne tak. Prompting, context engineering, RAG, MCP, skills, agents, fine-tuning, laptop par local models, evals, security, kharch, aur career ka raasta. Har idea ke saath picture, animation, aasaan example aur chalne wala code.</p>
    </div>
    <svg viewBox="0 0 120 140" role="img" aria-label="Haron the robot"><use href="#tokku"/></svg>
  </div>
  <div class="legend">
    <span class="lb"><span class="l-en">AI behaviour</span><span class="l-hi">AI behaviour</span></span>
    <span class="lh"><span class="l-en">Engineer's note</span><span class="l-hi">Engineer ka note</span></span>
    <span class="le"><span class="l-en">In the real world</span><span class="l-hi">Asli duniya mein</span></span>
  </div>
</header>
<div class="parts">
"""

if __name__ == "__main__":
    build()

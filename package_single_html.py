"""Pack BOTH books into ONE self-contained HTML file that opens offline in any browser,
including phones (no sign-in, no server, no extra files).

Everything is inlined: CSS, JS, fonts (as base64), every chapter. Chapters are stored in
<template> tags and shown one at a time by a tiny hash router (#home, #b1-ch05, #b2-index ...).

Run:  python package_single_html.py      ->  AI-Books.html
"""
import base64
import json
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "AI-Books.html")
FONTS_URL = ("https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&"
             "family=JetBrains+Mono:wght@400;500;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;"
             "0,8..60,600;1,8..60,400&display=swap")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def inline_fonts():
    """Download the Google Fonts CSS and embed the latin + latin-ext woff2 files as data URIs."""
    try:
        css = fetch(FONTS_URL).decode()
    except Exception as e:  # offline build: fall back to system fonts
        print("fonts not embedded:", e)
        return ""
    blocks = re.findall(r"/\* ([\w-]+) \*/\s*(@font-face\s*{.*?})", css, re.S)
    out = []
    for subset, block in blocks:
        if subset not in ("latin", "latin-ext"):
            continue
        url = re.search(r"url\((https://[^)]+)\)", block).group(1)
        data = base64.b64encode(fetch(url)).decode()
        out.append(block.replace(url, "data:font/woff2;base64," + data))
    print(f"embedded {len(out)} font files")
    return "\n".join(out)


def read(path):
    return open(path, encoding="utf-8").read()


def rewrite_links(html, book):
    html = re.sub(r'href="(ch\d\d)\.html"', lambda m: f'href="#{book}-{m.group(1)}"', html)
    return html.replace('href="index.html"', f'href="#{book}-index"')


def split_chapter(html):
    """-> (styles, body, script) from a full chapter page."""
    head = html.split("</head>", 1)[0] if "</head>" in html else ""
    styles = "".join(re.findall(r"<style>.*?</style>", head, re.S))
    body = html.split("<body>", 1)[1] if "<body>" in html else html
    body, rest = body.split('<script src="book.js"></script>', 1)
    scripts = re.findall(r"<script>(.*?)</script>", rest, re.S)
    return styles, body.strip(), (scripts[-1] if scripts else "")


def split_index(html):
    """Book index pages are fragments: styles + markup, then <script src="book.js">."""
    styles = "".join(re.findall(r"<style>.*?</style>", html.split('<div class="page', 1)[0], re.S))
    body = '<div class="page' + html.split('<div class="page', 1)[1]
    body = body.split('<script src="book.js"></script>', 1)[0]
    return styles, body.strip(), ""


pages = {}   # id -> (title, html, script)
for folder, key, title in [("book", "b1", "Building the Harness"), ("book2", "b2", "Becoming an AI Engineer")]:
    base = os.path.join(ROOT, folder)
    st, body, _ = split_index(read(os.path.join(base, "index.html")))
    body = body.replace('<div class="crumbs">', '<div class="crumbs"><a href="#home">All books</a>', 1)
    pages[f"{key}-index"] = (title, st + rewrite_links(body, key), "")
    for name in sorted(os.listdir(base)):
        m = re.fullmatch(r"(ch\d\d)\.html", name)
        if not m:
            continue
        full = read(os.path.join(base, name))
        t = re.search(r"<title>(.*?)</title>", full).group(1)
        st, body, script = split_chapter(full)
        pages[f"{key}-{m.group(1)}"] = (t, st + rewrite_links(body, key), script)

HOME = """<div class="page wide">
<header class="cover">
  <div class="eyebrow">Two storybooks · English / Hinglish · animated · works offline</div>
  <h1>AI Books</h1>
  <p class="lede">Pick a book. Everything is inside this one file: open it on a phone or laptop, even without internet.</p>
</header>
<ol class="chapters" style="margin-top:2rem">
  <li><span class="cn">1</span><a class="ct" href="#b2-index">Becoming an AI Engineer<span>34 chapters · from zero to AI engineer, A to Z: prompting, RAG, MCP, agents, local models, production</span></a><span class="st ready">Start here</span></li>
  <li><span class="cn">2</span><a class="ct" href="#b1-index">Building the Harness<span>18 chapters · LLM internals, agent harnesses, enterprise AI platforms</span></a><span class="st ready">Open</span></li>
</ol>
</div>"""
pages["home"] = ("AI Books", HOME, "")

css = read(os.path.join(ROOT, "book2", "book.css"))
js = read(os.path.join(ROOT, "book2", "book.js"))   # superset of the Harness book's runtime
fonts = inline_fonts()

parts = ["""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>AI Books</title>
<script>(function(){var r=document.documentElement,t=null;try{t=localStorage.getItem("harness-book-theme")}catch(e){}r.setAttribute("data-theme",t||(window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"))})()</script>
<style>""", fonts, css, """
:root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
""", read(os.path.join(ROOT, "search.css")), """
</style>
</head>
<body>
<div id="app"></div>
"""]
for pid, (title, html, script) in pages.items():
    parts.append(f'<template id="t-{pid}" data-title="{title}">{html}</template>\n')
    if script.strip():
        parts.append(f'<script type="text/plain" id="s-{pid}">{script}</script>\n')
parts.append("<script>\n" + js + "\n</script>\n")
parts.append("""<script>
(function () {
  var app = document.getElementById("app");
  function route() {
    var hash = (location.hash || "#home").slice(1).split("~");   // #page~n jumps to the nth h2 (search results)
    var id = hash[0], sec = Number(hash[1] || 0);
    var t = document.getElementById("t-" + id);
    if (!t) { id = "home"; t = document.getElementById("t-home"); }
    app.innerHTML = "";
    app.appendChild(t.content.cloneNode(true));
    document.title = t.getAttribute("data-title");
    var lang = window.Book ? window.Book.lang() : "en";
    app.querySelectorAll("[data-setlang]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-setlang") === lang));
    });
    var s = document.getElementById("s-" + id);
    if (s) { try { new Function(s.textContent)(); } catch (e) { console.error(id, e); } }
    var h = sec ? app.querySelectorAll("h2")[sec - 1] : null;
    if (h) h.scrollIntoView(); else window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", route);
  route();
})();
</script>
<script>
""" + read(os.path.join(ROOT, "search.js")) + """
</script>
</body>
</html>
""")
html = "".join(parts)
open(OUT, "w", encoding="utf-8").write(html)
print(f"{OUT}: {len(pages)} pages, {len(html) // 1024} KB")
print(json.dumps(sorted(pages)[:5]) + " ...")

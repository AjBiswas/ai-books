"""Make both books open without Claude sign-in: plain HTML files in one folder + a zip.

Run:  python package_offline.py
Output: dist/  (open dist/index.html)  and  AI-Books-offline.zip
"""
import os
import re
import shutil
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
BOOKS = [("book", "book1"), ("book2", "book2")]

HEAD = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n')


def standalone_index(fragment: str) -> str:
    """The published index pages are fragments (the artifact host adds <html>/<head>).
    Move everything before the first <div class="page"> into <head>."""
    i = fragment.find('<div class="page')
    head, body = fragment[:i], fragment[i:]
    # the Haron sprite <svg> (if present in the head part) belongs in the body
    sprite = re.search(r"<svg width=\"0\".*?</svg>\s*", head, re.S)
    if sprite:
        head = head.replace(sprite.group(0), "")
        body = sprite.group(0) + body
    return HEAD + head.strip() + "\n</head>\n<body>\n" + body.strip() + "\n</body>\n</html>\n"


HOME = HEAD + """<title>AI Books</title>
<link rel="stylesheet" href="book1/book.css">
</head>
<body>
<div class="page wide">
<header class="cover">
  <div class="eyebrow">Two storybooks · English / Hinglish · animated</div>
  <h1>AI Books</h1>
  <p class="lede">Open a book. Everything works offline; only the fonts need internet (without it, system fonts are used).</p>
</header>
<ol class="chapters" style="margin-top:2rem">
  <li><span class="cn">1</span><a class="ct" href="book2/index.html">Becoming an AI Engineer<span>47 chapters · from zero to AI engineer, A to Z: prompting, RAG, MCP, agents, local models, production</span></a><span class="st ready">Start here</span></li>
  <li><span class="cn">2</span><a class="ct" href="book1/index.html">Building the Harness<span>18 chapters · LLM internals, agent harnesses, enterprise AI platforms</span></a><span class="st ready">Open</span></li>
</ol>
</div>
<script src="book1/book.js"></script>
</body>
</html>
"""

if __name__ == "__main__":
    shutil.rmtree(DIST, ignore_errors=True)
    for src, dst in BOOKS:
        out = os.path.join(DIST, dst)
        os.makedirs(out)
        for name in os.listdir(os.path.join(ROOT, src)):
            if name.endswith((".html", ".css", ".js")):
                shutil.copy2(os.path.join(ROOT, src, name), os.path.join(out, name))
                if name.endswith(".html"):
                    p = os.path.join(out, name)
                    t = open(p, encoding="utf-8").read()
                    open(p, "w", encoding="utf-8").write(t.replace('href="../book/', 'href="../book1/'))
        idx = os.path.join(out, "index.html")
        text = open(idx, encoding="utf-8").read()
        if not text.lstrip().lower().startswith("<!doctype"):
            open(idx, "w", encoding="utf-8").write(standalone_index(text))
    open(os.path.join(DIST, "separate-files.html"), "w", encoding="utf-8").write(HOME)
    single = os.path.join(ROOT, "AI-Books.html")          # build it first: python package_single_html.py
    assert os.path.exists(single), "run package_single_html.py first"
    shutil.copy2(single, os.path.join(DIST, "index.html"))

    zpath = os.path.join(ROOT, "AI-Books-offline.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(DIST):
            for f in files:
                full = os.path.join(base, f)
                z.write(full, os.path.join("AI-Books", os.path.relpath(full, DIST)))
    n = sum(len(fs) for _, _, fs in os.walk(DIST))
    print(f"dist/ ready ({n} files) -> open dist/index.html (everything in one file; book1/ and book2/ hold the same pages as separate files)")
    print(f"zip: {zpath} ({os.path.getsize(zpath) // 1024} KB)")

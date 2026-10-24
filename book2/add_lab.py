"""Insert a "For coders" lab block into a Book 1 chapter fragment, just before "What we learned".

Usage (from Python):  add_lab(num, path, title_en, title_hi, code, output, note_en, note_hi)
The output must be the real text printed by the lab; the block is skipped if it's already there.
"""
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = '<div class="scene-title"><span class="sn">✓</span>'


def add_lab(num, path, title_en, title_hi, code, output, note_en="", note_hi=""):
    src = os.path.join(HERE, "src", f"ch{num:02d}.html")
    t = open(src, encoding="utf-8").read()
    if f'<span class="lvl">{path}</span>' in t:
        print(f"ch{num:02d}: lab block already present")
        return
    note = (f'\n  <p class="l-en">{note_en}</p>\n  <p class="l-hi">{note_hi}</p>') if note_en else ""
    block = (f'<details class="deep">\n'
             f'  <summary><span class="l-en">{title_en}</span><span class="l-hi">{title_hi}</span><span class="lvl">{path}</span></summary>\n'
             f'  <div class="inner">\n<pre>{html.escape(code.strip(), quote=False)}</pre>\n'
             f'<pre>$ python {path}\n{html.escape(output.rstrip(), quote=False)}</pre>{note}\n  </div>\n</details>\n\n')
    assert t.count(MARK) == 1, f"ch{num:02d}: expected one 'What we learned' marker"
    open(src, "w", encoding="utf-8", newline="").write(t.replace(MARK, block + MARK))
    print(f"ch{num:02d}: lab block added")

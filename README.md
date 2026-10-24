# AI Books

Two illustrated, animated storybooks about building with AI, in **English and Hinglish** (toggle on every page), with Haron the robot as your guide.

**Read online:** https://ajbiswas.github.io/ai-books/

| Book | What it covers |
|---|---|
| **Building the Harness** (18 chapters) | How LLMs work inside, AI behaviour patterns, building an agent harness, and running an enterprise AI platform with its own rules and token budgets |
| **Becoming an AI Engineer** (34 chapters) | A to Z for new AI engineers: prompting, context engineering, RAG, MCP, skills, agents, local models, fine-tuning, evals, security, cost, production, career |

## Offline

`AI-Books.html` is a single self-contained file (both books, all animations, fonts embedded). Download it and open it in any browser, including on a phone, with no internet.

## Layout

| Path | Contents |
|---|---|
| `index.html`, `AI-Books.html` | The single-file edition (same file) |
| `book/` | Book 1 as separate pages |
| `book2/` | Book 2 as separate pages; `src/` holds chapter sources, `build.py` rebuilds them |
| `code/` | Book 1 labs: a provider-agnostic Python harness (`code/harness/`) with tests (`python -m pytest -q`) |
| `code2/` | Book 2 labs, run against a local Ollama model (`qwen3:4b`, `all-minilm`) |
| `package_single_html.py` | Rebuilds `AI-Books.html` from `book/` and `book2/` |
| `package_offline.py` | Builds a multi-file offline folder and zip in `dist/` |

## Rebuild

```bash
python book2/build.py            # after editing book2/src/*.html
python package_single_html.py    # refresh AI-Books.html
cp AI-Books.html index.html
```

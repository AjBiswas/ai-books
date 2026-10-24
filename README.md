# AI Books

Two illustrated, animated storybooks about building with AI, in **English and Hinglish** (toggle on every page), with Haron the robot as your guide.

**Read online:** https://ajbiswas.github.io/ai-books/

| Book | What it covers |
|---|---|
| **Book 1 · Becoming an AI Engineer** (47 chapters, start here) | A to Z for new AI engineers: prompting, context engineering, RAG, MCP, skills, agents, local models, fine-tuning, evals, security, cost, production, career; research frontier (RLM, NCM), a 119-term dictionary; under the hood (neural nets, transformers, a tiny GPT you train yourself); deep dives (AI-assisted engineering, long-running agents, text-to-SQL, deployment, DSPy, agent identity, watermarks) |
| **Book 2 · Building the Harness** (18 chapters) | How LLMs work inside, AI behaviour patterns, building an agent harness, and running an enterprise AI platform with its own rules and token budgets |

## Offline

`AI-Books.html` is a single self-contained file (both books, all animations, fonts embedded) with topic search, a light/dark switch, chapter quizzes and reading progress (saved in your browser). Download it and open it in any browser, including on a phone, with no internet.

## Layout

| Path | Contents |
|---|---|
| `index.html`, `AI-Books.html` | The single-file edition (same file) |
| `book2/` | Book 1 (AI Engineer) as separate pages; `src/` holds chapter sources, `build.py` rebuilds them |
| `book/` | Book 2 (Harness) as separate pages |
| `code/` | Book 2 labs: a provider-agnostic Python harness (`code/harness/`) with tests (`python -m pytest -q`) |
| `code2/` | Book 1 labs, run against a local Ollama model (`qwen3:4b`, `all-minilm`) |
| `package_single_html.py` | Rebuilds `AI-Books.html` from `book/` and `book2/`, inlining `search.*`, `progress.*` and `quiz.js` |
| `book2/make_dictionary.py` | Generates the dictionary chapter (`book2/src/ch36.html`) from its term lists |
| `package_offline.py` | Builds `dist/` and the zip: `index.html` is the single-file edition, `book1/` and `book2/` the separate pages |

## Rebuild

```bash
python book2/build.py            # after editing book2/src/*.html
python book2/make_dictionary.py   # only after editing the dictionary terms
python package_single_html.py    # refresh AI-Books.html
cp AI-Books.html index.html
python package_offline.py        # refresh dist/ and the zip
```

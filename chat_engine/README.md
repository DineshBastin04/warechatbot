# WAI Warehouse Chatbot

A text-to-SQL RAG chatbot for warehouse/WMS data: ask a question in plain English, get SQL generated, validated, run, and explained — plus chat-driven writes (with confirmation), scheduled monitoring agents, prediction/anomaly dashboards, and multi-tenant workspace management.

This folder is the entire, standalone project — copy it anywhere, follow [SETUP.md](SETUP.md), and it runs. It was originally built on a vendored copy of the [Vanna](https://github.com/vanna-ai/vanna) framework; the app's own code has since been extracted out into this project, keeping only what it actually uses (RAG engine, ChromaDB retrieval, OpenAI/Ollama backends, the Flask app) — see the migration note below.

- **New here?** Start with [SETUP.md](SETUP.md) — install, configure, run, first workspace.
- **Want to know what it does?** See [FEATURES.md](FEATURES.md) — every feature area, grounded in the actual code.

## Project layout

```
main.py                  # entry point — python main.py (run from inside this folder)
requirements.txt         # every dependency the app needs
.env.example              # template for the environment variables SETUP.md walks through
templates/                 # login.html / admin.html / superadmin.html / user.html
engine/                    # the importable package — main.py does `from engine.flask... import`
  base/                     # VannaBase — core RAG logic (prompting, SQL validation, safety checks)
  chromadb/                 # ChromaDB_VectorStore + per-deployment training/config JSON files
  openai/, ollama/          # LLM backend implementations
  flask/                    # the Flask app: routes, auth, frontend assets, admin pages, its own templates/static
```

`engine/` is nested one level below `main.py` deliberately, not flattened alongside it — several of its subfolders (`types/`, `openai/`, `chromadb/`) share a name with a Python stdlib or third-party package, and Python auto-adds a running script's own directory to `sys.path`. If those folders sat directly next to `main.py`, they'd shadow the real `types`/`openai`/`chromadb` modules and crash on startup. Keep this nesting if you ever restructure the app further.

Templates are split across two folders on purpose: `templates/` (this level) holds the auth/dashboard pages (`login.html`, `admin.html`, `superadmin.html`, `user.html`), resolved relative to the working directory main.py runs from; `engine/flask/templates/` holds a separate set (`home.html`, `index*.html`) used elsewhere in the app. Keep both when copying this project.

## What to include when sharing this project

**Include:** this entire folder, as-is — `main.py`, `requirements.txt`, `.env.example`, `README.md`/`SETUP.md`/`FEATURES.md`, `.gitignore`, and every code subfolder. There's nothing outside it you need.

**`.gitignore` already excludes, and you shouldn't hand out manually either:**
- `.env` — holds real API keys and DB credentials
- `admin_store/` — the ChromaDB store backing user accounts, workspaces, DB/LLM connections; holds real password hashes and connection credentials
- `chroma.sqlite3` and any other ChromaDB data folder (e.g. `chroma/`, `chromadb_store/`) — per-workspace RAG data, not just schema
- `venv/`, `venv_py314/` — rebuild locally from `requirements.txt`; a copied venv is large and platform-specific
- `Logs/`, `*.log` — runtime logs

A `git archive`/fresh `git clone` of a pushed branch already gives a clean, shareable copy without any manual filtering, since all of the above is gitignored.

## Migration note: `vanna/` → this project

The original codebase lived under a directory named `vanna/`, which looked like a pip dependency but wasn't one — it was a full vendored copy of the upstream Vanna project, carrying ~20 integration modules this app never used (other vector stores, other LLM providers) alongside the real, customized code. That customized code was copied out as-is into this project, with only the unused modules dropped — no behavior change — and then this whole project was made self-contained (entry point, dependencies, env template, and docs moved inside it) so it stands alone rather than living as a subfolder of a larger, messier checkout. If a `vanna/` directory (or backup copies of it) exists as a sibling outside this folder, it's pre-migration history kept as a rollback reference — nothing in this project depends on it.

Two things surfaced by that move, now fixed:
- The Flask app's `template_folder` was resolved from `os.getcwd()`. That's still how it works (see the templates note above), but making this project standalone meant actually giving it a `templates/` folder to find at that location — it had been silently relying on wherever `main.py` used to be launched from.
- Three separate places in the code (`engine/flask/auth.py`, `engine/flask/__init__.py` ×2) had the ChromaDB client for user accounts/workspaces/connections hardcoded to an absolute path from a previous machine (`D:/Admin-Module/WAI`) — unrelated to this project's actual location, and would have broken entirely for anyone else this was shared with. Repointed all three to a project-relative `admin_store/` folder and copied the real existing data over so nothing was lost.

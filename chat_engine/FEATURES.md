# Features

What this application does, organized by area. File/line references (relative to this project's root) point into `engine/flask/__init__.py` unless noted otherwise, so a developer can jump straight to the implementation.

## 1. Authentication & roles

Two pluggable auth backends (`engine/flask/auth.py`): `NoAuth` (no login) and `BasicAuth`, which is what's actually wired up. Users live in a ChromaDB `users` collection, seeded from three starter accounts — `superadmin`/`admin123`, `admin`/`admin123`, `user1`/`user123` — hashed with plain SHA-256.

> These starter credentials and the hashing scheme are demo-grade. Before sharing or deploying this anywhere real, change the seed passwords and see [SETUP.md](SETUP.md#security-checklist-before-going-live).

Three roles: `superadmin`, `admin`, `user`.
- A plain `user` is pinned to exactly one **workspace** and is rejected at login if that workspace doesn't exist or was deleted.
- `admin`/`superadmin` aren't workspace-restricted and see admin/superadmin dashboards (`/admin`, `/superadmin`) with cross-workspace management tools.
- Route-level enforcement is via `requires_auth` (must be logged in) and `requires_role([...])` (must have one of the given roles) decorators.
- On top of that, a deny-by-default guard (`engine/flask/access_control.py`) runs before every request.
  - Only the login page, static assets, the Teams endpoints (which authenticate themselves) and logout are public.
  - Workspace/LLM/DB configuration, training, SQL testing, user management, debug and agent-control routes are admin-only.
  - Everything else requires a login.
- Plain users get only a workspace's id and name from `/get_workspace` (never its DB password or API key), and can connect only their own workspace.
- `/connect-vanna` always builds the connection from the workspace's saved config.

## 2. Workspaces (multi-tenancy)

Everything — DB connection, LLM choice, training data, agent configs — is scoped to a **workspace** (a UUID-keyed row in a ChromaDB `Workspaces` collection). A new workspace starts empty; an admin walks through DB connection → LLM selection → training data before it's usable by end users.

CRUD: create/update/delete/list workspaces, switch the active workspace per session.

## 3. Chat / RAG core (the main feature)

A user types a question in natural language; the app turns it into SQL, runs it, and returns results.

1. **Language handling** — non-English questions are auto-detected and translated to English before hitting the LLM; original text is preserved for display.
2. **Intent classification** — a cheap keyword heuristic (`classify_intent`) decides read vs. write. This is a UX router only, **not** the security boundary — every write is independently re-validated before execution (see §5).
3. **Read path** — retrieves similar past questions, table docs, and DDL from ChromaDB, builds a prompt, calls the LLM, extracts SQL, then runs two safety checks before returning it: rejects malformed cross-DB literal injection, and rejects any SQL touching a database outside the workspace's configured scope.
4. **Execution** — a separate call actually runs the validated SQL and returns a DataFrame; results can be auto-charted, summarized in natural language, exported to CSV, or used to suggest follow-up questions.
5. Every call logs token usage and cost per user for billing (see §11).

## 4. Dual-database / cross-database queries

A workspace can connect **two** databases — a primary and an optional secondary — not just one.
- If both are on the same SQL Server instance, generated SQL can reference the second DB with plain three-part naming.
- If they're on separate servers, the app auto-syncs a SQL Server **linked server** and requires cross-DB access to go through `OPENQUERY(...)`.
- Generated SQL is scope-checked so it can never silently reach a database outside what the workspace is configured for.

## 5. Chat-driven writes (INSERT / UPDATE / DELETE via chat)

A user can ask the chatbot to *change* data, not just read it — with a confirm-before-execute step, not an unattended auto-write.

1. A write-classified question generates the SQL, validates it against a whitelist, and returns a preview (including an affected-row count) — nothing executes yet.
2. An `admin`/`superadmin` confirms, which re-validates independently (never trusts the client round-trip) and executes in a transaction (commit or full rollback), writing an audit log entry (who, when, what SQL, rows affected, success/failure).
3. Validation requires: exactly one statement, only UPDATE/INSERT/DELETE (DDL/EXEC/GRANT are hard-blocked), every table+column referenced must be on the whitelist, and UPDATE/DELETE must include a `WHERE` clause — no whole-table writes.

**The whitelist is off by default.** It lives at `engine/chromadb/write_whitelist.json` and ships empty (`{}`), meaning no table is writable until an admin explicitly adds one. This is the single control that turns chat-driven writes on for a given table.

## 6. Scheduled background agents

Four always-on jobs (APScheduler), each independently configurable per workspace:

| Agent | Interval | What it does |
|---|---|---|
| **Stock-out agent** | every 30 min | Runs configured "scenario" queries; emails recipients a CSV when rows come back, with a per-scenario cooldown so the same alert doesn't spam. |
| **Data-integrity agent** | every 5 min (global tick) | Same idea for data-quality checks (SELECT-only, hard-enforced); configurable check interval and re-notify cooldown per scenario. |
| **Identify Stuck Device** | every 2 hours | Detects warehouse handheld devices stuck in an error state, and — atomically — relocates any inventory pinned to that device/location and clears the assignment. This performs live writes to the WMS database. |
| **Automated Unpick** | every 2 hours | Detects mismatched "unpick" transactions and reverts them; also available as an on-demand admin action (scan-only, execute, or partial-execute) with its own log viewer. |

Stock-out and data-integrity only need a per-workspace config (recipients, enabled scenarios) plus a working email provider. Stuck-device and unpick additionally need `SCHEDULER_DB_*`/`EXECUTOR_DB_*` environment variables pointing at the WMS database — they log a warning and no-op (never crash startup) if those aren't set.

## 7. Prediction & anomaly dashboards

Two systems exist side by side:

- **Legacy/fixed endpoints** — an earlier generation of hardcoded per-scenario predictions (delivery time, shipment delay, stockout risk, etc.) against fixed SQL and, in places, literal example coefficients rather than real training. Kept for compatibility; not where new work should go.
- **Generic, admin-configurable engine (current)** — served at `/prediction-page` and `/anomaly-page`. An admin defines a named config: a SQL query + an algorithm (`mean`, `standard_deviation`, `linear_regression`, `logistic_regression` for predictions; `z_score`, `isolation_forest`, `dbscan`, or a custom rule/expression for anomalies) + parameters. The LLM can suggest a starting config for a given table so the admin doesn't have to hand-write the SQL. End users view results in a DataTables/Chart.js dashboard.

## 8. LLM backend: OpenAI or Ollama, per workspace

Each workspace independently chooses `openai` or `ollama` as its model backend (not a global setting). For OpenAI, an API key + model name are validated and stored; for Ollama, the app lists locally installed models via the `ollama` CLI. The vector-store/retrieval layer (ChromaDB) is identical either way — only the completion backend swaps in as a mixin (`OpenAI_Chat` or `Ollama`).

## 9. Email notifications

Two providers: plain SMTP (Gmail-tuned defaults) or Outlook via Microsoft Graph (OAuth2 client-credentials). A global kill switch can disable all outbound email regardless of provider. Triggered by the stock-out agent, the data-integrity agent, and a manual "send test alert" admin action — each attaches a CSV of the affected rows. Recipients and which scenarios alert are configured per workspace/agent.

## 10. Training data — how the RAG actually learns your schema

Two layers:

**A. Per-workspace, editable through the app** — question→SQL example pairs, free-text documentation (including PDF/CSV upload), and named reusable parameterized queries ("Vanna functions"). This is what actually populates each workspace's ChromaDB collections used at question time, and is the main lever for improving answer quality on a new deployment.

**B. Deployment-level JSON files** (`engine/chromadb/*.json`) — loaded once at startup, **no admin UI for these today**, hand-edited/deployed as files:
- `glossary.json` — maps business vocabulary to canonical concepts.
- `table_relevance.json` — keyword clusters → the table they indicate, used to narrow what's pulled into the prompt.
- `query_mapping.json` — curated canned query templates per named scenario.
- `domain_mapping.json` — a related term/domain mapping layer.
- `write_whitelist.json` — the write-enablement whitelist from §5.

Several `*_pirtek.json` / `*_remco.json` variants exist alongside the defaults — these appear to be **manually swapped per customer deployment**, not switched at runtime. Treat "customize these four files for the new tenant" as a required manual step in any new deployment, and see [SETUP.md](SETUP.md#per-tenant-training-data).

## 11. Admin & billing

Superadmin routes cover user management (create/update/delete, assign role + workspace), per-user token-usage lookups, and billing rollups/export — every chat call's token count and computed USD cost is logged per user, so cost oversight across workspaces is built in, not bolted on.

## 12. SOP document Q&A

A second, smaller RAG pipeline, separate from the main text-to-SQL knowledge base: upload Standard Operating Procedure documents, list/delete them, and query them conversationally at `/sop-chat`. Useful for "how do I..." process questions that aren't data questions.

## 13. Microsoft Teams integration and voice

`engine/teams/` (Microsoft 365 Agents SDK) exposes the same chat pipeline in Teams. Setup is in [SETUP.md](SETUP.md#microsoft-teams).

- **Bot chat (`/api/messages`).**
  - Every request's Bot Framework JWT is validated.
  - Turns run on a background event loop, so slow queries never hit Teams' timeout.
  - Answers come back as an Adaptive Card: summary, a table of up to 10 rows, and the SQL.
  - Follow-up questions build on the previous answer (`reset` starts over).
  - Scheduling works exactly as in the web chat (`/list`, `/stop <id>`, `/email list`, "email … every Monday"). Chat-channel results are pushed back into the user's Teams chat.
  - Data changes show a confirm card that only admins can execute.
  - Attached audio files are transcribed and answered.
- **Tab (`/teams/tab`).**
  - Teams single sign-on starts a normal WAI session and opens the existing chat UI.
  - Voice uses server speech: the mic records, stops on silence, and sends the audio to `/api/v0/transcribe`. The question is sent automatically and the answer is read aloud via `/api/v0/speak`.
  - The same server speech is used in any browser without built-in speech recognition.
- **Identity.**
  - Teams users are matched to WAI users by the **Teams email** set in User Management. The first match stores their Entra object id.
  - Plain users are served in their assigned workspace, which must have Teams enabled.
  - Several workspaces can have Teams enabled at once.
- **Admin page.** The Teams Configuration page shows setup status, the messaging endpoint and SSO values, and a **Download Teams app package** button.

## 14. Interactive admin wizards

- **Relocation wizard** — a guided two-step tool to manually fix a stuck device/employee/inventory state, the interactive counterpart to the automated Stuck-Device agent.
- **Unpick wizard** — auto-scan → review → execute or partial-execute, with its own log viewer, the interactive counterpart to the automated Unpick agent.

## 15. Developer/ops extras

- Swagger/OpenAPI docs are auto-registered (Flasgger) — check `/apidocs` for a live API reference.
- A debug WebSocket (`/api/v0/log`) streams internal logs to connected clients when the app runs with `debug=True` — a developer tool, not for end users.

## 16. Warehouse Performance Intelligence Agent

An automatic, zero-configuration, read-only agent (`engine/warehouse_perf/`) that runs for **every** workspace on the
existing scheduled-agents scheduler. It discovers usable operational data in the workspace's own warehouse database,
builds same-weekday/equal-elapsed baselines, flags statistically unusual deterioration, drills down to the warehouse,
process and hour where it happened, and produces an executive report — emailed to the workspace's saved Email Config
recipients when a significant deterioration is found. V1 uses internal data only (no weather/traffic).
Three agents share the work: the **Monitor** (what changed, where, when), the **Investigator** (checks staffing, work per
person, exceptions, stock problems, reversals, demand, order size and the data feed in the records for those hours) and
the **Advisor** (ranks the likely causes, lists what was ruled out, and writes specific actions).
Dashboard: *Manage Agents → Warehouse Performance* or `/warehouse-performance`; chat: `/warehouse report`.
Design, methodology, security model and deployment risks: [docs/warehouse_performance_agent.md](docs/warehouse_performance_agent.md).

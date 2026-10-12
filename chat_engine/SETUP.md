# Setup

## Prerequisites

- **Python 3.11+** (the project has been run against both 3.11 and 3.14 during development — either works)
- **ODBC Driver for SQL Server** (e.g. "ODBC Driver 17/18 for SQL Server") installed on the machine — required by `pyodbc` to reach the warehouse database(s)
- Network access to the SQL Server instance(s) you'll connect a workspace to
- An OpenAI API key, and/or a local [Ollama](https://ollama.com) install if you want a local-model workspace instead

## 1. Get the code

Copy this whole folder (it's the entire, self-contained project), or clone the repo and keep this folder's name — `main.py` imports itself as the `chat_engine` package, so the folder needs to stay named `chat_engine` wherever it lives.

You do **not** need (and won't find, since they're gitignored) `venv/`, `chroma.sqlite3`/`chroma/` (real user data), or `Logs/`/`*.log` — see [README.md](README.md#what-to-include-when-sharing-this-project).

## 2. Create a virtual environment

From inside this folder:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs everything the app imports — Flask, ChromaDB, OpenAI's SDK, `pyodbc`, scikit-learn, APScheduler, the Bot Framework connector, etc.

## 4. Configure environment variables

Copy `.env.example` to `.env` and fill in what you need:

```bash
cp .env.example .env
```

| Variable | Required? | Purpose |
|---|---|---|
| `FLASK_SECRET_KEY` | Yes | Signs session cookies. The app refuses to start without it. Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `OPENAI_API_KEY` | Only if any workspace uses OpenAI, or for voice | LLM calls for SQL generation, summaries, follow-ups; speech-to-text and text-to-speech |
| `FEEDBACK_DB_*` | Yes | Backing store for the feedback/email-config feature |
| `HOST` / `PORT` | No | Bind address (default `127.0.0.1:8084`) |
| `MICROSOFT_APP_ID` / `MICROSOFT_APP_PASSWORD` / `MICROSOFT_APP_TENANT_ID` | Only if using Teams | Entra app registration behind the Azure Bot (see [Microsoft Teams](#microsoft-teams)) |
| `PUBLIC_BASE_URL`, `TEAMS_APP_ID`, `TEAMS_TAB_ENABLED`, `TEAMS_SSO_RESOURCE`, `TEAMS_ENABLED` | Only if using Teams | Public HTTPS address, Teams app id, voice tab switch (see [Microsoft Teams](#microsoft-teams)) |
| `OPENAI_STT_MODEL` / `OPENAI_TTS_MODEL` / `OPENAI_TTS_VOICE` | No | Speech models (defaults `gpt-4o-mini-transcribe`, `gpt-4o-mini-tts`, `alloy`) |
| `SCHEDULER_DB_*` | Only if using the Stuck-Device agent | Read-side WMS connection for detecting stuck devices |
| `EXECUTOR_DB_*` | Only if using the Stuck-Device agent | Write-side WMS connection for applying the fix |

Everything marked "only if" is safe to leave blank — those features log a warning and no-op rather than blocking startup. See [FEATURES.md](FEATURES.md#6-scheduled-background-agents) for what each agent needs.

## 5. Run it

From inside this folder (with the venv active):

```bash
python main.py
```

This starts a Waitress server on `http://127.0.0.1:8084` (see the bottom of `main.py` if you need to change host/port). On first run it creates a local ChromaDB store (`chroma.sqlite3` + a data folder) right here in this folder and seeds three starter accounts.

## 6. Log in and change the default credentials

Starter accounts (see [FEATURES.md](FEATURES.md#1-authentication--roles)):

| Username | Password | Role |
|---|---|---|
| `superadmin` | `admin123` | superadmin |
| `admin` | `admin123` | admin |
| `user1` | `user123` | user (workspace `No.2`) |

**Change these before using the app with real data.** They're hardcoded seed values, hashed with plain SHA-256 — fine for local development, not for anything you'd call production. See the [security checklist](#security-checklist-before-going-live) below.

## 7. Set up your first workspace

As `admin` or `superadmin`:

1. **Create a workspace** — gives it a name and a fresh UUID.
2. **Connect a database** — test the connection, then save it (this is "slot A", the primary DB). If you need cross-database queries, repeat for "slot B" — the app will auto-configure a SQL Server linked server between them if they're on different instances.
3. **Choose an LLM backend** — OpenAI (paste/validate an API key) or Ollama (pick from locally installed models).
4. **Activate the workspace** (connect) — this builds the running RAG instance for that workspace from the DB + LLM config.
5. **Add training data** — at minimum, some documentation and a handful of question→SQL example pairs for your actual schema. Answer quality depends entirely on this step; an empty workspace will generate poor SQL.

## Per-tenant training data

Four files under `engine/chromadb/` — `glossary.json`, `table_relevance.json`, `query_mapping.json`, `domain_mapping.json` — are loaded once at process startup and have **no in-app editor**. If you're deploying this for a new customer/tenant with different vocabulary or table naming, review and customize these by hand (see the `*_pirtek.json`/`*_remco.json` variants already in the folder as examples of what a customized set looks like) before going live for that tenant.

## Microsoft Teams

Users can chat with WAI in Teams (typed questions, attached audio recordings), and ask by voice and hear the answers in the **Ask WAI** tab. Scheduled reports and alerts created from Teams are delivered back into Teams. A Teams user is matched to a WAI user by the **Teams email** set in User Management. Plain users get their assigned workspace; admins get the first Teams-enabled workspace and can switch with `workspace <name>`.

You need an Azure subscription in the same Microsoft Entra tenant as your Teams users. No Azure Speech, Azure OpenAI or Graph *application* permissions are required. Speech uses `OPENAI_API_KEY`.

**With your Azure subscription:**
1. **Public HTTPS address.** Teams must reach this server over HTTPS. For testing, use a *persistent* dev tunnel (the hostname becomes part of the sign-in configuration, so it must not change): `devtunnel create wi -a`, `devtunnel port create wi -p 8084`, `devtunnel host wi`. Put the URL in `PUBLIC_BASE_URL`.
2. **Entra app registration** (single tenant). Copy the Application (client) ID into `MICROSOFT_APP_ID` and the Directory (tenant) ID into `MICROSOFT_APP_TENANT_ID`. Create a client secret and put it in `MICROSOFT_APP_PASSWORD` (note its expiry).
3. **Expose an API** on that registration, for the tab's single sign-on:
   1. In the app's manifest, set `api.requestedAccessTokenVersion` to `2`.
   2. Set the Application ID URI to `api://<public host, lowercase>/botid-<client id>`. The server shows the exact value under **Workspace Admin → Teams Configuration**.
   3. Add a scope `access_as_user` (Admins and users).
   4. Add authorized client applications `1fec8e78-bce4-4aaf-ab1b-5451cc387264` (Teams desktop/mobile) and `5e3ce6c0-2b1f-4285-8d4b-75ee78787346` (Teams web).
   5. Under API permissions, add delegated Microsoft Graph `openid`, `profile`, `email`, `offline_access`, `User.Read`.
4. **Azure Bot resource.** Free tier, type **Single Tenant**, using the existing app registration. Set its messaging endpoint to `https://<public host>/api/messages` and add the **Microsoft Teams** channel.
5. **`.env`.** Set `TEAMS_APP_ID` to any new GUID and `TEAMS_TAB_ENABLED=true`, then restart.
6. **In WAI:**
   1. Enable Teams for the workspace under **Workspace Admin → Teams Configuration**.
   2. Set each user's Teams email in User Management.
   3. Click **Download Teams app package**.

**Needs your Teams / Entra admin:**
- Upload the package in the Teams admin center (Manage apps → Upload new app), or allow custom app upload for the test users.
- **Grant admin consent** for the app registration's delegated permissions.

**Limits to know:**
- Teams doesn't let users send native voice messages to bots. In chat, users attach an audio file instead.
- Bot replies in chat are text/cards, not audio. Spoken answers play in the tab.
- On Teams mobile the tab records through Teams' own recorder (tap to stop; no silence auto-stop).

## Security checklist before going live

- [ ] Change (or delete/recreate) the three seed accounts and their passwords
- [ ] Populate `engine/chromadb/write_whitelist.json` deliberately — it ships empty, meaning chat-driven writes are off for every table until you explicitly enable one (see [FEATURES.md](FEATURES.md#5-chat-driven-writes-insert--update--delete-via-chat))
- [ ] Don't commit or hand out `.env`, `admin_store/` (real password hashes, workspace/DB/LLM connection credentials), or `chroma.sqlite3`/other ChromaDB data folders
- [ ] If exposing this outside a trusted network, put it behind HTTPS — the app itself serves plain HTTP via Waitress

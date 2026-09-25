# Fixes plan — findings from live regression testing (2026-09-25)

**All items below are now fixed and live-verified.** This file is kept as a record
of what was found and how it was addressed.

---

## 1. 🔴 Critical — unauthenticated endpoints leak credentials

**Status: Fixed.** Added `@self.requires_auth` to all four routes. Live-verified:
each now returns `302` (redirect to login) with zero auth cookies, and `200` as
before when called with a valid session cookie — no regression for the legitimate
frontend flow.

| Route | Method | Leaked |
|---|---|---|
| `/get_workspaces` | GET | Every workspace's plaintext DB password + plaintext OpenAI API key |
| `/get_workspace/<id>` | GET | Same, plus the secondary (`db_config_b`) DB password |
| `/connect_workspace/<id>` | POST | Let an unauthenticated caller re-point the server's **global** `vn` instance to any workspace's DB/LLM — affected every logged-in user's next request, not just the caller |
| `/api/list_users` | GET | Every user's password hash. `admin` and `superadmin` share an identical hash (same password), and the hashes look like unsalted SHA-256 — crackable via rainbow table if ever leaked |

**Not done (separate, smaller decision, flagged not fixed):** `/get_workspaces` and
`/get_workspace/<id>` still return raw `password`/`api_key` fields to *any
authenticated* user, not just admins. Redacting those for non-admin roles is a
follow-up if wanted — out of scope for this pass, which only closed the
no-auth-at-all hole.

---

## 2. 🟡 `save_feedback` / `get_feedback` — no input validation or error handling

**Status: Fixed** (`save_feedback`, plus `get_feedback` which turned out to have the
identical gap — found while live-verifying this fix and folded in).

`save_feedback` (`engine/flask/__init__.py`) passed `rating` straight into a
parameterized SQL INSERT/UPDATE against `user_feedback.rating`, an `int` column. A
non-numeric `rating` threw an uncaught `pyodbc.DataError` → unhandled 500. Neither
route wrapped its DB calls in `try/except` at all, so *any* DB-layer failure (bad
input, connection drop, etc.) surfaced as a raw, unhandled 500.

**Fix applied:** both routes now validate `workspace_id`/`question_id` are present
and `rating` is int-coercible before querying (clean `400` on failure), and wrap the
connection + query in `try/except/finally` so a DB failure returns a clean JSON
`500` instead of an unhandled exception, with the connection still closed via
`finally`.

**Live-verified:**
- Bad `rating` (`"positive"`) → clean `400` with a clear message (previously an
  unhandled 500).
- Missing `workspace_id`/`question_id` → clean `400`.
- Valid request → still saves/reads correctly (confirmed round-trip before this
  fix, and the validation path after).
- An actual DB connectivity drop (the feedback DB happened to become unreachable
  mid-testing — real, not simulated) → both routes now return a clean JSON `500`
  ("Could not reach the feedback database" / "Could not read feedback") instead of
  Flask's raw unhandled-exception page. This incidentally exercised the exact
  failure path the fix targets.

---

## 3. 🟢 NL "view my schedules" — top-level classifier gap

**Status: Fixed.**

Previously fixed (earlier round): `_handle_schedule_message`'s list-shortcut
recognizes NL phrasing like "list my scheduled questions" (verb+noun test, not just
the literal `/list`) — but only once a message is *already* routed to the
scheduling handler.

The remaining gap: phrasings like "show my schedules" or "what are my scheduled
agents" were classified as `"query"` by the top-level 3-way router
(`classify_message_route` in `engine/base/base.py`) and never reached the schedule
handler at all — they hit RAG instead and returned "Insufficient data for query."

**Fix applied:** extended the `classify_message_route` prompt's "schedule" category
definition to explicitly cover viewing/listing/managing scheduled agents that
already exist, not just creating or timing a new one — kept as a reasoning test
("is this about the delivery/scheduling mechanism itself, not about looking up
data") rather than an enumerated phrase list, consistent with how this prompt was
originally written. Added corresponding illustrative examples.

**Live-verified:**
- "show my schedules" and "what are my scheduled agents" → now classify as
  `"schedule"` (previously `"query"`).
- "list my scheduled questions" → still `"schedule"` (regression).
- Regression pass on the other categories: plain query phrasing, prediction
  phrasing, schedule-creation phrasing, and the ambiguous "send this to me" case
  all still classify correctly.
- Edge case specifically probed for false positives from the broadened wording:
  "show me the scheduled maintenance cost for warehouse PHX1" (a genuine data
  question that happens to contain the word "scheduled") → correctly still
  classifies as `"query"`, confirming the model is reasoning about intent rather
  than keyword-matching on "schedule".

---

## 4. ⚪ Not a bug — `user1` login credential unknown

**Status: No action — informational only.**

`user1` is a real seeded account (`role: user`, `workspace: No.2`) but its actual
password isn't "user123" as assumed from earlier session notes — that login attempt
failed cleanly (re-rendered the login page, no crash). I did not attempt further
password guesses. If `user1`-specific testing is needed, get the real credential
from whoever set it up, or reset it via the superadmin/admin user-management UI.

---

## Status: all fixed, not yet pushed

Items 1–3 applied and live-verified against a real running server with a real DB
(where reachable — the feedback DB and later the main WMS DB both dropped
connectivity mid-testing, unrelated to these fixes; behavior was confirmed correct
in both the reachable and unreachable states). Nothing has been committed or pushed
yet.

# Warehouse Performance Intelligence Agent — V1 (automatic, internal data only)

The agent watches every workspace's own warehouse/WMS SQL Server database. It works out how the warehouse is performing compared with its own history, what changed, where and when it changed, and whether the change needs attention. It writes an executive report and emails it to the workspace's saved recipients when a significant deterioration is found.

**Nothing needs to be configured.** There are no metrics, thresholds, warehouses, baselines, frequencies or recipients to enter. Every workspace, including one created tomorrow, gets the agent automatically.

V1 uses **only the workspace's own database**. There is no weather, traffic, transport or events data; section 11 describes the V2 extension point for those.

---

## 1. Where it plugs in (integration map)

| Existing piece | How the agent uses it |
|---|---|
| `VannaFlaskApp.__init__` (`engine/flask/__init__.py`) | One `create_warehouse_perf(...)` call right after the scheduled-agents scheduler is built. It receives `scheduled_agents_scheduler`, `_send_email` and `load_email_config`. Two short hooks send `/warehouse …` messages from `slash_command_route` / `route_message` to the agent. |
| `scheduled_agents_scheduler` (the existing APScheduler `BackgroundScheduler`) | Holds the agent's jobs. **No second scheduler is created.** Job options match the existing scheduled agents: `max_instances=1`, `coalesce`, `replace_existing`, misfire grace. |
| Workspaces ChromaDB collection | Read fresh on every run, by explicit `workspace_id`: `db_config`, `llm_config` and `email_recipients`. |
| Email Config (`/api/v0/get_workspace_email_config`, `/api/v0/save_workspace_email_config`) | The recipient list. The agent keeps no recipient configuration of its own. |
| `_send_email` / `load_email_config` / `send_email_enabled` | Delivery goes through the app's own SMTP/Graph path and honours the global kill switch. |
| `requires_auth` / `requires_role` | Wrap every new route. The agent also checks per-workspace authorization (`authz.py`). |
| `VannaBase.validate_db_scope` / `validate_openquery_literals` | Reused unchanged inside the read-only SQL policy. |
| Generic anomaly engine (`z_score` in `_run_anomaly_config`) | Its formula and default threshold (\|z\| > 2.0 against sample std) are reproduced; see section 4. The endpoint itself isn't called, because it runs admin-written SQL through the global `vn`. |
| Workspace Manager sidebar (`config.py`) | Adds a "Warehouse Performance" entry and a `<script>` tag for the dashboard. |

**Deliberately not used:**
- The legacy fixed prediction/anomaly endpoints.
- The global `vn` and `ensure_vanna_initialized`.
- `/api/v0/save_agent_config` and `/api/v0/get_agent_config`: this agent has no configuration.
- `/api/v0/run_agent_query` and `/api/v0/test_agent_alert`: these run stock-out scenario SQL through `vn`.
- `/api/v0/scheduled_agents*` / `scheduled_questions/poll`: these manage users' slash-command records. The agent's jobs share the same scheduler but aren't those records, so they don't appear in that list.

**Footprint on existing files:**
- `engine/flask/__init__.py`: +23 lines (import, one init call, two 3-line chat hooks, comments).
- `engine/flask/config.py`: +4 lines (sidebar entry, script tag). The other 3 lines in its diff are an unrelated local `gpt-5.6-*` edit that isn't part of this feature.
- `.env.example`, `FEATURES.md`: documentation.

Everything else is new code in `engine/warehouse_perf/`.

## 2. Modules (`engine/warehouse_perf/`)

| File | Responsibility |
|---|---|
| `discovery.py` | Phase 1. Classifies the workspace catalog into roles and chooses the source tables. Derives the available metrics and gives a reason for every unavailable one. |
| `queries.py` | Builds SQL from structured specs, with every identifier and alias `[bracket]`-quoted. `WorkspaceData` is per-run data access. |
| `db.py` | `ReadOnlyExecutor`: per-query connection, `ApplicationIntent=ReadOnly`, autocommit off, always `ROLLBACK`, timeout and row cap, and the policy re-checked on every call. |
| `sql_policy.py` | Read-only SQL policy: single SELECT/WITH, no writes/DDL/EXEC, table allowlist, window parameters required. |
| `analytics.py` | Phases 2–3. Equal-elapsed cube, comparable-day selection, median baseline, z-score classification, hourly degradation window, trend t-test. |
| `agents.py` | Runs the three agents in order (Monitor → Investigator → Advisor) and records what each did (`result["agents"]`). |
| `analyzer.py` | **Monitor agent.** One cycle: fetch, period, per-metric evaluation, backlog, demand adjustment, freshness, overall result, and the case file (`handoff`) for the Investigator. |
| `investigator.py` | **Investigator agent.** Checks every possible cause the records can show, for the problem warehouse and hours against the same hours on the comparable days. |
| `advisor.py` | **Advisor agent.** Ranks the likely causes from the Investigator's checks, lists what was ruled out or could not be checked, and writes the actions. No database access, no LLM. |
| `drilldown.py` | Phase 4. Metric → warehouse → process → time → category/zone/shift, plus evidence and recommendations. |
| `evidence.py` | Evidence kinds. `InternalEvidence` is used in V1; `ExternalEvidence` / `CorrelationAnalysis` are V2 placeholders. |
| `reporting.py` | Phase 6. The 14-section report (text/HTML/CSV/JSON), narrative guardrails and alert signature. |
| `llm.py` | Per-workspace narrator (OpenAI or Ollama), built from that workspace's `llm_config`. |
| `recipients.py`, `delivery.py` | Phase 7. Resolve saved recipients; deliver one message per recipient with dedupe, retries and audit. |
| `store.py` | Per-workspace JSON files under `admin_store/warehouse_perf/<workspace_id>/`. No new database backend. |
| `service.py` | `run_analysis(workspace_id)`: the single entry point used by every interface. Also the dashboard view and manual send. |
| `jobs.py` | Phase 8. Registers the reconcile job and per-workspace jobs on the existing scheduler. |
| `routes.py`, `dashboard.js` | Dashboard page, dashboard/report API and the executive dashboard UI. |
| `chat.py` | Optional `/warehouse` commands onto the same engine. |
| `synthetic.py` | Synthetic HighJump-style database for tests and the demo. Never used by the running app. |

## 3. How one analysis cycle works

1. **Resolve.** `workspace_id` (the job argument) → a fresh read of that workspace's metadata. If the workspace has no DB configured, the status is `not_configured` and nothing is queried.
2. **Discover** (cached per workspace for 24 h, and invalidated when the server or database changes).
   - Reads `INFORMATION_SCHEMA` with one fixed query (the only query exempt from the table allowlist; `run_catalog` accepts nothing else).
   - Tokenises column names (snake, camel and compound, e.g. `shipdate`) and assigns roles:
     - warehouse id, order id, quantity, activity/process type, status, category, zone, shift
     - timestamps, either generic or stage-specific (created / picked / packed / loaded / dispatched / completed)
   - Planning dates (`required_`, `earliest_`, `due`, `promised`…) and bookkeeping dates (`updated`, `archived`…) are never used as event times.
   - A `<x>_date` + `<x>_time` pair (HighJump `start_tran_date` / `start_tran_time`) becomes one timestamp.
   - Archive, backup, staging, host-interface and similar tables are ignored.
   - The best three candidates per source are probed with a bounded COUNT/MIN/MAX; the one with the most recent rows wins. If even the best has no recent rows, a second probe reports its latest record date.
3. **Metrics that can be derived**, and only those:
   - Activity source: warehouse transactions and units moved.
   - Orders source: orders received, picked, packed, loaded, dispatched and completed.
   - Pending orders (backlog), reconstructed at the same clock time on each comparable day.
   - Order processing time.

   Anything missing gets a specific reason, e.g. "Dispatch performance cannot be analysed because dispatch timestamps are unavailable." It is never shown as 0.

   **Transaction types.** When the activity table has a description column for its type code (HighJump `t_tran_log.description` for `tran_type`):
   - Types are shown by name, e.g. "Picking (bot-pick) (301)", not as bare codes.
   - **Units moved** counts only one outbound stage, so each unit is counted once: picking types, or shipping types if there are no picking types.
   - Internal moves labelled "(Pick)", replenishment, the put half of a pick/put pair, loading, reversals, voids and adjustments are excluded.
   - On the real HighJump snapshot this leaves `301 Picking (bot-pick)` and `309 Picking (WAVESTAGE pick)`.
   - If no pick/ship type can be identified, all types are summed and the report says the result may count a unit more than once.
   - *Warehouse transactions* still counts every type.
4. **Fetch.** One aggregated query per source/stage over the look-back window, grouped by date, hour, warehouse and process. Every query is generated, policy-checked, parameterised and read-only.
5. **Baseline and classify** (section 4).
6. **Demand adjustment.** If orders received is itself unusual today, a volume metric that simply moved with it isn't a performance problem. The metric/orders-received ratio is compared with its own history; if that ratio is normal, the metric is reclassified as normal variation and the raw classification is kept.
7. **Freshness.** If a source table has recorded nothing in the last 3 hours when activity is normally seen then, that source gets a data-feed warning. Its metrics don't trigger automatic email.
8. **Drill down** (section 5), **report**, **store**, and **deliver** if the result is alert-worthy.

## 3a. The three agents: from "what changed" to "why" and "what to do"

One agent doing everything would have to hold detection, investigation and advice at once. The work is split into three agents with one job each and a narrow input, so none of them is overloaded:

| Agent | Job | Receives | Produces |
|---|---|---|---|
| 1. Monitor (`analyzer.py`, `drilldown.py`) | What changed, where and when | The workspace's data | Classified metrics, drill-down, and a **case file** (`result["handoff"]`): measure, warehouse, problem hours, comparable days, plus demand / order-size / backlog / freshness facts for those hours |
| 2. Investigator (`investigator.py`) | Why: check every possible cause in the records | **Only** the case file, the schema model and read-only data access | `result["investigation"]`: one check per possible cause, each *supported*, *ruled out* or *not checked* (with the reason), with numbers |
| 3. Advisor (`advisor.py`) | Which cause is most likely, and what to do | **Only** the case file and the checks (no database) | `result["diagnosis"]`: ranked likely causes with confidence and evidence, actions, ruled-out list, not-checked list |

**Discovery for the Investigator** (same token rules as the rest of discovery; `MODEL_VERSION = 2`, older cached models are re-scanned):
- the activity log's person column (`employee_id`, `user_id`, `operator`…) and item column (`item_number`, `sku`…);
- an exception/error log table (name contains exception/error/alert/incident…, with an event timestamp and an exception type and/or description). On HighJump: `t_exception_log` (`exception_date` + `exception_time`, `tran_type`, `description`, `wh_id`).

**Investigator checks** — problem warehouse, problem hours (from the Monitor's degradation window) vs the same hours on each comparable day; same median baseline and z-score rules as the Monitor; one query per day, so result sets stay small:

| Hypothesis | How it is checked | Supported when |
|---|---|---|
| Staffing | Distinct people recording work per hour, per activity type (`COUNT(DISTINCT employee_id)`) and overall | Below normal variation |
| Work per person | Activity per person-hour, per activity type | Below normal variation |
| Stock / location | Activity types whose description says short pick / denial / adjustment / not available (e.g. *Short Pick Close*, *Full Floor Denial*), and exception types of that kind; the items involved are listed | Above normal and ≥ 3 events and ≥ 2 more than normal |
| Rework | Reversal types (unpick, unload, cancel, void…) | Same as stock |
| Exceptions | Each exception type in the exception log | Same as stock |
| Demand | Orders received in the problem hours (Monitor fact) | Below normal |
| Order size | Units per order picked in the problem hours (Monitor fact) | Above normal and ≥ 15 % bigger |
| Data feed | Freshness warning (Monitor fact) | No records in recent hours |

Activity types examined: those whose volume fell outside normal variation (up to 4, largest shortfall first), or the 3 biggest when none fell. A check whose data does not exist (no person column, no exception log, an exception log with no recent rows, no reversal types) is **not checked**, with that reason — never "ruled out".

**Advisor reasoning** (deterministic):
- A volume decline in an activity type is split into *fewer people* and *less per person* (log shares). Fewer people → a staffing cause ("put N more people on the X step"; warehouses running normally are named as possible lenders).
- Less per person needs an explanation: exception / stock / rework spikes are attached to the slowdown they name (e.g. *Short Pick Close* → Pick), otherwise to the biggest slowdown in those hours. With no explanation it is reported as a slowdown with no recorded reason.
- Fewer orders received, bigger orders and a stopped data feed are causes on their own.
- Impact = share of the warehouse's activity shortfall the cause accounts for; confidence High / Medium / Low from impact and how far outside normal its evidence is. Up to 3 likely causes, ranked by impact.
- Statuses: `cause_found`; `narrowed_down` (the biggest part has no recorded reason — said first and plainly); `no_internal_cause` ("the cause is probably something the system does not record … the team will know"); `investigation_failed`.
- Wording is always "likely cause": a strong pattern in the warehouse's own records for the same hours, to be confirmed by the team — not proof. Causes the database cannot see (unlogged equipment faults, trucks, power) are named as such.

**Failure isolation:** an Investigator query failure makes that check *not checked* (status `partial`); an Advisor failure leaves the Monitor's report intact. The email still goes out.

**Example** (synthetic test data and the SQL test scenario): "Most likely cause: 'Label printer communication error' exceptions slowing the Shipping step in LAK1; also not enough people on the Picking (pick) step in LAK1. Checked and normal: bigger orders than usual, fewer orders coming in, stock and location problems, warehouse system not recording."

## 4. Baseline and significance methodology (fixed; not configurable)

**Equal elapsed window.**
- Today 00:00 up to the last complete hour is compared with the same hours on comparable days.
- Before 02:00, or when timestamps turn out to be date-only, the previous complete operating day is analysed instead.

**Comparable days.**
- First choice: the same weekday in each of the previous 5 weeks, operating days only.
- Otherwise: up to 10 recent operating days within 21 days.
- Fewer than 3 comparable days gives `insufficient_data` with "No historical baseline is available yet. At least 3 comparable periods are required (found N)." No baseline value is shown in that case.
- An operating day is one on which the source recorded any activity, so closed days never drag the baseline to zero.

**Deviation.**
- Baseline = median of the comparables.
- abs diff = actual − baseline; % diff = abs diff / baseline.
- z = (actual − mean) / sample std, the same statistic and \|z\| > 2 default as the app's generic `z_score` engine.

**Classification** (direction-aware: lower is better for backlog and processing time):

| Classification | Rule |
|---|---|
| `significant_deterioration` | Adverse and \|z\| ≥ 3 |
| `deterioration` | Adverse and 2 ≤ \|z\| < 3 |
| `improvement` | Favourable and \|z\| ≥ 2 |
| `normal_variation` | \|z\| < 2, or \|% diff\| < 5% (materiality guard) |
| `insufficient_data` | Fewer than 3 comparables |
| `above_normal` / `below_normal` | Orders received only; demand is context, not performance |
| History with zero variation | Classified on relative change and labelled as such |

**Also computed:**
- Previous-operating-day comparison.
- A 14-day trend (least-squares slope; "rising" or "falling" only when \|t\| ≥ 2).
- Overall performance = median of the direction-signed % changes; its classification is the most severe individual metric.

## 5. Drill-down, evidence and reports

- **Headline metric.** The most severe classification, then the most negative z. Throughput and process metrics outrank their knock-on effects (backlog, processing time) at equal severity.
- **Warehouse.** Each warehouse's share of the total shortfall. It is "concentrated" when one warehouse has ≥ 50%.
- **Process within that warehouse.** Order stages (picking / packing / loading / dispatch), or the values of the activity-type column.
- **Time.** The earliest hour of the sustained adverse run (≥ 1 hourly std below its hourly baseline; one gap hour tolerated), and whether it is still ongoing.
- **Secondary dimensions** (category / zone / shift): queried only when there is a deterioration to explain.
- **Conclusion.** The Monitor never states a cause. Example: "The available warehouse data shows a significant dispatch decline concentrated in warehouse WH-B, beginning around 09:00. These performance measures show what changed, where and when - not why; the possible causes are checked separately against the warehouse records." (Causes: section 3a.)
- **Evidence labels.** Every statement is labelled *Observed fact*, *Calculated comparison*, *Detected anomaly*, *Inferred interpretation* or *Unknown / insufficient evidence*. Cross-metric context (lower orders received, rising backlog) is always an interpretation.
- **Report sections.**
  1. Executive summary
  2. Current performance
  3. Historical baseline
  4. Major deviations
  5. Warehouse comparison
  6. Process comparison
  7. Time of degradation
  8. Pending/backlog impact
  9. Evidence-based internal findings
  10. Data limitations
  11. Recommended areas for investigation
  12. Root-cause investigation (every check: found / ruled out / not checked, and the tables/columns read)
  13. Likely causes and recommended actions
  14. How the agents worked

  Formats: text, HTML (escaped, with a strict CSP), Word, CSV and JSON. The management part of the email, Word report and Full report leads with **Why it happened** (cause cards with evidence) and **What to do now**, then the charts, then **Checked and ruled out** and **What we don't know yet**.
- **LLM.** The workspace's own LLM writes only the executive summary of *what changed*, and only from the structured facts; it never sees raw rows or SQL. The summary is accepted only if every number already appears in those facts and it states no cause, external factor or URL. Otherwise the deterministic summary is used and the report says so. The Advisor's one-line diagnosis (deterministic) is appended to whichever summary is used.

## 6. Dashboard, chat and delivery

**Dashboard** (*Workspace Manager → Manage Agents → Warehouse Performance*, or `/warehouse-performance?workspace_id=…`). Users see their own workspace; admins see any they're allowed to.
- Header: status, last analysis and next analysis times.
- KPI cards: units moved, orders dispatched, pending orders, overall. Only KPIs the database can supply are shown.
- "What changed?", "Where is the problem?".
- "Why it happened — and what to do": the three agents and their status, the ranked likely causes with evidence, the actions, what was ruled out and what could not be checked.
- The executive finding.
- Actions: Run analysis now, Full report, Download CSV / Download Word, and (admin only) Re-scan database. Emailing is automatic (no button). The page refreshes itself within a minute when a scheduled analysis finishes, and shows *Last email sent* (when and to whom).
- Automatic reporting status and the data the agent found.

**Chat (optional):**
- `/warehouse report` — the latest finding.
- `/warehouse run` — start an analysis now.
- `/warehouse send`, then `/warehouse send confirm <report id>` (admin).

**Automatic email** (dashboard → *Email settings*, admin only):
- **Who:** tick which of the workspace's saved recipients receive the report. *Add a recipient* (name + email) saves it into the workspace's existing Email Config and ticks it; the agent stores only which labels it uses (`settings.json`), never addresses. Until an admin saves a choice, every saved recipient receives it.
- **When:** *Only when a significant problem is found* (default: the automatic runs email once per problem per day, at most 3 a day; a recipient added later still gets the current problem) or *After every analysis* (every completed run's report, about hourly, problems included, no daily limit).
- **Run analysis now / `/warehouse run`:** a run a person asked for always emails the report when it finds a significant problem (not blocked by, and not counted towards, the daily limit). The next automatic run does not email the same problem again.
- Sent automatically by any run — hourly schedule, Run analysis now, Re-scan database or chat. No button is needed.
- Addresses are resolved label → address at send time from the workspace's Email Config. Duplicate labels and invalid addresses are skipped and recorded. With nobody selected, the report is still generated and the dashboard says why it wasn't sent.
- `/warehouse send` (admin, in chat) sends the latest report to the same recipients by hand.
- **What the email looks like** (`exec_report.py`, `charts.py`; preview: `docs/examples/warehouse_perf_email_preview.png`): a management version in plain English. It has a status banner (Needs attention / Watch closely / All normal) with a one-line headline; "In short" bullets covering what, where, when, and whether it's demand or throughput; four KPI tiles (today vs normal); and three charts, drawn as PNGs with Pillow and embedded inline (*When did it start?*, *Where is the problem?*, *Which step is affected?*, or one overview chart on a normal day). It ends with "What we recommend" and "What we don't know yet". The full report as a **Word document** (management summary with charts, then the 11 technical sections) and the data (CSV) are attached; the dashboard offers the same Word file (*Download Word*) and CSV. The dashboard's *Full report* page opens with the same management view.
- Sending uses the app's own `_send_email`, which gained optional `html`, `inline_images` and `extra_attachments` arguments (SMTP: multipart/related with Content-ID images; Microsoft Graph: HTML body with inline attachments). Existing callers are unchanged.

## 7. Isolation and security

- Each job's only input is its `workspace_id`. Each run resolves that workspace, uses a `WorkspaceData` bound to it, and writes only `admin_store/warehouse_perf/<workspace_id>/` (the id is validated before use in a path).
- Nothing is cached across workspaces; the schema cache is per workspace and tied to its DB fingerprint.
- A test (`test_isolation.test_package_never_uses_the_global_vn_or_active_workspace`) asserts the package never references `vn`, `ensure_vanna_initialized`, the session or the "current workspace".
- Every run is wrapped: a failure is recorded against that workspace and returned, never raised into the scheduler. Per-workspace thread and file locks prevent overlapping runs.
- **Read-only:**
  - Generated SQL only; the policy is re-checked at execution.
  - Bound time parameters; bracket-quoted identifiers.
  - `ApplicationIntent=ReadOnly`, autocommit off, unconditional rollback, per-query timeout and a row cap (a truncated result is marked, not analysed).
  - No tables are created and nothing is written to the warehouse database.
- No new API returns DB credentials, API keys, email secrets or full addresses (addresses are masked). Errors are scrubbed before storage or logging.
- There is no configuration API.

## 8. Observability

Every run logs one line:

```
warehouse_perf run workspace=<id> trigger=scheduled status=ok duration=4.68s db=ok discovered=9 calculated=9
  unavailable=1 anomalies=orders_dispatched report=<id> recipients=1 email=sent failure=-
```

The run record (start/end, DB status, per-query status/rows/duration/SQL hash, metrics discovered/calculated/unavailable, anomalies, report, recipients, email outcome, failure reason) is kept in `runs.json` (last 200). The delivery audit is kept in `deliveries.json`. No passwords, keys, connection strings or full addresses are logged.

## 9. Deployment defaults (environment only — nothing is required)

| Variable | Default | Meaning |
|---|---|---|
| `WPA_ENABLED` | `1` | `0` removes the feature: no routes, no jobs. |
| `WPA_INTERVAL_MINUTES` | `60` | Analysis frequency per workspace (15–1440). |
| `WPA_TIMEZONE` | `SCHEDULE_DEFAULT_TIMEZONE` (Asia/Kolkata) | Local time of the warehouse timestamps. |
| `WPA_AUTO_EMAIL` | `1` | `0` = generate reports but never auto-email. |
| `WPA_MAX_AUTO_EMAILS_PER_DAY` | `3` | Per workspace. |
| `WPA_RECIPIENT_LABELS` | unset (= all saved) | Optionally limit to these saved Email Config labels. |
| `WPA_LOOKBACK_DAYS` | `35` | History read per cycle. |
| `WPA_QUERY_TIMEOUT_SECONDS`, `WPA_ROW_LIMIT` | `30`, `50000` | Per query. |
| `WPA_CATALOG_TTL_HOURS` | `24` | Schema re-scan interval. |
| `WPA_STORE_DIR` | `admin_store/warehouse_perf` | Results store. |
| `WPA_ODBC_DRIVER` | `ODBC Driver 17 for SQL Server` | |
| `WPA_ANALYSIS_AS_OF` | unset | **Testing only.** Analyse as if the local time were this ISO datetime (for database snapshots). The dashboard shows a "Test mode" banner. |

**Rollout:**
1. Deploy and restart. Each workspace gets its first analysis about 2 minutes after start-up, staggered 45 s apart.
2. Open the dashboard and check "Data the agent found".
3. Make sure Email Config has the right recipients before a significant deterioration occurs.

## 10. Tests (`tests/warehouse_perf/`, 187 tests; the three agents: `test_agents.py`)

```bash
cd chat_engine && env\Scripts\python.exe -m unittest discover -s tests -t . -p "test_*.py"
```

| Required test | Where |
|---|---|
| 1 Workspace isolation | `test_isolation.py` |
| 2 Baseline calculation | `test_analytics.py` (Comparables, EqualElapsedWindow), `test_analysis_pipeline.py` |
| 3 Percentage deviation | `test_analytics.py` (Classification) |
| 4 Historical comparison | `test_analytics.py`, `test_analysis_pipeline.py` (DegradedWarehouse) |
| 5 Warehouse comparison | `test_analysis_pipeline.py::test_warehouse_comparison_isolates_the_degraded_warehouse` |
| 6 Process drill-down | `test_analysis_pipeline.py::test_process_drill_down_points_at_dispatch` |
| 7 Insufficient data | `test_analysis_pipeline.py` (InsufficientData), `test_analytics.py` |
| 8 Missing columns | `test_discovery.py` (MissingColumns), `test_analysis_pipeline.py` (MissingColumnsEndToEnd) |
| 9 Read-only SQL | `test_sql_readonly.py` |
| 10 Recipient resolution | `test_recipients_delivery.py` (Resolution) |
| 11 No-recipient behaviour | `test_recipients_delivery.py` (NoRecipients) |
| 12 Report generation | `test_reporting.py` |
| 13 Scheduler, multiple workspaces | `test_scheduler.py` (Scheduling) |
| 14 Failure isolation | `test_scheduler.py` (FailureIsolation) |

All tests use synthetic data (`synthetic.py`). Every query the fake answers is first rendered by the real SQL builder and passed through the real read-only policy. `python -m engine.warehouse_perf.synthetic --out docs/examples` regenerates the demo report (clearly labelled SYNTHETIC).

**Verified against a real SQL Server** (this repository's local workspace, a HighJump snapshot: 583 tables, 9,037 columns; automatic email off):
- Discovery chose `dbo.t_tran_log` (`start_tran_date`+`start_tran_time`, `wh_id`, `tran_qty`, `tran_type`) and `dbo.t_order` (`order_date`, `date_picked`, `actual_ship_date`). It correctly reported pack/load timestamps as unavailable.
- With the real clock, it correctly reported "no records in the last 35 days" (latest records 2026-06-05 and 2025-08-13).
- With `WPA_ANALYSIS_AS_OF=2023-10-26T16:00` it computed 7 metrics with 0 failed queries, and the workspace's LLM summary passed validation.
- The real run found and fixed one bug the fake couldn't: `proc` is a T-SQL reserved word. All aliases are now bracket-quoted, with a regression test.

## 11. V2 extension point

`evidence.py` defines `ExternalEvidenceProvider.collect(workspace, analysis_result) -> ExternalEvidence` and the empty `EXTERNAL_PROVIDERS` list. The analyzer already writes `evidence.external` (always `[]` in V1) and `evidence.correlation` (`None`). A V2 weather/traffic/carrier provider plugs in there without changes to discovery, baselines or drill-down. The report guardrails would then need to allow external factors, labelled as hypotheses.

## 12. Known limitations and unresolved deployment risks

1. **Heuristic discovery.** Tables and columns are chosen by name and type. An unusual schema may be missed or mis-mapped. Check "Data the agent found" on the dashboard after rollout, and use *Re-scan database* after schema changes. There is no override UI (by design).
2. **Shared login.** The agent uses the workspace's own DB login. Every safeguard is in the application (policy, read-only intent, rollback). A database-side read-only login for the workspace would be stronger, but it's shared with chat-driven writes, so it's an operational decision.
3. **Query load.** About 10–15 aggregated queries per workspace per hour over 35 days. On very large transaction tables, check query plans and indexes on the timestamp columns. The timeout and row cap bound the damage, not the cost.
4. **Single process.** Locks are in-process plus a lock file on local disk. With several app servers sharing a store, use one scheduler host.
5. **Local time.** Timestamps are assumed to be the warehouse's local time in one time zone per deployment (`WPA_TIMEZONE`). Multi-time-zone tenants on one server are not modelled.
6. **Order counts** are distinct per hour and summed; an order hitting a stage in two hours counts twice. Backlog is reconstructed from timestamps over a 30-day window, so cancelled orders without a completion timestamp count as pending.
7. **Primary database only.** A workspace's secondary database isn't analysed in V1.
8. **Email delivery.** It depends on the app's existing provider configuration. In this environment Outlook `client_secret` is empty, so every agent's email currently fails until it's configured.
9. **Authenticated UI not browser-tested.** The dashboard was exercised through the API test client and a JS syntax check, not clicked through in a logged-in browser session.
10. **Pre-existing app issues** found during the work (not changed):
    - `/save_workspace`, `/delete_workspace`, `/get_prediction_configs` and `/save_prediction_config` have no login check.
    - `ensure_vanna_initialized` logs secrets.
    - `model_check.py` (repo root) contains a plaintext API key.

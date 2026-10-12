# Warehouse Performance Agent — test scenarios

Script: `wpa_test_data_insert.sql`. Set `DECLARE @scenario int = N;` at the top, run it, then click
**Run analysis now**. Remove the data with `wpa_test_data_cleanup.sql` before the next scenario.

Every scenario writes the same 5 weeks of normal history for two warehouses (ATH1 ~20 orders/hour,
LAK1 ~15 orders/hour, 06:00–19:59, Monday–Saturday). Only **today** differs. Run it after 13:00 on a
Monday–Saturday so several hours of "today" exist after the problem starts.

The "Agents reported" column is what the real three agents produced on these exact rows (replayed
2026-10-07 at 14:18 against a rolled-back copy, nothing written). ✅ = the agent gets it right;
⚠ = the scenario exposes a gap in the agent (listed at the end).

| # | Scenario | What happens today | Agents reported | |
|---|---|---|---|---|
| 0 | Normal day | nothing goes wrong | **All normal** — "All 7 measures are within normal ups and downs." No alert. | ✅ |
| 1 | Two problems | LAK1 from 09:00: picker WPATSTLP4 absent, label printer fails for a third of shipments | **Needs attention** — orders shipped −17%, LAK1, from 09:00. #1 'Label printer communication error' slowing Shipping (High, ~71%); #2 not enough people on Picking (Medium, ~29%) | ✅ |
| 2 | Staff shortage | LAK1 from 09:00: 2 of the 4 pickers absent | **Needs attention** — units picked −13%, LAK1, from 09:00. #1 not enough people on Picking (High, ~58%); #2 Shipping slower per person, no recorded reason (~42%) | ✅ ⚠A |
| 3 | Printer failure | LAK1 from 09:00: label printer fails for half the shipments, each logged | **Needs attention** — orders shipped −16%. #1 'Label printer communication error' slowing Shipping (High, ~100%); staffing ruled out | ✅ |
| 4 | Stock shortage | LAK1 from 09:00: a third of orders hit an empty location (short picks, 3 items) | **Needs attention** — units picked −9%. #1 stock problems (Short Pick Close: 31, normally 0) slowing Picking (High, ~61%); #2 Shipping slower per person (~39%) | ✅ ⚠A |
| 5 | Low demand | LAK1 from 09:00: 40% fewer orders come in | **Better than normal** — "All 7 measures are within normal ups and downs." The drop in incoming orders is not mentioned | ⚠B |
| 6 | Slow shipping | LAK1 from 09:00: same people, half the shipments 2.5 h late, nothing logged | **Needs attention** — average time to ship +13%, from 11:00 (3 h 09 min vs 2 h 03 min). "No cause was found in the warehouse records… the LAK1 team will know." | ✅ |
| 7 | System stopped recording | both warehouses from 11:00: no picks or shipments recorded | **Needs attention** — orders shipped −49%; freshness warning "No activity recorded in dbo.t_tran_log since 11:00". #1 the warehouse system stopped recording (High, ~100%) | ✅ ⚠F |
| 8 | Bigger orders | LAK1 from 09:00: orders 8–10 units instead of 2–4, a third not picked yet | **Needs attention** — orders picked −9%. Units per order 9.5 (normally 2.9) found, but ranked #3; #1 is "Picking slower per person, no recorded reason" | ⚠C |
| 9 | Rework | LAK1 from 09:00: a third of shipments reversed (unshipped) | **Needs attention** — orders shipped −11%. #1 work being undone: Unship (reversal) — 27, normally 0 (Medium, ~15%) | ✅ ⚠G |
| 10 | Short stoppage | both warehouses 10:00–12:00: all work stops, then catches up | **Needs attention** — average time to ship +29%, window reported as 12:00–13:00, "no cause found". The 10:00–12:00 stop itself is not identified | ⚠D |
| 11 | Busy day | LAK1 from 09:00: 45% more orders, all handled | **Needs attention** — orders waiting to ship +21% in LAK1. Orders received +36% is listed but "no cause was found" | ⚠E |

## Gaps the scenarios expose (agent improvements to make)

- **A — knock-on effects (2, 4).** When picking is short, shipping has less to ship. The Advisor lists
  "Shipping slower per person, no recorded reason" as a separate cause instead of saying it follows
  from the picking problem.
- **B — falling demand is invisible (5).** 40% fewer incoming orders is not reported. Orders received is
  treated as a neutral measure, and the day is labelled "Better than normal" while the headline says
  "all within the normal range".
- **C — bigger orders not linked to slower picking (8).** The order-size check finds orders 3x bigger,
  but the Advisor does not use it to explain the slower picking per person, so it ranks third.
- **D — a stoppage that recovers is missed (10).** The problem-window search lands on the catch-up hour
  (12:00–13:00) instead of the two hours with no activity.
- **E — rising demand not named as the reason (11).** The Investigator only tests "fewer orders coming
  in"; a backlog caused by 36% more orders gets "no cause found".
- **F — duplicate causes when nothing is recorded (7).** Next to "system stopped recording" it also lists
  "not enough people on Picking / Shipping", which are the same missing records.
- **G — rework share too low (9).** The reversals are the whole cause, but the Advisor credits them with
  only ~15% of the drop.

## Running all scenarios automatically, one every 15 minutes

Use a separate test database, never ISN_db.

1. **Test database:** select it in SSMS and run `wpa_test_db_setup.sql`. That adds empty `t_order`,
   `t_tran_log` and `t_exception_log` tables. It refuses to run in ISN_db or a system database.
2. **Workspace:** in the app's Workspace Manager, connect a workspace to that database.
3. **Analysis every 15 minutes:** add `WPA_INTERVAL_MINUTES=15` to `chat_engine/.env` and restart the app.
   The app then analyses every workspace every 15 minutes, with the dashboard's normal email rules.
4. **Start the runner:**

   ```
   cd chat_engine
   env\Scripts\python.exe docs\examples\wpa_scenario_runner.py --workspace <workspace id> --database <test db name> --scenarios 0-11
   ```

   For each scenario it loads the data, waits for the app's next analysis (about 15 minutes), then logs
   what the agents concluded beside what was expected. Results are printed and appended to
   `Logs/wpa_scenario_runs.jsonl`. When the pass ends it removes the test data.

   The runner only writes to the database named with `--database`, and refuses ISN_db. It reads the
   app's run history but never changes the app.

**Email:** with the normal rules, an automatic analysis emails a problem only once a day, at most
3 per day. So not every alerting scenario sends an email. To get one for every scenario, set the
dashboard's email option to "every run" for that workspace.

## Checking the data yourself

`wpa_test_check_queries.sql` has read-only queries (orders per hour, picks per person, exceptions,
short picks) to confirm what a scenario wrote.

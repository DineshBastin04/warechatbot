"""
Warehouse Performance Agent - scenario runner.

Loads the test scenarios from wpa_test_data_insert.sql into a TEST database one after another.
The running app analyses them itself: with WPA_INTERVAL_MINUTES=15 in the app's .env it runs the
agent every 15 minutes, with the dashboard's normal email rules. After loading a scenario the runner
waits for the app's next completed analysis of that workspace, records what the agents concluded next
to what the scenario expects, then loads the next scenario. When the pass is over it removes the
test data.

It only writes to the database named with --database and refuses ISN_db (create the test database
with wpa_test_db_setup.sql and add a workspace for it in the app first). It reads the app's run history
but never imports or changes the app.

    cd chat_engine
    env\\Scripts\\python.exe docs\\examples\\wpa_scenario_runner.py --workspace <workspace id> \\
        --database WPA_TestDB --scenarios 0-11

Results: printed, and appended to Logs/wpa_scenario_runs.jsonl.
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

HERE = os.path.join(ROOT, "docs", "examples")
INSERT_SQL = os.path.join(HERE, "wpa_test_data_insert.sql")
CLEANUP_SQL = os.path.join(HERE, "wpa_test_data_cleanup.sql")
LOG = os.path.join(ROOT, "Logs", "wpa_scenario_runs.jsonl")
PROTECTED = {"isn_db"}          # never load test scenarios here

EXPECTED = {
    0: "All normal - no alert",
    1: "Label printer exceptions (#1) and short of pickers (#2) in LAK1 from 09:00",
    2: "Not enough people on Picking in LAK1 from 09:00",
    3: "Label printer exceptions slowing Shipping in LAK1 from 09:00",
    4: "Short picks (stock) slowing Picking in LAK1 from 09:00",
    5: "Fewer orders coming in to LAK1 from 09:00 (not a warehouse fault)",
    6: "Shipping slower in LAK1, no recorded cause",
    7: "Warehouse system stopped recording at 11:00 (both warehouses)",
    8: "Bigger orders than usual in LAK1 from 09:00",
    9: "Work being undone (unships) in LAK1 from 09:00",
    10: "Work stopped 10:00-12:00 in both warehouses",
    11: "More orders than usual in LAK1 from 09:00 - handled, backlog up",
}


def parse_scenarios(text):
    out = []
    for part in text.split(","):
        a, _, b = part.strip().partition("-")
        out += list(range(int(a), int(b) + 1)) if b else [int(a)]
    bad = [n for n in out if n not in EXPECTED]
    if bad:
        raise SystemExit(f"unknown scenario(s): {bad}")
    return out


def run_sql_file(conn, sql):
    """Runs a whole script (one batch) and returns the last result set as a list of dicts."""
    cur = conn.cursor()
    cur.execute(sql)
    last = []
    while True:
        if cur.description:
            cols = [d[0] for d in cur.description]
            last = [dict(zip(cols, r)) for r in cur.fetchall()]
        if not cur.nextset():
            break
    return last


def wait_for_run(store, workspace_id, after_iso, timeout_s, poll_s=20):
    """The app's first SUCCESSFUL analysis of this workspace that started after `after_iso`. A failed run
    (e.g. the database was unreachable) does not count - the scenario waits for the next one."""
    deadline = time.time() + timeout_s
    seen_failed = None
    while time.time() < deadline:
        for rec in store.list_runs(workspace_id, limit=5) or []:
            if (rec.get("started_at") or "")[:19] <= after_iso:
                continue
            if rec.get("status") == "ok":
                return rec, seen_failed
            seen_failed = rec
        time.sleep(poll_s)
    return None, seen_failed


def connect(ctx, expected_db, give_up_s, protected):
    """A fresh connection to the test database, waiting (up to give_up_s) while the server is unreachable."""
    import pyodbc
    from engine.warehouse_perf.db import build_connection_string
    deadline, delay, last = time.time() + give_up_s, 30, None
    while True:
        try:
            conn = pyodbc.connect(build_connection_string(ctx.db_config), autocommit=True, timeout=30)
            db = conn.cursor().execute("SELECT DB_NAME()").fetchone()[0]
            if db.lower() != expected_db.lower() or db.lower() in protected:
                conn.close()
                raise SystemExit(f"workspace connects to {db}, not {expected_db} - stopping")
            return conn, db
        except pyodbc.Error as exc:
            last = exc
            if time.time() >= deadline:
                raise RuntimeError(f"database unreachable for {give_up_s / 60:.0f} minutes: {last}") from exc
            print(f"   [{datetime.now():%H:%M}] database unreachable - retrying in {delay}s", flush=True)
            time.sleep(delay)
            delay = min(delay * 2, 300)


def summarise(store, workspace_id, rec):
    out = {"run_started": rec.get("started_at"), "trigger": rec.get("trigger"), "status": rec.get("status"),
           "email_status": rec.get("email_status"), "failure_reason": rec.get("failure_reason")}
    if not rec.get("report_id"):
        return out
    r = (store.get_report(workspace_id, rec["report_id"]) or {}).get("result") or {}
    dd = r.get("drilldown") or {}
    d = r.get("diagnosis") or {}
    out.update({"overall": (r.get("overall") or {}).get("classification"),
                "conclusion": dd.get("conclusion"),
                "diagnosis": d.get("status"), "summary": d.get("summary"),
                "causes": [f"#{c['rank']} {c['title']} ({c['confidence']}, ~{c['explains_pct']}%)"
                           for c in d.get("likely_causes") or []]})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", required=True, help="workspace id that connects to the test database")
    ap.add_argument("--database", required=True, help="name of the test database (safety check)")
    ap.add_argument("--scenarios", default="0-11", help="e.g. 0-11 or 2,5,8")
    ap.add_argument("--wait", type=float, default=35, help="minutes to wait for the app's analysis per scenario")
    ap.add_argument("--db-wait", type=float, default=120,
                    help="minutes to keep retrying while the database server is unreachable")
    ap.add_argument("--attempts", type=int, default=3, help="tries per scenario before moving on")
    ap.add_argument("--keep-data", action="store_true", help="leave the last scenario's data in place")
    args = ap.parse_args()

    if args.database.strip().lower() in PROTECTED:
        raise SystemExit(f"refusing to load test scenarios into {args.database}")
    import chromadb
    from engine.warehouse_perf.store import WarehousePerfStore
    from engine.warehouse_perf.workspace_context import WorkspaceResolver

    store = WarehousePerfStore(os.environ.get("WPA_STORE_DIR") or os.path.join("admin_store", "warehouse_perf"))
    ctx = WorkspaceResolver(chromadb.PersistentClient(path="admin_store").get_collection("Workspaces")).get(
        args.workspace)
    if ctx is None:
        raise SystemExit(f"workspace {args.workspace} not found")
    conn, db = connect(ctx, args.database.strip(), args.db_wait * 60, PROTECTED)
    conn.close()

    insert = open(INSERT_SQL, encoding="utf-8").read()
    # The app analyses complete hours only, some minutes after the data is loaded: write each scenario up
    # to the top of the next hour, so the hours it analyses are complete (rows after "now" are never read).
    insert = re.sub(r"DECLARE @now\s+datetime\s*=\s*GETDATE\(\);",
                    "DECLARE @now datetime = DATEADD(hour, DATEDIFF(hour, 0, GETDATE()) + 1, 0);", insert, count=1)
    if "DATEDIFF(hour, 0, GETDATE()) + 1" not in insert:
        raise SystemExit("could not set @now in wpa_test_data_insert.sql")
    cleanup = open(CLEANUP_SQL, encoding="utf-8").read()
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    scenarios = parse_scenarios(args.scenarios)
    print(f"{len(scenarios)} scenarios into {db} (workspace {args.workspace}); each waits for the app's next "
          f"successful analysis", flush=True)
    try:
        for n in scenarios:
            for attempt in range(1, args.attempts + 1):
                row = {"scenario": n, "expected": EXPECTED[n], "database": db, "attempt": attempt}
                retry = False
                try:
                    conn, db = connect(ctx, args.database.strip(), args.db_wait * 60, PROTECTED)
                    try:
                        run_sql_file(conn, cleanup)
                        sql = re.sub(r"DECLARE @scenario int\s*=\s*\d+;", f"DECLARE @scenario int = {n};", insert,
                                     count=1)
                        row["created"] = [{k: (str(v) if isinstance(v, datetime) else v) for k, v in r.items()}
                                          for r in run_sql_file(conn, sql)]
                    finally:
                        conn.close()
                    loaded = datetime.now().isoformat(timespec="seconds")
                    row["loaded_at"] = loaded
                    print(f"\n[{loaded}] scenario {n} loaded - expected: {EXPECTED[n]}", flush=True)
                    rec, failed = wait_for_run(store, args.workspace, loaded, args.wait * 60)
                    if rec is not None:
                        row.update(summarise(store, args.workspace, rec))
                    else:
                        retry = True
                        row["error"] = (f"no successful analysis within {args.wait:g} minutes"
                                        + (f" (last run: {failed.get('status')} - {failed.get('failure_reason')})"
                                           if failed else " - is the app running?"))
                except SystemExit:
                    raise
                except Exception as exc:  # noqa: BLE001 - log it, then retry this scenario
                    retry = True
                    row["error"] = f"{type(exc).__name__}: {exc}"
                with open(LOG, "a", encoding="utf-8") as f:
                    f.write(json.dumps(row, default=str) + "\n")
                for k in ("error", "run_started", "overall", "conclusion", "summary", "email_status"):
                    if row.get(k):
                        print(f"   {k}: {row[k]}", flush=True)
                for c in row.get("causes") or []:
                    print(f"   {c}", flush=True)
                if not retry:
                    break
                if attempt < args.attempts:
                    print(f"   retrying scenario {n}", flush=True)
    finally:
        if not args.keep_data:
            try:
                conn, _ = connect(ctx, args.database.strip(), args.db_wait * 60, PROTECTED)
                run_sql_file(conn, cleanup)
                conn.close()
                print("\ntest data removed", flush=True)
            except Exception as exc:  # noqa: BLE001
                print(f"\ncould not remove the test data ({exc}) - run wpa_test_data_cleanup.sql in {db}", flush=True)


if __name__ == "__main__":
    main()

"""
SYNTHETIC test/demo data — never used by the running application.

Builds an in-memory, HighJump-style warehouse database (t_tran_log with split
start_tran_date / start_tran_time columns and per-warehouse teams of employees,
t_order with stage timestamps, t_exception_log, plus noise tables the discovery
must ignore) and a data-access object with
the same interface as queries.WorkspaceData. Every query spec it answers is
first rendered to SQL by queries.build_sql and checked by the real read-only
policy (sql_policy.validate_select_sql), so tests exercise the generated SQL
too; results are then computed with pandas using the same semantics.

Demo:  python -m engine.warehouse_perf.synthetic --out docs/examples
"""
import argparse
import json
import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from .queries import FetchResult, build_sql, normalize_frame
from .sql_policy import SqlPolicyError, validate_select_sql

SYNTHETIC_BANNER = "SYNTHETIC DATA — generated for testing/demo, not real warehouse activity."
WAREHOUSES = {"WH-A": 400, "WH-B": 320, "WH-C": 250}
WEEKDAY_FACTOR = {0: 1.1, 1: 1.0, 2: 1.0, 3: 1.05, 4: 1.1, 5: 0.6, 6: 0.0}   # Sunday closed
CATEGORIES = ["Bulk", "Parcel", "Cold"]
ROUTINE_EXCEPTIONS = [("101", "Putaway Location Override"), ("351", "LP Weight Override"), ("301", "Damage Report")]
LABEL_ERROR = ("317", "Label Printer Communication Error")
SHORT_PICK = ("376", "Short Pick Close")

TABLE_TYPES = {
    "dbo.t_tran_log": {"tran_log_id": "int", "tran_type": ("nvarchar", 10), "description": ("nvarchar", 60),
                       "start_tran_date": "datetime", "start_tran_time": "datetime", "wh_id": ("nvarchar", 10),
                       "item_number": ("nvarchar", 30), "tran_qty": "int", "employee_id": ("nvarchar", 20),
                       "location_id": ("nvarchar", 30)},
    "dbo.t_order": {"order_number": ("nvarchar", 30), "wh_id": ("nvarchar", 10), "order_date": "datetime",
                    "picked_date": "datetime", "packed_date": "datetime", "loaded_date": "datetime",
                    "ship_date": "datetime", "required_ship_date": "datetime", "status": ("nvarchar", 10),
                    "order_category": ("nvarchar", 20), "customer_name": ("nvarchar", 80)},
    "dbo.t_order_detail": {"order_number": ("nvarchar", 30), "line_number": "int", "item_number": ("nvarchar", 30),
                           "qty": "int", "wh_id": ("nvarchar", 10)},
    "dbo.t_item_master": {"item_number": ("nvarchar", 30), "description": ("nvarchar", 60), "unit_weight": "float",
                          "last_updated": "datetime"},
    "dbo.t_tran_log_archive": {"tran_log_id": "int", "tran_type": ("nvarchar", 10), "start_tran_date": "datetime",
                               "wh_id": ("nvarchar", 10), "tran_qty": "int"},
    "dbo.t_exception_log": {"tran_type": ("nvarchar", 5), "description": ("nvarchar", 100),
                            "exception_date": "datetime", "exception_time": "datetime",
                            "employee_id": ("nvarchar", 10), "wh_id": ("nvarchar", 10),
                            "location_id": ("nvarchar", 50), "item_number": ("nvarchar", 30), "quantity": "float",
                            "control_number": ("nvarchar", 30)},
}


def team_size(base):
    """People per activity type in a warehouse (each records many transactions an hour)."""
    return max(2, round(base / 80))


def _split(ts):
    return datetime.combine(ts.date(), datetime.min.time()), datetime(1900, 1, 1, ts.hour, ts.minute, ts.second)


def generate_tables(now, days=42, seed=7, degrade=True, degrade_wh="WH-B", degrade_from_hour=9,
                    load_skip=0.25, ship_skip=0.35, warehouses=None, cause="mixed"):
    """Returns {"dbo.t_order": df, "dbo.t_tran_log": df, ...}. `now` is naive local time;
    nothing is generated after `now`. The degradation (if any) hits `degrade_wh` today
    from `degrade_from_hour`: some packed orders are not loaded, some loaded not shipped.

    cause (what is behind the degradation, visible to the Investigator):
      "mixed" — one of the warehouse's loaders is missing (the loads that do happen are
                done by one person fewer), and every shipment that does not happen
                logs a "Label Printer Communication Error" exception;
      "none"  — the same decline with the full team and no exceptions (nothing in the
                records explains it).
    Every warehouse also has routine exceptions and short picks every day, so those
    checks have a normal level to compare with."""
    rng = np.random.default_rng(seed)
    rng2 = np.random.default_rng(seed + 1000)    # people/exceptions: never disturbs the order stream above
    exceptions = []
    whs = warehouses or WAREHOUSES
    today = now.date()
    orders, trans = [], []
    hours = np.arange(6, 21)
    weights = np.exp(-((hours - 12.5) ** 2) / 18.0)
    weights /= weights.sum()
    oid = 0
    for back in range(days, -1, -1):
        d = today - timedelta(days=back)
        wf = WEEKDAY_FACTOR[d.weekday()]
        if wf == 0:
            continue
        for wh, base in whs.items():
            n = max(0, int(rng.normal(base * wf, base * wf * 0.04)))
            created_h = np.repeat(hours, np.round(weights * n).astype(int))   # stratified: no hourly sampling noise
            n = len(created_h)
            created_m = rng.integers(0, 60, size=n)
            for i in range(n):
                t0 = datetime.combine(d, datetime.min.time()) + timedelta(hours=int(created_h[i]),
                                                                          minutes=int(created_m[i]))
                if t0 > now:
                    continue
                oid += 1
                num = f"SO{oid:07d}"
                picked = t0 + timedelta(minutes=float(rng.gamma(4, 10)))
                packed = picked + timedelta(minutes=float(rng.gamma(3, 7)))
                loaded = packed + timedelta(minutes=float(rng.gamma(3, 10)))
                shipped = loaded + timedelta(minutes=float(rng.gamma(2, 10)))
                degraded = degrade and wh == degrade_wh and d == today
                cut = datetime.combine(d, datetime.min.time()) + timedelta(hours=degrade_from_hour)
                if degraded:
                    if packed >= cut and rng.random() < load_skip:
                        loaded = shipped = None
                    elif loaded is not None and loaded >= cut and rng.random() < ship_skip:
                        if cause == "mixed" and shipped <= now:
                            dd_, tt_ = _split(shipped)
                            exceptions.append({"tran_type": LABEL_ERROR[0], "description": LABEL_ERROR[1],
                                               "exception_date": dd_, "exception_time": tt_,
                                               "employee_id": f"{wh[-1]}204-0", "wh_id": wh,
                                               "location_id": "SHIPDOCK", "item_number": None, "quantity": 0.0,
                                               "control_number": num})
                        shipped = None
                stamps = {"picked": picked, "packed": packed, "loaded": loaded, "shipped": shipped}
                stamps = {k: (v if v is not None and v <= now else None) for k, v in stamps.items()}
                if stamps["picked"] is None:
                    stamps = {k: None for k in stamps}
                elif stamps["packed"] is None:
                    stamps.update(loaded=None, shipped=None)
                elif stamps["loaded"] is None:
                    stamps["shipped"] = None
                status = ("SHIPPED" if stamps["shipped"] else "LOADED" if stamps["loaded"] else
                          "PACKED" if stamps["packed"] else "PICKED" if stamps["picked"] else "RELEASED")
                orders.append({"order_number": num, "wh_id": wh, "order_date": t0, "picked_date": stamps["picked"],
                               "packed_date": stamps["packed"], "loaded_date": stamps["loaded"],
                               "ship_date": stamps["shipped"], "required_ship_date": t0 + timedelta(days=2),
                               "status": status, "order_category": CATEGORIES[oid % 3],
                               "customer_name": f"Customer {oid % 50}"})
                qty = int(rng.integers(1, 9))
                team = team_size(base)
                for code, desc, ts in (("201", "Pick", stamps["picked"]), ("202", "Pack", stamps["packed"]),
                                       ("203", "Load", stamps["loaded"]), ("204", "Ship", stamps["shipped"])):
                    if ts is None:
                        continue
                    size = team - 1 if (degraded and cause == "mixed" and code == "203" and ts >= cut) else team
                    trans.append({"tran_log_id": len(trans) + 1, "tran_type": code, "description": desc,
                                  "start_tran_date": datetime.combine(ts.date(), datetime.min.time()),
                                  "start_tran_time": datetime(1900, 1, 1, ts.hour, ts.minute, ts.second),
                                  "wh_id": wh, "item_number": f"ITEM{oid % 200:04d}", "tran_qty": qty,
                                  "employee_id": f"{wh[-1]}{code}-{oid % size}", "location_id": f"LOC{oid % 90:03d}"})
            # routine exceptions and short picks: a normal level for the Investigator to compare with
            day0 = datetime.combine(d, datetime.min.time())
            for _ in range(int(rng2.poisson(2.0))):
                t = day0 + timedelta(hours=int(rng2.integers(6, 21)), minutes=int(rng2.integers(0, 60)))
                if t <= now:
                    code, desc = ROUTINE_EXCEPTIONS[int(rng2.integers(0, len(ROUTINE_EXCEPTIONS)))]
                    dd_, tt_ = _split(t)
                    exceptions.append({"tran_type": code, "description": desc, "exception_date": dd_,
                                       "exception_time": tt_, "employee_id": f"{wh[-1]}201-0", "wh_id": wh,
                                       "location_id": f"LOC{int(rng2.integers(0, 90)):03d}",
                                       "item_number": f"ITEM{int(rng2.integers(0, 200)):04d}", "quantity": 1.0,
                                       "control_number": None})
            for _ in range(int(rng2.poisson(1.0))):
                t = day0 + timedelta(hours=int(rng2.integers(6, 21)), minutes=int(rng2.integers(0, 60)))
                if t <= now:
                    dd_, tt_ = _split(t)
                    trans.append({"tran_log_id": len(trans) + 1, "tran_type": SHORT_PICK[0],
                                  "description": SHORT_PICK[1], "start_tran_date": dd_, "start_tran_time": tt_,
                                  "wh_id": wh, "item_number": f"ITEM{int(rng2.integers(0, 200)):04d}", "tran_qty": 0,
                                  "employee_id": f"{wh[-1]}201-0", "location_id": f"LOC{int(rng2.integers(0, 90)):03d}"})
    order_df = pd.DataFrame(orders)
    tran_df = pd.DataFrame(trans)
    for c in ("order_date", "picked_date", "packed_date", "loaded_date", "ship_date", "required_ship_date"):
        order_df[c] = pd.to_datetime(order_df[c])
    for c in ("start_tran_date", "start_tran_time"):
        tran_df[c] = pd.to_datetime(tran_df[c])
    exc_df = pd.DataFrame(exceptions, columns=list(TABLE_TYPES["dbo.t_exception_log"]))
    for c in ("exception_date", "exception_time"):
        exc_df[c] = pd.to_datetime(exc_df[c])
    return {
        "dbo.t_exception_log": exc_df,
        "dbo.t_order": order_df,
        "dbo.t_tran_log": tran_df,
        "dbo.t_order_detail": pd.DataFrame({"order_number": order_df["order_number"].head(50), "line_number": 1,
                                            "item_number": "ITEM0001", "qty": 1, "wh_id": order_df["wh_id"].head(50)}),
        "dbo.t_item_master": pd.DataFrame({"item_number": ["ITEM0001"], "description": ["Widget"],
                                           "unit_weight": [1.5], "last_updated": [pd.Timestamp(now)]}),
        "dbo.t_tran_log_archive": tran_df[["tran_log_id", "tran_type", "start_tran_date", "wh_id", "tran_qty"]].head(10),
    }


class SyntheticDatabase:
    def __init__(self, tables, types=None):
        self.tables = tables
        self.types = types or TABLE_TYPES

    def catalog_rows(self):
        rows = []
        for ref, cols in self.types.items():
            if ref not in self.tables:
                continue
            schema, table = ref.split(".", 1)
            for col, typ in cols.items():
                name, length = (typ if isinstance(typ, tuple) else (typ, None))
                rows.append({"schema": schema, "table": table, "column": col, "data_type": name,
                             "max_length": length, "table_type": "BASE TABLE"})
        return rows


def _ts(df, ts):
    col = pd.to_datetime(df[ts["column"]])
    if ts.get("time_column"):
        t = pd.to_datetime(df[ts["time_column"]])
        return col.dt.normalize() + (t - t.dt.normalize())
    return col


class SyntheticData:
    """Same interface as queries.WorkspaceData (catalog / fetch / probe /
    query_log / close), answered from a SyntheticDatabase."""

    def __init__(self, db, scope=None, row_limit=50000, fail_labels=None, fail_all=False, fail_catalog=False):
        self.db = db
        self.scope = scope or {"primary_db_name": "WMS_DB", "secondary_db_name": None, "same_instance": False,
                               "secondary_db_alias": None}
        self.row_limit = row_limit
        self.fail_labels = set(fail_labels or ())
        self.fail_all = fail_all
        self.fail_catalog = fail_catalog
        self.query_log = []
        self.sql_seen = []
        self.closed = False

    def catalog(self):
        if self.fail_catalog or self.fail_all:
            self.query_log.append({"label": "catalog", "status": "failed"})
            raise RuntimeError("could not connect to the workspace database: login timeout")
        self.query_log.append({"label": "catalog", "status": "ok"})
        return self.db.catalog_rows()

    def _check(self, spec):
        sql = build_sql(spec)
        policy = validate_select_sql(sql, [spec.table_ref], self.scope)
        if not policy.ok:
            raise SqlPolicyError("; ".join(policy.errors))
        self.sql_seen.append(sql)
        if self.fail_all or any(lbl in (spec.label or "") for lbl in self.fail_labels):
            self.query_log.append({"label": spec.label, "status": "failed"})
            raise RuntimeError("query failed: simulated database error")

    def fetch(self, spec, window_start, window_end):
        self._check(spec)
        start = pd.Timestamp(window_start.replace(tzinfo=None) if window_start.tzinfo else window_start)
        end = pd.Timestamp(window_end.replace(tzinfo=None) if window_end.tzinfo else window_end)
        df = self.db.tables[spec.table_ref]
        filt = pd.to_datetime(df[spec.ts["column"]])
        m = (filt >= start) & (filt < end)
        if spec.kind == "probe":
            ts = _ts(df[m], spec.ts)
            mid = int(((ts.dt.hour == 0) & (ts.dt.minute == 0) & (ts.dt.second == 0)).sum()) if len(ts) else 0
            out = pd.DataFrame([{"n": int(m.sum()), "first_ts": ts.min() if len(ts) else None,
                                 "last_ts": ts.max() if len(ts) else None, "midnight_rows": mid}])
            self.query_log.append({"label": spec.label, "status": "ok", "rows": 1})
            return FetchResult(out)
        if spec.kind == "labels":
            sub = df[m]
            g = (sub.assign(__code=sub[spec.group_process].astype(str))
                 .groupby("__code").agg(label=(spec.description_column, "min"), rows=(spec.description_column, "size"))
                 .reset_index().rename(columns={"__code": "code"}))
            self.query_log.append({"label": spec.label, "status": "ok", "rows": len(g)})
            return FetchResult(g)
        if spec.kind == "backlog":
            created, done = _ts(df, spec.ts), _ts(df, spec.done_ts)
            m = m & (created < end) & (done.isna() | (done >= end))
            sub = df[m]
            keys = [c for c in (spec.group_warehouse, spec.group_dim) if c]
            if keys:
                g = sub.groupby(keys)[spec.measure_column].nunique().reset_index(name="n")
                g = g.rename(columns={spec.group_warehouse: "wh", spec.group_dim: "dim"} if spec.group_dim else
                             {spec.group_warehouse: "wh"})
            else:
                g = pd.DataFrame([{"n": sub[spec.measure_column].nunique()}])
            self.query_log.append({"label": spec.label, "status": "ok", "rows": len(g)})
            return FetchResult(normalize_frame(g))
        sub = df[m].copy()
        ts = _ts(sub, spec.ts)
        sub["bucket_date"] = ts.dt.date
        sub["bucket_hour"] = ts.dt.hour if spec.ts.get("granularity") == "hour" else 0
        keys = ["bucket_date", "bucket_hour"]
        rename = {}
        for alias, col in (("wh", spec.group_warehouse), ("proc", spec.group_process), ("dim", spec.group_dim)):
            if col:
                sub[f"__{alias}"] = sub[col].astype(str)
                keys.append(f"__{alias}")
                rename[f"__{alias}"] = alias
        if spec.measure == "duration":
            start_ts = _ts(sub, spec.start_ts)
            ok = start_ts.notna() & ts.notna() & (ts >= start_ts)
            sub = sub[ok]
            sub["__dur"] = ((ts[ok] - start_ts[ok]).dt.total_seconds() // 60).astype(float)
            g = sub.groupby(keys).agg(n=("__dur", "size"), dur_sum=("__dur", "sum")).reset_index()
        elif spec.measure == "count_distinct":
            g = sub.groupby(keys)[spec.measure_column].nunique().reset_index(name="n")
        elif spec.measure == "count_and_distinct":
            g = sub.groupby(keys).agg(n=(spec.measure_column, "size"),
                                      q=(spec.measure_column, "nunique")).reset_index()
        elif spec.measure == "sum":
            g = sub.groupby(keys).agg(n=(spec.measure_column, "size"), q=(spec.measure_column, "sum")).reset_index()
        else:
            g = sub.groupby(keys).size().reset_index(name="n")
        g = g.rename(columns=rename)
        truncated = len(g) > self.row_limit
        self.query_log.append({"label": spec.label, "status": "ok", "rows": min(len(g), self.row_limit),
                               "truncated": truncated})
        return FetchResult(normalize_frame(g.head(self.row_limit)), truncated)

    def probe(self, spec, window_start, window_end):
        f = self.fetch(spec, window_start, window_end).frame
        row = f.iloc[0].to_dict()
        return {"rows": int(row["n"]), "first_ts": row["first_ts"], "last_ts": row["last_ts"],
                "midnight_rows": int(row["midnight_rows"])}

    def close(self):
        self.closed = True


class FakeWorkspaceCollection:
    """Minimal stand-in for the ChromaDB Workspaces collection."""

    def __init__(self, workspaces):
        self._ws = {w["id"]: w["metadata"] for w in workspaces}

    def get(self, ids=None):
        keys = list(self._ws) if ids is None else [i for i in ids if i in self._ws]
        return {"ids": keys, "metadatas": [self._ws[k] for k in keys]}


def demo_workspace_meta(name="Synthetic Demo"):
    return {"name": name, "display_name": name,
            "db_config": json.dumps({"serverName": "synthetic", "databaseName": "WMS_DB", "username": "demo",
                                     "password": "not-a-real-password"}),
            "db_config_b": json.dumps({}), "llm_config": json.dumps({}),
            "email_recipients": json.dumps([{"label": "Operations Head", "address": "ops@example.invalid"}])}


def build_demo(out_dir, now=None):
    """Runs the real service end to end on synthetic data; writes the report files."""
    from zoneinfo import ZoneInfo

    from .delivery import EmailDelivery
    from .reporting import render_html, render_text
    from .service import ServiceSettings, WarehousePerfService
    from .store import WarehousePerfStore
    from .workspace_context import WorkspaceResolver

    tz = ZoneInfo("Asia/Kolkata")
    now = now or datetime(2026, 9, 24, 13, 30)
    db = SyntheticDatabase(generate_tables(now))
    ws = "00000000-0000-4000-8000-00000000demo"
    coll = FakeWorkspaceCollection([{"id": ws, "metadata": demo_workspace_meta()}])
    os.makedirs(out_dir, exist_ok=True)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        store = WarehousePerfStore(tmp)
        sent = []
        service = WarehousePerfService(
            store=store, resolver=WorkspaceResolver(coll), executor=None,
            delivery=EmailDelivery(store, lambda *a: sent.append(a) or True, lambda: {"send_email_enabled": True},
                                   sleep=lambda s: None),
            settings=ServiceSettings(timezone="Asia/Kolkata"), clock=lambda: now.replace(tzinfo=tz),
            narrator_factory=lambda cfg: None, data_factory=lambda ctx: SyntheticData(db))
        rec = service.run_analysis(ws, trigger="scheduled")
        report = store.get_report(ws, rec["report_id"])
    text = SYNTHETIC_BANNER + "\n\n" + render_text(report)
    with open(os.path.join(out_dir, "warehouse_perf_synthetic_report.txt"), "w", encoding="utf-8") as fh:
        fh.write(text)
    with open(os.path.join(out_dir, "warehouse_perf_synthetic_report.html"), "w", encoding="utf-8") as fh:
        fh.write(render_html(report).replace("<body>", f"<body><p><b>{SYNTHETIC_BANNER}</b></p>", 1))
    slim = {k: v for k, v in report["result"].items() if k != "query_log"}
    with open(os.path.join(out_dir, "warehouse_perf_synthetic_findings.json"), "w", encoding="utf-8") as fh:
        json.dump({"_note": SYNTHETIC_BANNER, **slim}, fh, indent=2, default=str)
    return rec, report, len(sent)


def main(argv=None):
    p = argparse.ArgumentParser(description="Generate the synthetic Warehouse Performance Agent demo report.")
    p.add_argument("--out", default=os.path.join("docs", "examples"))
    args = p.parse_args(argv)
    rec, report, sent = build_demo(args.out)
    dd = report["result"]["drilldown"]
    print(f"run status={rec['status']} report={rec['report_id']} emails={sent}")
    print("headline:", (dd.get("headline_metric") or {}).get("label"), "| warehouse:",
          (dd.get("warehouse") or {}).get("name"), "| process:", (dd.get("process") or {}).get("primary"),
          "| from:", (dd.get("time_window") or {}).get("start"))
    print(dd.get("conclusion"))


if __name__ == "__main__":
    main()

"""
Agent 1 of 3 — the Monitor: fetch → baseline → classify → drill down
("what changed, where and when?").

analyze(workspace_public, model, data, now, settings) runs one analysis cycle
for ONE workspace, using only `data` (a WorkspaceData bound to that
workspace) and the workspace's schema model. It returns a JSON-serialisable
structured result — the only thing the reporting layer and the LLM ever see.

A metric that fails (query error, truncated result, too little history) is
marked with its own status and reason; the remaining metrics still run.

When a deterioration is found, the result carries a "handoff": the Monitor's case
file for the Investigator agent (which measure, warehouse, hours and comparable
days, plus demand / order-size facts for those hours). It is the only thing the
Investigator receives from the Monitor.
"""
import logging
from datetime import datetime, time, timedelta

import numpy as np

from . import analytics as A
from .drilldown import drill_down
from .evidence import EXTERNAL_PROVIDERS
from .queries import QuerySpec
from .workspace_context import scrub_text

logger = logging.getLogger(__name__)

FRESHNESS_HOURS = 3
BACKLOG_LOOKBACK_DAYS = 30
PERIOD_TODAY = "today_so_far"
PERIOD_PREVIOUS = "previous_operating_day"
KPI_THROUGHPUT_ORDER = ("units_moved", "orders_dispatched", "transactions", "orders_completed", "orders_picked")


class Settings:
    def __init__(self, lookback_days=35, min_comparable=A.MIN_COMPARABLE, min_elapsed_hours=2,
                 backlog_lookback_days=BACKLOG_LOOKBACK_DAYS):
        self.lookback_days = max(22, int(lookback_days))
        self.min_comparable = max(2, int(min_comparable))
        self.min_elapsed_hours = max(1, int(min_elapsed_hours))
        self.backlog_lookback_days = int(backlog_lookback_days)


def _iso(d):
    return d.isoformat() if d is not None else None


def _hh(h):
    return f"{int(h) % 24:02d}:00" if h is not None else None


class _Run:
    """Per-run working state (never shared between runs or workspaces)."""

    def __init__(self, model, data, now, settings):
        self.model = model
        self.data = data
        self.now = now
        self.s = settings
        self.defs = {m["metric_id"]: m for m in model.get("metrics") or []}
        self.sources = model.get("sources") or {}
        self.cubes = {}
        self.failures = {}
        self.truncated = set()
        self.source_days = {"activity": set(), "orders": set()}
        self.limitations = []
        self.dim_cache = {}
        self.gran_override = {}
        self.lookback_start = datetime.combine(now.date() - timedelta(days=self.s.lookback_days), time.min)
        self.window_end = datetime.combine(now.date() + timedelta(days=1), time.min)

    # ------------------------------------------------------------ fetching
    def _spec_for(self, mid, group_dim=None):
        m = self.defs[mid]
        src = self.sources.get(m["source"]) or {}
        common = dict(schema=src["schema"], table=src["table"], group_warehouse=src.get("warehouse"),
                      group_dim=group_dim, label=f"{mid}{' by ' + group_dim if group_dim else ''}")
        if m["source"] == "activity":
            return QuerySpec("buckets", ts=src["ts"], measure="sum" if src.get("quantity") else "count",
                             measure_column=src.get("quantity"), group_process=src.get("process"), **common)
        if m["measure"] == "count_distinct":
            return QuerySpec("buckets", ts=src["stages"][m["stage"]], measure="count_distinct",
                             measure_column=src["order_key"], **common)
        if m["measure"] == "duration":
            return QuerySpec("buckets", ts=src["stages"][m["done_stage"]], measure="duration",
                             start_ts=src["stages"]["created"], **common)
        return None

    def fetch_all(self):
        activity_ids = [m for m, d in self.defs.items() if d["source"] == "activity"]
        if activity_ids:
            spec = self._spec_for(activity_ids[0])
            try:
                fr = self.data.fetch(spec, self.lookback_start, self.window_end)
            except Exception as exc:
                for mid in activity_ids:
                    self.failures[mid] = scrub_text(str(exc))
            else:
                self._check_granularity(activity_ids, fr.frame)
                self.cubes["transactions"] = A.Cube(self._labelled(fr.frame), "n")
                if "units_moved" in self.defs:
                    self.cubes["units_moved"] = A.Cube(self._labelled(self._outbound(fr.frame)), "q")
                self.source_days["activity"] = self.cubes["transactions"].active_days()
                if fr.truncated:
                    self.truncated.update(activity_ids)
        for mid, d in self.defs.items():
            if d["source"] != "orders" or d["measure"] not in ("count_distinct", "duration"):
                continue
            spec = self._spec_for(mid)
            try:
                fr = self.data.fetch(spec, self.lookback_start, self.window_end)
            except Exception as exc:
                self.failures[mid] = scrub_text(str(exc))
                continue
            self._check_granularity([mid], fr.frame)
            cube = A.Cube(fr.frame, "avg_duration" if d["measure"] == "duration" else "n")
            self.cubes[mid] = cube
            if d["measure"] == "count_distinct":
                self.source_days["orders"] |= cube.active_days()
            if fr.truncated:
                self.truncated.add(mid)

    def _outbound(self, frame):
        """Units moved: keep only pick/ship activity types when they could be identified."""
        codes = (self.defs.get("units_moved") or {}).get("outbound_codes") or []
        if not codes or frame is None or not len(frame) or "proc" not in frame:
            return frame
        return frame[frame["proc"].isin(set(codes))]

    def _labelled(self, frame):
        """Show activity types by name ("Pick (201)") instead of the raw code."""
        labels = (self.sources.get("activity") or {}).get("labels") or {}
        if not labels or frame is None or not len(frame) or "proc" not in frame or frame["proc"].isna().all():
            return frame
        f = frame.copy()
        f["proc"] = [f"{labels[c]} ({c})" if labels.get(c) else c for c in f["proc"]]
        return f

    def _check_granularity(self, mids, frame):
        """A timestamp whose every row falls in hour 0 over several days holds dates only."""
        if frame is None or not len(frame) or self.granularity(mids[0]) != "hour":
            return
        if (frame["bucket_hour"] == 0).all() and frame["bucket_date"].nunique() >= 3:
            for mid in mids:
                self.gran_override[mid] = "day"
            self.limitations.append(f"{', '.join(self.defs[m]['label'] for m in mids)}: the timestamps carry no time "
                                    f"of day, so they are compared per complete day.")

    def fetch_dim(self, mid, dim_key):
        """Lazy drill-down breakdown by a secondary dimension (category/zone/shift)."""
        key = (mid, dim_key)
        if key in self.dim_cache:
            return self.dim_cache[key]
        m = self.defs.get(mid)
        src = self.sources.get((m or {}).get("source")) or {}
        col = (src.get("dims") or {}).get(dim_key)
        cube = None
        if m and col and m["measure"] in ("count", "sum", "count_distinct"):
            try:
                fr = self.data.fetch(self._spec_for(mid, group_dim=col), self.lookback_start, self.window_end)
                if fr.truncated:
                    self.limitations.append(f"The {dim_key} breakdown hit the row limit and was not used.")
                else:
                    frame = self._outbound(fr.frame) if mid == "units_moved" else fr.frame
                    cube = A.Cube(self._labelled(frame), "q" if mid == "units_moved" else "n")
            except Exception as exc:
                self.limitations.append(f"The {dim_key} breakdown could not be read: {scrub_text(str(exc))}")
        self.dim_cache[key] = (cube, col) if cube is not None else None
        return self.dim_cache[key]

    def granularity(self, mid):
        if mid in self.gran_override:
            return self.gran_override[mid]
        m = self.defs[mid]
        src = self.sources.get(m["source"]) or {}
        if m["source"] == "activity":
            return src["ts"].get("granularity", "hour")
        stage = m.get("stage") or m.get("done_stage")
        return (src.get("stages", {}).get(stage) or {}).get("granularity", "hour")


def _choose_period(run):
    today, hours_now = run.now.date(), run.now.hour
    all_days = run.source_days["activity"] | run.source_days["orders"]
    if not all_days:
        return None
    hourly = any(run.granularity(mid) == "hour" for mid in run.cubes)
    same_weekday_history = sum(1 for k in range(1, A.SAME_WEEKDAY_WEEKS + 1)
                               if today - timedelta(weeks=k) in all_days)
    expected_today = today in all_days or same_weekday_history >= run.s.min_comparable
    if hourly and hours_now >= run.s.min_elapsed_hours and expected_today:
        return {"type": PERIOD_TODAY, "date": today, "hours": hours_now}
    prev = A.previous_operating_day(today, all_days)
    if prev is None:
        return {"type": PERIOD_TODAY, "date": today, "hours": max(1, hours_now)}
    return {"type": PERIOD_PREVIOUS, "date": prev, "hours": 24}


def _period_public(p):
    if p is None:
        return None
    label = (f"today {p['date'].isoformat()}, 00:00–{_hh(p['hours'])}" if p["type"] == PERIOD_TODAY
             else f"{p['date'].isoformat()} (full day)")
    return {"type": p["type"], "date": _iso(p["date"]), "start": "00:00",
            "end": "24:00" if p["hours"] >= 24 else _hh(p["hours"]), "elapsed_hours": p["hours"], "label": label}


def _shares(rows, direction, is_avg):
    if is_avg or direction == A.NEUTRAL:
        return
    short = {}
    for r in rows:
        a, b = r.get("actual"), r.get("baseline")
        if a is None or b is None:
            continue
        gap = (b - a) if direction == A.HIGHER else (a - b)
        if gap > 0:
            short[r["key"]] = gap
    total = sum(short.values())
    for r in rows:
        r["shortfall"] = A._r(short.get(r["key"], 0.0))
        r["share_of_shortfall_pct"] = A._r(short.get(r["key"], 0.0) / total * 100) if total > 0 else None


def _evaluate_breakdown(cube, period_date, hours, comps, direction, dimension, **fixed):
    rows = []
    for member in sorted(cube.members.get(dimension) or []):
        kw = dict(fixed)
        kw[dimension] = member
        actual = cube.value(period_date, hours, **kw)
        res = A.classify(actual, [cube.value(d, hours, **kw) for d in comps], direction)
        res["key"] = member
        rows.append(res)
    _shares(rows, direction, cube.kind == "avg_duration")
    rows.sort(key=lambda r: (A.oriented_pct(r, direction) if A.oriented_pct(r, direction) is not None else 0))
    return rows


def _evaluate_metric(run, mid, period):
    d = run.defs[mid]
    direction = d["direction"]
    base = {"metric_id": mid, "label": d["label"], "unit": d["unit"], "direction": direction,
            "source_table": None, "columns_used": [], "status": "ok"}
    src = run.sources.get(d["source"]) or {}
    base["source_table"] = f"{src.get('schema')}.{src.get('table')}" if src else None
    base["columns_used"] = _columns_used(d, src)
    if mid in run.failures:
        return {**base, "status": "query_failed", "reason": f"The query for this metric failed: {run.failures[mid]}",
                "classification": A.INSUFFICIENT}
    if mid in run.truncated:
        return {**base, "status": "data_truncated", "classification": A.INSUFFICIENT,
                "reason": "The result exceeded the row limit, so values would be incomplete; not analysed."}
    cube = run.cubes.get(mid)
    if cube is None:
        return {**base, "status": "unavailable", "classification": A.INSUFFICIENT, "reason": "No data was read."}

    p_date, hours, p_type = period["date"], period["hours"], period["type"]
    note = None
    if run.granularity(mid) == "day" and hours < 24:
        prev = A.previous_operating_day(run.now.date(), run.source_days[d["source"]])
        if prev is None:
            return {**base, "status": "insufficient_data", "classification": A.INSUFFICIENT,
                    "reason": "Timestamps are date-only and there is no previous complete day to analyse."}
        p_date, hours = prev, 24
        note = "Timestamps are date-only, so this metric is compared for the previous complete operating day."
    op_days = run.source_days[d["source"]] - {p_date}
    comps, method = A.select_comparables(p_date, op_days, run.s.min_comparable)
    actual = cube.value(p_date, hours)
    res = A.classify(actual, [cube.value(x, hours) for x in comps], direction, run.s.min_comparable)
    out = {**base, **res, "period_date": _iso(p_date), "period_hours": hours, "note": note,
           "baseline_method": method, "baseline_method_text": A.METHOD_TEXT[method],
           "comparables": [{"date": _iso(x), "value": A._r(cube.value(x, hours))} for x in comps]}
    if res["classification"] == A.INSUFFICIENT:
        out["status"] = "insufficient_data"
        out["reason"] = res["basis"]

    prev = A.previous_operating_day(p_date, run.source_days[d["source"]])
    if prev is not None:
        pv = cube.value(prev, hours)
        out["previous_day"] = {"date": _iso(prev), "value": A._r(pv), "pct_diff": A._r(A.pct_change(actual, pv))}
    hist = sorted(x for x in run.source_days[d["source"]] if x < p_date)[-A.TREND_DAYS:]
    out["trend"] = A.trend([(x, cube.value(x, 24)) for x in hist])

    if run.granularity(mid) == "hour" and hours >= 2 and len(comps) >= run.s.min_comparable:
        prof = A.hourly_profile(cube, p_date, hours, comps)
        out["hourly"] = [{"hour": r["hour"], "actual": r["actual"], "baseline": r["baseline"]} for r in prof]
        win = A.degradation_window(prof, direction)
        out["degradation_window"] = _window_public(win)
    if len(comps) >= run.s.min_comparable:
        if cube.members["wh"]:
            out["by_warehouse"] = _evaluate_breakdown(cube, p_date, hours, comps, direction, "wh")
        if cube.members["proc"]:
            out["by_process"] = _evaluate_breakdown(cube, p_date, hours, comps, direction, "proc")
            if cube.members["wh"]:
                out["by_warehouse_process"] = {
                    wh: _evaluate_breakdown(cube, p_date, hours, comps, direction, "proc", wh=wh)
                    for wh in sorted(cube.members["wh"])}
    out["_comps"] = comps
    out["_p_date"] = p_date
    out["_hours"] = hours
    return out


def _window_public(win):
    if not win:
        return None
    return {"start": _hh(win["start_hour"]), "end": _hh(win["end_hour"]), "ongoing": win["ongoing"],
            "adverse_hours": win["adverse_hours"], "gap": win["gap"]}


def _columns_used(d, src):
    if not src:
        return []
    cols = []
    if d["source"] == "activity":
        ts = src["ts"]
        cols += [ts["column"]] + ([ts["time_column"]] if ts.get("time_column") else [])
        if d["metric_id"] == "units_moved" and src.get("quantity"):
            cols.append(src["quantity"])
        cols += [c for c in (src.get("warehouse"), src.get("process")) if c]
    else:
        for stage in (d.get("stage"), d.get("done_stage"), "created" if d.get("done_stage") else None):
            ts = (src.get("stages") or {}).get(stage) if stage else None
            if ts:
                cols += [ts["column"]] + ([ts["time_column"]] if ts.get("time_column") else [])
        cols += [c for c in (src.get("order_key"), src.get("warehouse")) if c]
    seen, out = set(), []
    for c in cols:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _evaluate_backlog(run, period):
    mid = "pending_orders"
    d = run.defs[mid]
    src = run.sources["orders"]
    base = {"metric_id": mid, "label": d["label"], "unit": d["unit"], "direction": d["direction"],
            "source_table": f"{src['schema']}.{src['table']}", "columns_used": _columns_used(d, src),
            "status": "ok"}
    stages = src["stages"]
    p_date, hours = period["date"], period["hours"]
    if stages["created"].get("granularity") == "day" or stages[d["done_stage"]].get("granularity") == "day":
        if hours < 24:
            prev = A.previous_operating_day(run.now.date(), run.source_days["orders"])
            if prev is None:
                return {**base, "status": "insufficient_data", "classification": A.INSUFFICIENT,
                        "reason": "Order timestamps are date-only and there is no previous complete day."}
            p_date, hours = prev, 24
    comps, method = A.select_comparables(p_date, run.source_days["orders"] - {p_date}, run.s.min_comparable)
    prev = A.previous_operating_day(p_date, run.source_days["orders"])

    def as_of(day):
        return datetime.combine(day, time.min) + timedelta(hours=hours)

    def pending(day, dim=None, at=None):
        spec = QuerySpec("backlog", src["schema"], src["table"], stages["created"], measure="count_distinct",
                         measure_column=src["order_key"], done_ts=stages[d["done_stage"]],
                         group_warehouse=src.get("warehouse"), group_dim=dim,
                         label=f"pending orders as of {day.isoformat()}{' by status' if dim else ''}")
        t = at or as_of(day)
        return run.data.fetch(spec, t - timedelta(days=run.s.backlog_lookback_days), t)

    try:
        cur = pending(p_date)
    except Exception as exc:
        return {**base, "status": "query_failed", "classification": A.INSUFFICIENT,
                "reason": f"The pending-orders query failed: {scrub_text(str(exc))}"}
    frames, skipped = {}, 0
    for day in comps + ([prev] if prev and prev not in comps else []):
        try:
            frames[day] = pending(day).frame
        except Exception:
            skipped += 1
    comps = [x for x in comps if x in frames]

    def total(frame, wh=None):
        if frame is None or not len(frame):
            return 0.0
        if wh is not None and "wh" in frame:
            frame = frame[frame["wh"] == wh]
        return float(frame["n"].sum())

    actual = total(cur.frame)
    res = A.classify(actual, [total(frames[x]) for x in comps], d["direction"], run.s.min_comparable)
    out = {**base, **res, "period_date": _iso(p_date), "period_hours": hours, "baseline_method": method,
           "baseline_method_text": (f"pending orders at {_hh(hours) if hours < 24 else 'end of day'} on comparable "
                                    f"days ({A.METHOD_TEXT[method]})"),
           "comparables": [{"date": _iso(x), "value": total(frames[x])} for x in comps],
           "as_of": as_of(p_date).isoformat(timespec="minutes"),
           "note": (f"Counts orders created in the {run.s.backlog_lookback_days} days before each point in time "
                    f"that had no {d['done_stage']} timestamp yet at that time.")}
    if skipped:
        out["note"] += f" {skipped} comparable point(s) could not be read and were left out."
    if res["classification"] == A.INSUFFICIENT:
        out["status"] = "insufficient_data"
        out["reason"] = res["basis"]
    if prev in frames:
        pv = total(frames[prev])
        out["previous_day"] = {"date": _iso(prev), "value": pv, "pct_diff": A._r(A.pct_change(actual, pv))}
    whs = sorted(set(cur.frame["wh"]) | set().union(*[set(f["wh"]) for f in frames.values() if "wh" in f])) \
        if src.get("warehouse") and "wh" in cur.frame and cur.frame["wh"].notna().any() else []
    if whs and len(comps) >= run.s.min_comparable:
        rows = []
        for wh in whs:
            r = A.classify(total(cur.frame, wh), [total(frames[x], wh) for x in comps], d["direction"])
            r["key"] = wh
            rows.append(r)
        _shares(rows, d["direction"], False)
        rows.sort(key=lambda r: (A.oriented_pct(r, d["direction"]) or 0))
        out["by_warehouse"] = rows
    if src.get("status") and period["type"] == PERIOD_TODAY and p_date == period["date"]:
        try:
            snap = pending(p_date, dim=src["status"], at=run.now.replace(tzinfo=None, microsecond=0)).frame
            if len(snap):
                g = snap.groupby("dim")["n"].sum().sort_values(ascending=False).head(10)
                out["current_status_breakdown"] = [{"status": k, "orders": float(v)} for k, v in g.items()]
        except Exception:
            pass
    out["_comps"] = comps
    out["_p_date"] = p_date
    out["_hours"] = hours
    return out


VOLUME_METRICS = ("units_moved", "transactions", "orders_picked", "orders_packed", "orders_loaded",
                  "orders_dispatched", "orders_completed", "pending_orders")


def _demand_adjust(run, metrics):
    """When incoming order volume itself is unusual, a volume metric moving with
    it is not a performance problem. For each adverse volume metric, compare
    its ratio to orders received against the same ratio on the comparable
    days; if that ratio is within normal variation, the metric is reclassified
    as normal variation (raw classification kept)."""
    rec = metrics.get("orders_received")
    rcube = run.cubes.get("orders_received")
    if not rec or rcube is None or rec.get("classification") not in (A.BELOW, A.ABOVE):
        return []
    notes = []
    for mid in VOLUME_METRICS:
        m = metrics.get(mid)
        if not m or m.get("status") != "ok" or m.get("classification") not in A.ADVERSE or not m.get("_comps"):
            continue
        p_date, hours = m["_p_date"], m["_hours"]
        cur_rec = rcube.value(p_date, hours)
        if not cur_rec or m.get("actual") is None:
            continue
        comps = []
        for x in m["_comps"]:
            rv = rcube.value(x, hours)
            mv = next((c["value"] for c in m.get("comparables") or [] if c["date"] == _iso(x)), None)
            if rv and mv is not None:
                comps.append(mv / rv)
        adj = A.classify(m["actual"] / cur_rec, comps, m["direction"], run.s.min_comparable)
        m["demand_adjusted"] = {"ratio": A._r(m["actual"] / cur_rec, 4), "baseline_ratio": A._r(adj["baseline"], 4),
                                "pct_diff": adj["pct_diff"], "z_score": adj["z_score"],
                                "classification": adj["classification"]}
        if adj["classification"] in (A.NORMAL, A.IMPROVEMENT):
            m["raw_classification"] = m["classification"]
            m["classification"] = A.NORMAL
            m["basis"] = (f"moves with incoming orders (orders received {_pct(rec.get('pct_diff'))}); relative to "
                          f"orders received it is within normal variation")
            notes.append(f"{m['label']} changed by {_pct(m.get('pct_diff'))}, in line with orders received "
                         f"({_pct(rec.get('pct_diff'))}); relative to incoming orders it is within normal variation, "
                         f"so it is not treated as a deterioration.")
    return notes


def _pct(p):
    return "n/a" if p is None else f"{'+' if p > 0 else ''}{p:.1f}%"


def _freshness(run, period, metrics):
    if period["type"] != PERIOD_TODAY:
        return []
    warnings = []
    for source, lead in (("activity", "transactions"), ("orders", next(
            (m for m in ("orders_dispatched", "orders_received", "orders_picked", "orders_completed")
             if m in run.cubes), None))):
        cube = run.cubes.get(lead) if lead else None
        m = metrics.get(lead) if lead else None
        if cube is None or not m or not m.get("_comps") or run.granularity(lead) != "hour":
            continue
        hours = period["hours"]
        lo = max(0, hours - FRESHNESS_HOURS)
        expected = A.describe([sum(cube.value(x, hour=h) for h in range(lo, hours)) for x in m["_comps"]])["median"]
        recent = sum(cube.value(period["date"], hour=h) for h in range(lo, hours))
        if expected and expected > 0 and recent == 0:
            last = cube.last_active_hour(period["date"], hours)
            src = run.sources[source]
            since = f"since {_hh(last + 1)}" if last is not None else "at all today"
            warnings.append({"source": source, "table": f"{src['schema']}.{src['table']}",
                             "message": (f"No activity has been recorded in {src['schema']}.{src['table']} "
                                         f"{since}, although activity is normally recorded in these hours. This may be "
                                         f"a data-feed delay, so the most recent hours may be incomplete.")})
            for mid, d in run.defs.items():
                if d["source"] == source and mid in metrics:
                    metrics[mid]["freshness_warning"] = True
    return warnings


def _overall(metrics):
    perf = [m for m in metrics.values() if m.get("status") == "ok" and m["direction"] != A.NEUTRAL
            and m.get("classification") != A.INSUFFICIENT]
    if not perf:
        return {"classification": A.INSUFFICIENT, "performance_index_pct": None, "metrics_evaluated": 0,
                "basis": "no performance metric had enough history to compare"}
    oriented = [A.oriented_pct(m, m["direction"]) for m in perf]
    oriented = [o for o in oriented if o is not None]
    classes = [m["classification"] for m in perf]
    if A.SIGNIFICANT in classes:
        cls = A.SIGNIFICANT
    elif A.DETERIORATION in classes:
        cls = A.DETERIORATION
    elif A.IMPROVEMENT in classes:
        cls = A.IMPROVEMENT
    else:
        cls = A.NORMAL
    return {"classification": cls,
            "performance_index_pct": A._r(float(np.median(oriented))) if oriented else None,
            "metrics_evaluated": len(perf),
            "basis": ("median of the performance metrics' % changes against their baselines, signed so that "
                      "negative is worse; the classification is the most severe individual metric classification")}


def _changes(metrics):
    rows = []
    for m in metrics.values():
        if m.get("status") != "ok" or m.get("classification") == A.INSUFFICIENT:
            continue
        a, b = m.get("actual"), m.get("baseline")
        rows.append({"metric_id": m["metric_id"], "label": m["label"], "unit": m["unit"], "actual": a,
                     "baseline": b, "abs_diff": m.get("abs_diff"), "pct_diff": m.get("pct_diff"),
                     "z_score": m.get("z_score"), "classification": m["classification"],
                     "usual_range_pct": A.usual_range_pct(m),
                     "direction": "up" if (a or 0) > (b or 0) else "down" if (a or 0) < (b or 0) else "flat",
                     "favourable": (None if m["direction"] == A.NEUTRAL else
                                    m["classification"] == A.IMPROVEMENT or
                                    (m["classification"] == A.NORMAL and (A.oriented_pct(m, m["direction"]) or 0) >= 0)),
                     "freshness_warning": bool(m.get("freshness_warning")),
                     "demand_adjusted": bool(m.get("raw_classification"))})
    rows.sort(key=lambda r: (-A.SEVERITY.get(r["classification"], 0), -abs(r.get("z_score") or 0),
                             -abs(r.get("pct_diff") or 0)))
    return rows


def _kpis(metrics, overall):
    def pick(ids):
        for mid in ids:
            if mid in metrics:
                return _kpi(metrics[mid])
        return None
    return {
        "units_moved": pick(("units_moved", "transactions")),
        "orders_dispatched": pick(("orders_dispatched", "orders_completed")),
        "pending_orders": pick(("pending_orders",)),
        "overall": {"label": "Overall performance", "value": overall.get("performance_index_pct"), "unit": "%",
                    "classification": overall["classification"]},
    }


def _kpi(m):
    return {"metric_id": m["metric_id"], "label": m["label"], "unit": m["unit"], "value": m.get("actual"),
            "baseline": m.get("baseline"), "pct_diff": m.get("pct_diff"), "classification": m.get("classification"),
            "status": m.get("status"), "reason": m.get("reason"), "freshness_warning": bool(m.get("freshness_warning"))}


def analyze(workspace_public, model, data, now, settings=None):
    settings = settings or Settings()
    run = _Run(model, data, now, settings)
    result = {
        "schema_version": 1,
        "workspace": workspace_public,
        "generated_at": now.isoformat(timespec="seconds"),
        "status": "ok",
        "period": None,
        "metrics": [],
        "unavailable": list(model.get("unavailable") or []),
        "data_sources": _data_sources(model),
        "discovery_notes": list(model.get("notes") or []),
        "limitations": [],
        "evidence": {"internal": {"source": "workspace warehouse database", "items": []}, "external": [],
                     "correlation": None},
        "query_log": data.query_log if hasattr(data, "query_log") else [],
    }
    if not run.defs:
        found = [s for s in (model.get("sources") or {}).values() if s]
        if found:
            parts = []
            for src in found:
                latest = (src.get("probe") or {}).get("latest_record")
                parts.append(f"{src['schema']}.{src['table']}" + (f" (latest record {latest[:10]})" if latest else ""))
            result["status"] = "no_recent_data"
            result["message"] = (f"Warehouse tables were found ({', '.join(parts)}) but they contain no records in the "
                                 f"last {settings.lookback_days} days, so there is nothing current to analyse.")
        else:
            result["status"] = "no_metrics"
            result["message"] = ("No usable operational data was found in this workspace's database, so no metric "
                                 "could be derived. See the unavailable list for what is missing.")
        result["overall"] = _overall({})
        result["kpis"] = _kpis({}, result["overall"])
        result["changes"] = []
        result["drilldown"] = {"status": "not_run"}
        return result

    run.fetch_all()
    period = _choose_period(run)
    if period is None:
        result["status"] = "query_failed" if run.failures else "no_data"
        result["message"] = ("The workspace database could not be queried: " + "; ".join(sorted(set(
            run.failures.values())))) if result["status"] == "query_failed" else (
            f"No warehouse activity was found in the last {settings.lookback_days} days.")
        result["metrics"] = [{"metric_id": m, "label": d["label"], "status": "query_failed" if m in run.failures else
                              "no_data", "reason": run.failures.get(m), "classification": A.INSUFFICIENT,
                              "direction": d["direction"], "unit": d["unit"]} for m, d in run.defs.items()]
        result["overall"] = _overall({})
        result["kpis"] = _kpis({}, result["overall"])
        result["changes"] = []
        result["drilldown"] = {"status": "not_run"}
        return result
    result["period"] = _period_public(period)

    metrics = {}
    for mid in run.defs:
        if mid == "pending_orders":
            continue
        try:
            metrics[mid] = _evaluate_metric(run, mid, period)
        except Exception as exc:  # noqa: BLE001 — one metric's failure never stops the others
            logger.exception("warehouse_perf: metric %s failed", mid)
            metrics[mid] = {"metric_id": mid, "label": run.defs[mid]["label"], "unit": run.defs[mid]["unit"],
                            "direction": run.defs[mid]["direction"], "status": "query_failed",
                            "classification": A.INSUFFICIENT, "reason": scrub_text(f"{type(exc).__name__}: {exc}")}
    if "pending_orders" in run.defs:
        try:
            metrics["pending_orders"] = _evaluate_backlog(run, period)
        except Exception as exc:  # noqa: BLE001
            logger.exception("warehouse_perf: pending_orders failed")
            d = run.defs["pending_orders"]
            metrics["pending_orders"] = {"metric_id": "pending_orders", "label": d["label"], "unit": d["unit"],
                                         "direction": d["direction"], "status": "query_failed",
                                         "classification": A.INSUFFICIENT,
                                         "reason": scrub_text(f"{type(exc).__name__}: {exc}")}

    result["demand_adjustments"] = _demand_adjust(run, metrics)
    result["freshness_warnings"] = _freshness(run, period, metrics)
    result["overall"] = _overall(metrics)
    result["changes"] = _changes(metrics)
    result["drilldown"], evidence = drill_down(run, metrics, period)
    result["handoff"] = _handoff(run, metrics, result["drilldown"], result)
    result["evidence"]["internal"] = evidence.to_dict()
    result["evidence"]["external"] = [p.collect(workspace_public, result).to_dict() for p in EXTERNAL_PROVIDERS]
    result["kpis"] = _kpis(metrics, result["overall"])

    lim = list(run.limitations)
    if run.truncated:
        lim.append("Some results exceeded the row limit and were not analysed: " + ", ".join(sorted(run.truncated)) + ".")
    if (workspace_public or {}).get("secondary_database"):
        lim.append("Only the workspace's primary database is analysed; the secondary database is not used in V1.")
    for mid, m in metrics.items():
        if m.get("note"):
            lim.append(f"{m['label']}: {m['note']}")
    if (run.defs.get("units_moved") or {}).get("scope_note"):
        lim.append(run.defs["units_moved"]["scope_note"])
    for w in result["freshness_warnings"]:
        lim.append(w["message"])
    if any(d["measure"] == "count_distinct" for d in run.defs.values()):
        lim.append("Order counts are distinct per hour and summed, so an order that reaches the same stage in two "
                   "different hours is counted twice.")
    lim.append("Timestamps are read as the warehouse's local time "
               f"({(workspace_public or {}).get('timezone') or 'application default timezone'}).")
    lim.append("No external data (weather, traffic, transport, events) is used; causes outside the warehouse "
               "database cannot be assessed.")
    result["limitations"] = lim
    for m in metrics.values():
        for k in ("_comps", "_p_date", "_hours"):
            m.pop(k, None)
    order = list(run.defs)
    result["metrics"] = sorted(metrics.values(), key=lambda m: order.index(m["metric_id"]))
    return result


def _window_total(cube, day, start, end, wh=None):
    return cube.value(day, end, wh=wh) - cube.value(day, start, wh=wh)


def _window_fact(run, cube_ids, day, comps, start, end, wh, ratio=False):
    """A NEUTRAL comparison of a volume (or a units-per-order ratio) over the problem hours."""
    cubes = [run.cubes.get(c) for c in cube_ids]
    if any(c is None for c in cubes) or any(run.granularity(c) != "hour" for c in cube_ids):
        start, end = 0, 24
    if any(c is None for c in cubes):
        return None
    scope = wh if wh is not None and all(wh in c.members["wh"] for c in cubes) else None

    def val(d):
        if not ratio:
            return _window_total(cubes[0], d, start, end, scope)
        units, orders = (_window_total(c, d, start, end, scope) for c in cubes)
        return units / orders if orders else None

    actual = val(day)
    res = A.classify(actual, [v for v in (val(d) for d in comps) if v is not None], A.NEUTRAL)
    return {k: res.get(k) for k in ("actual", "baseline", "pct_diff", "z_score", "classification", "n_comparable")} \
        | {"warehouse": scope}


def _handoff(run, metrics, dd, result):
    """The Monitor's case file for the Investigator."""
    hd = dd.get("headline_metric")
    if not hd:
        return None
    m = metrics.get(hd["metric_id"]) or {}
    comps, p_date, hours = m.get("_comps"), m.get("_p_date"), m.get("_hours")
    if not comps or p_date is None or not hours:
        return None
    w = dd.get("warehouse") or {}
    wh = w.get("name")
    tw = dd.get("time_window") or {}
    start, end = 0, int(hours)
    if tw.get("start"):
        start = int(tw["start"][:2])
        if not tw.get("ongoing"):
            stop = int(tw["end"][:2])
            end = stop if stop > start else int(hours)
    others = [x["name"] for x in w.get("comparison") or []
              if x["name"] != wh and x.get("classification") not in A.ADVERSE]
    pend = metrics.get("pending_orders") or {}
    prow = next((x for x in pend.get("by_warehouse") or [] if x.get("key") == wh), None) if wh else None
    pend_src = prow or pend
    facts = {
        "orders_received": _window_fact(run, ["orders_received"], p_date, comps, start, end, wh),
        "units_per_order": _window_fact(run, ["units_moved", "orders_picked"], p_date, comps, start, end, wh,
                                        ratio=True) if "units_moved" in run.cubes else None,
        "pending_orders": ({k: pend_src.get(k) for k in ("actual", "baseline", "pct_diff", "classification")}
                           if pend.get("status") == "ok" else None),
        "freshness_warnings": [x["message"] for x in result.get("freshness_warnings") or []],
    }
    return {
        "metric_id": hd["metric_id"], "label": hd["label"], "unit": hd["unit"], "direction": m["direction"],
        "actual": hd.get("actual"), "baseline": hd.get("baseline"), "pct_diff": hd.get("pct_diff"),
        "classification": hd["classification"],
        "warehouse": wh, "warehouse_concentrated": bool(w.get("concentrated")), "other_warehouses_normal": others,
        "date": _iso(p_date), "period_hours": int(hours), "start_hour": start, "end_hour": end,
        "window_found": bool(tw), "ongoing": bool(tw.get("ongoing")),
        "comparable_dates": [_iso(d) for d in comps], "baseline_method": m.get("baseline_method"),
        "granularity": run.granularity(hd["metric_id"]),
        "step": (dd.get("process") or {}).get("primary"), "step_kind": (dd.get("process") or {}).get("kind"),
        "facts": facts,
    }


def _data_sources(model):
    out = []
    for kind, src in (model.get("sources") or {}).items():
        if not src:
            continue
        out.append({"kind": kind, "table": f"{src['schema']}.{src['table']}",
                    "rows_in_lookback": (src.get("probe") or {}).get("rows"),
                    "latest_record": (src.get("probe") or {}).get("last_ts"),
                    "warehouse_column": src.get("warehouse"),
                    "process_column": src.get("process"),
                    "timestamp": src.get("ts"),
                    "stages": {k: v.get("column") for k, v in (src.get("stages") or {}).items()} or None,
                    "dimensions": src.get("dims") or {}})
    return out

"""
Agent 2 of 3 — the Investigator: "why did it happen?"

Input: ONLY the Monitor's case file (result["handoff"]: which measure fell, in which
warehouse, in which hours, and which comparable days count as normal), the
workspace's schema model and the workspace's read-only data access. It never sees
the Monitor's working state, and the Advisor never sees the database.

For the problem hours it reads the warehouse's own records again and compares each
possible reason with the SAME hours on the SAME comparable days, using the same
baseline and z-score rules as the Monitor (analytics.classify):

  staffing       people recording work per hour, per activity type (the activity
                 log's employee/user column)
  productivity   work done per person per hour, per activity type
  stock          short picks, location denials, stock adjustments (activity types
                 or exception types whose description says so), with the items involved
  rework         reversals / unpicks / cancellations
  exceptions     entries in the WMS exception/error log, per exception type
  demand         orders received in the same hours            (Monitor's facts)
  order size     units per order in the same hours            (Monitor's facts)
  data feed      no records at all in recent hours            (Monitor's facts)

Each check is "supported" (outside normal variation in the adverse direction),
"ruled_out" (within normal variation) or "not_checked" (the data needed is missing,
with the reason). Nothing is concluded here: ranking the causes and advising is the
Advisor's job (advisor.py).

Every query is generated from the schema model (queries.build_sql), runs through the
same read-only executor and policy as the Monitor's, and covers one day at a time
(the problem day and each comparable day), so result sizes stay small.
"""
import logging
import math
import re
import time as _time
from datetime import date, datetime, time, timedelta

import pandas as pd

from . import analytics as A
from .discovery import split_tokens
from .drilldown import fmt_num, fmt_pct
from .queries import NOT_RECORDED, QuerySpec
from .workspace_context import scrub_text

logger = logging.getLogger(__name__)

SUPPORTED, RULED_OUT, NOT_CHECKED = "supported", "ruled_out", "not_checked"
MIN_EVENTS = 3            # a problem-event spike needs at least this many events in the window ...
MIN_EXTRA_EVENTS = 2      # ... and at least this many more than normal
MAX_ACTIVITY_TYPES = 4
MIN_TYPE_VOLUME = 5       # activity types smaller than this (baseline, in the window) are not examined
MAX_EXCEPTION_CHECKS = 4
TOP_ITEMS = 5
MIN_ORDER_SIZE_CHANGE_PCT = 15.0   # bigger orders only count as a reason when they are materially bigger

STOCK_WORDS = {"short", "shortage", "shorted", "denial", "denied", "deny", "stockout", "unavailable", "empty",
               "adjust", "adjustment", "adjustments", "itu"}
STOCK_PHRASES = ("not available", "no stock", "not found", "no itu")
REWORK_WORDS = {"unpick", "unload", "unship", "reverse", "reversal", "reversed", "undo", "cancel", "cancelled",
                "canceled", "void", "voided", "return", "returned", "reject", "rejected", "correction"}

HYPOTHESES = {
    "staffing": "Fewer people working",
    "productivity": "Slower work per person",
    "stock": "Stock and location problems",
    "rework": "Work being undone (reversals)",
    "exceptions": "Exceptions logged by the warehouse system",
    "demand": "Fewer orders coming in",
    "order_size": "Bigger orders than usual",
    "data_feed": "Warehouse system not recording",
}


def problem_category(label):
    """'stock' / 'rework' for a problem activity or exception type, from its description; else None."""
    text = str(label or "").lower()
    toks = set(split_tokens(text))
    if toks & REWORK_WORDS:
        return "rework"
    if toks & STOCK_WORDS or any(p in text for p in STOCK_PHRASES):
        return "stock"
    return None


def clean_label(text, limit=60):
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    return (t[:limit - 1].rstrip() + "…") if len(t) > limit else t


def _hh(h):
    return f"{int(h) % 24:02d}:00"


class _Window:
    """The problem hours on the problem day and on each comparable day."""

    def __init__(self, case, granularity="hour"):
        self.day = date.fromisoformat(case["date"])
        self.comps = [date.fromisoformat(x) for x in case["comparable_dates"]]
        self.hourly = granularity == "hour"
        self.start = int(case["start_hour"]) if self.hourly else 0
        self.end = int(case["end_hour"]) if self.hourly else 24
        if self.end <= self.start:
            self.end = self.start + 1
        self.days = [self.day] + self.comps

    @property
    def label(self):
        return f"{_hh(self.start)}–{_hh(self.end)}" if self.hourly and (self.start, self.end) != (0, 24) else "the day"

    @property
    def since(self):
        return f"since {_hh(self.start)}" if self.hourly and self.start else "today" if self.hourly else "that day"

    def total(self, cube, day, **kw):
        if not self.hourly:
            return cube.value(day, 24, **kw)
        return cube.value(day, self.end, **kw) - cube.value(day, self.start, **kw)

    def hours(self):
        return list(range(self.start, self.end)) if self.hourly else [0]


def _fetch_days(data, spec, days):
    """One query per day (problem day + comparable days); returns (frame, truncated)."""
    frames, truncated = [], False
    for d in days:
        start = datetime.combine(d, time.min)
        fr = data.fetch(spec, start, start + timedelta(days=1))
        truncated = truncated or fr.truncated
        if fr.frame is not None and len(fr.frame):
            frames.append(fr.frame)
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()), truncated


def _check(cid, hypothesis, status, statement, subject=None, res=None, unit=None, **extra):
    out = {"id": cid, "hypothesis": hypothesis, "hypothesis_title": HYPOTHESES[hypothesis], "subject": subject,
           "status": status, "statement": statement, "unit": unit}
    if res:
        out.update({k: res.get(k) for k in ("actual", "baseline", "pct_diff", "z_score", "classification",
                                            "n_comparable")})
    out.update(extra)
    return out


def _events_status(res):
    """A problem-event count (more is worse) is a supported reason only when it is
    outside normal variation AND large enough to matter."""
    a, b = res.get("actual") or 0, res.get("baseline") or 0
    if res.get("classification") in A.ADVERSE and a >= MIN_EVENTS and a - b >= MIN_EXTRA_EVENTS:
        return SUPPORTED
    return RULED_OUT


def _decline_shares(vol, staff, rate):
    """Split a volume decline into 'fewer people' and 'less per person' (log shares, 0..1)."""
    a, b = vol.get("actual"), vol.get("baseline")
    if a is None or not b or a >= b:
        return None, None
    lv = math.log(max(a, b * 0.01) / b)

    def part(x):
        xa, xb = x.get("actual"), x.get("baseline")
        if xa is None or not xb or xa >= xb:
            return 0.0
        return max(0.0, min(1.0, math.log(max(xa, xb * 0.01) / xb) / lv))

    s, r = part(staff), part(rate)
    if s + r > 1:
        s, r = s / (s + r), r / (s + r)
    return round(s, 2), round(r, 2)


class Investigator:
    def __init__(self, case, model, data):
        self.case = case
        self.model = model or {}
        self.data = data
        self.act = (self.model.get("sources") or {}).get("activity") or {}
        self.exc = (self.model.get("evidence_sources") or {}).get("exceptions")
        self.labels = self.act.get("labels") or {}
        self.wh = case.get("warehouse")
        self.checks = []
        self.notes = []
        self.activity = []
        self.sources = []
        self.failed = 0

    # ---------------------------------------------------------- helpers
    def _name(self, code):
        label = self.labels.get(code)
        return f"{clean_label(label)} ({code})" if label else str(code)

    def _where(self):
        return f" in {self.wh}" if self.wh else ""

    def _fail(self, what, exc):
        self.failed += 1
        msg = f"{what} could not be read: {scrub_text(str(exc))}"
        self.notes.append(msg)
        logger.warning("warehouse_perf investigator: %s", msg)

    # ------------------------------------------------------------- run
    def run(self):
        self._activity_checks()
        self._exception_checks()
        self._fact_checks()
        return self.checks

    # ----------------------------------------------- staffing / productivity / problem activity types
    def _activity_checks(self):
        act = self.act
        if not act or not act.get("ts"):
            for h in ("staffing", "productivity", "stock", "rework"):
                self.checks.append(_check(f"{h}:none", h, NOT_CHECKED, "No warehouse activity log was found.",
                                          reason="no activity/transaction table"))
            return
        W = _Window(self.case, act["ts"].get("granularity", "hour"))
        self.window = W
        table = f"{act['schema']}.{act['table']}"
        actor = act.get("actor")
        per_hour = "per hour" if W.hourly else "per day"
        common = dict(schema=act["schema"], table=act["table"], ts=act["ts"], group_warehouse=act.get("warehouse"))
        try:
            if actor:
                spec = QuerySpec("buckets", measure="count_and_distinct", measure_column=actor,
                                 group_process=act.get("process"), label="investigator: activity and people by type",
                                 **common)
            else:
                spec = QuerySpec("buckets", measure="count", group_process=act.get("process"),
                                 label="investigator: activity by type", **common)
            frame, truncated = _fetch_days(self.data, spec, W.days)
        except Exception as exc:  # noqa: BLE001
            self._fail("Activity by type", exc)
            for h in ("staffing", "productivity", "stock", "rework"):
                self.checks.append(_check(f"{h}:failed", h, NOT_CHECKED, "The activity log could not be read.",
                                          reason="query failed"))
            return
        if truncated:
            self.notes.append("The activity breakdown hit the row limit; activity-type checks may be incomplete.")
        self.sources.append({"name": "Activity log", "table": table,
                             "columns": [c for c in (act["ts"]["column"], act["ts"].get("time_column"),
                                                     act.get("warehouse"), act.get("process"), actor) if c]})
        vol = A.Cube(frame, "n")
        people = A.Cube(frame, "q") if actor else None
        scope = self.wh if self.wh in vol.members["wh"] else None
        if self.wh and scope is None:
            self.notes.append(f"Warehouse {self.wh} does not appear in {table}; activity checks cover all warehouses.")
        self.act_scope = scope
        codes = sorted(vol.members["proc"]) if vol.members["proc"] else [None]
        problem = {c: problem_category(self.labels.get(c)) for c in codes if c is not None}

        # -- people on the floor overall
        if actor:
            try:
                tspec = QuerySpec("buckets", measure="count_distinct", measure_column=actor,
                                  label="investigator: people working", **common)
                tframe, _ = _fetch_days(self.data, tspec, W.days)
                tcube = A.Cube(tframe, "n")
                hours = [h for h in W.hours() if tcube.value(W.day, hour=h, wh=scope) or
                         A.describe([tcube.value(d, hour=h, wh=scope) for d in W.comps])["median"]]
                if hours:
                    def avg(d):
                        return sum(tcube.value(d, hour=h, wh=scope) for h in hours) / len(hours)
                    res = A.classify(avg(W.day), [avg(d) for d in W.comps], A.HIGHER)
                    status = SUPPORTED if res["classification"] in A.ADVERSE else RULED_OUT
                    self.checks.append(_check(
                        "staffing:all", "staffing", status,
                        f"People recording work{self._where()} {W.label}: {fmt_num(res['actual'])} {per_hour} "
                        f"(normally {fmt_num(res['baseline'])}, {fmt_pct(res['pct_diff'])}).",
                        subject="all activities", res=res, unit=f"people {per_hour}"))
            except Exception as exc:  # noqa: BLE001
                self._fail("People working", exc)
        else:
            self.checks.append(_check("staffing:none", "staffing", NOT_CHECKED,
                                      f"{table} has no employee/user column, so staffing could not be checked.",
                                      reason="no person column"))

        # -- per activity type: volume, people, work per person
        rows = []
        for code in codes:
            if code is not None and problem.get(code):
                continue
            kw = {"wh": scope, "proc": code}
            v = A.classify(W.total(vol, W.day, **kw), [W.total(vol, d, **kw) for d in W.comps], A.HIGHER)
            if (v.get("baseline") or 0) < MIN_TYPE_VOLUME and (v.get("actual") or 0) < MIN_TYPE_VOLUME:
                continue
            rows.append((code, kw, v))
        adverse = sorted([r for r in rows if r[2]["classification"] in A.ADVERSE],
                         key=lambda r: -((r[2]["baseline"] or 0) - (r[2]["actual"] or 0)))
        examine = adverse[:MAX_ACTIVITY_TYPES] or sorted(rows, key=lambda r: -(r[2]["baseline"] or 0))[:3]
        shortfall = sum(max(0.0, (r[2]["baseline"] or 0) - (r[2]["actual"] or 0)) for r in adverse) or None
        for code, kw, v in examine:
            name = self._name(code) if code is not None else "all activity"
            row = {"code": code, "name": name, "volume": v, "people": None, "per_person": None,
                   "staff_share": None, "rate_share": None, "shortfall": None, "shortfall_share": None}
            if v["classification"] in A.ADVERSE and shortfall:
                row["shortfall"] = A._r((v["baseline"] or 0) - (v["actual"] or 0))
                row["shortfall_share"] = A._r(row["shortfall"] / shortfall, 3)
            if people is not None:
                hours = [h for h in W.hours() if vol.value(W.day, hour=h, **kw) or
                         A.describe([vol.value(d, hour=h, **kw) for d in W.comps])["median"]]
                if hours:
                    def staff(d):
                        return sum(people.value(d, hour=h, **kw) for h in hours)

                    def rate(d):
                        ph = staff(d)
                        return W.total(vol, d, **kw) / ph if ph else None
                    s = A.classify(staff(W.day) / len(hours), [staff(d) / len(hours) for d in W.comps], A.HIGHER)
                    r = A.classify(rate(W.day), [x for x in (rate(d) for d in W.comps) if x is not None], A.HIGHER)
                    row["people"], row["per_person"] = s, r
                    row["staff_share"], row["rate_share"] = _decline_shares(v, s, r)
                    vol_text = (f"{name}{self._where()} {W.label}: {fmt_num(v['actual'])} (normally "
                                f"{fmt_num(v['baseline'])}, {fmt_pct(v['pct_diff'])})")
                    self.checks.append(_check(
                        f"staffing:{code}", "staffing", SUPPORTED if s["classification"] in A.ADVERSE else RULED_OUT,
                        f"People doing {name}{self._where()} {W.label}: {fmt_num(s['actual'])} {per_hour} "
                        f"(normally {fmt_num(s['baseline'])}, {fmt_pct(s['pct_diff'])}).",
                        subject=name, res=s, unit=f"people {per_hour}", activity=code,
                        share_of_decline=row["staff_share"], volume=vol_text))
                    self.checks.append(_check(
                        f"productivity:{code}", "productivity",
                        SUPPORTED if r["classification"] in A.ADVERSE else RULED_OUT,
                        f"{name} per person{self._where()} {W.label}: {fmt_num(r['actual'])} {per_hour} "
                        f"(normally {fmt_num(r['baseline'])}, {fmt_pct(r['pct_diff'])}).",
                        subject=name, res=r, unit=f"per person {per_hour}", activity=code,
                        share_of_decline=row["rate_share"], volume=vol_text))
            self.activity.append(row)
        if people is None and examine:
            self.checks.append(_check("productivity:none", "productivity", NOT_CHECKED,
                                      "Work per person needs an employee/user column in the activity log.",
                                      reason="no person column"))

        # -- problem activity types (short picks, denials, adjustments, reversals)
        for cat in ("stock", "rework"):
            cat_codes = [c for c, p in problem.items() if p == cat]
            if not cat_codes:
                self.checks.append(_check(
                    f"{cat}:none", cat, NOT_CHECKED,
                    f"The activity log has no {'short-pick / denial / adjustment' if cat == 'stock' else 'reversal'} "
                    f"transaction types in the comparison period, so this could not be checked.",
                    reason="no such activity types"))
                continue
            for code in cat_codes:
                kw = {"wh": scope, "proc": code}
                res = A.classify(W.total(vol, W.day, **kw), [W.total(vol, d, **kw) for d in W.comps], A.LOWER)
                status = _events_status(res)
                check = _check(f"{cat}:{code}", cat, status,
                               f"{self._name(code)}{self._where()} {W.label}: {fmt_num(res['actual'])} "
                               f"(normally {fmt_num(res['baseline'])}).", subject=self._name(code), res=res,
                               unit="events", activity=code)
                if status == SUPPORTED and cat == "stock" and act.get("item"):
                    check["items"] = self._items(common, act["item"], code, scope, W)
                self.checks.append(check)

    def _items(self, common, item_col, code, scope, W):
        """The items most involved in a problem activity type during the problem hours."""
        try:
            spec = QuerySpec("buckets", measure="count", group_process=self.act.get("process"), group_dim=item_col,
                             label="investigator: items with stock problems", **common)
            frame, _ = _fetch_days(self.data, spec, [W.day])
        except Exception as exc:  # noqa: BLE001
            self._fail("Items with stock problems", exc)
            return []
        if not len(frame):
            return []
        f = frame[(frame["proc"] == code) & (frame["dim"] != NOT_RECORDED)]
        if scope is not None:
            f = f[f["wh"] == scope]
        if W.hourly:
            f = f[(f["bucket_hour"] >= W.start) & (f["bucket_hour"] < W.end)]
        top = f.groupby("dim")["n"].sum().sort_values(ascending=False).head(TOP_ITEMS)
        return [{"item": str(k), "events": int(v)} for k, v in top.items()]

    # ------------------------------------------------------------ exceptions
    def _exception_checks(self):
        exc = self.exc
        if not exc:
            self.checks.append(_check("exceptions:none", "exceptions", NOT_CHECKED,
                                      "No exception/error log was found in this database.", reason="no exception log"))
            return
        table = f"{exc['schema']}.{exc['table']}"
        probe = exc.get("probe") or {}
        if probe.get("rows") == 0:
            latest = probe.get("latest_record")
            self.checks.append(_check(
                "exceptions:stale", "exceptions", NOT_CHECKED,
                f"The exception log ({table}) has no recent records"
                + (f" (latest {latest[:10]})" if latest else "") + ", so system exceptions could not be checked.",
                reason="no recent records"))
            return
        W = _Window(self.case, exc["ts"].get("granularity", "hour"))
        group = exc.get("type") or exc.get("description")
        common = dict(schema=exc["schema"], table=exc["table"], ts=exc["ts"])
        try:
            spec = QuerySpec("buckets", measure="count", group_warehouse=exc.get("warehouse"), group_process=group,
                             label="investigator: exceptions by type", **common)
            frame, _ = _fetch_days(self.data, spec, W.days)
            labels = {}
            if exc.get("type") and exc.get("description"):
                lspec = QuerySpec("labels", group_process=exc["type"], description_column=exc["description"],
                                  label="investigator: exception types", **common)
                lo = datetime.combine(min(W.days), time.min)
                lf = self.data.fetch(lspec, lo, datetime.combine(W.day, time.min) + timedelta(days=1)).frame
                lf.columns = [str(c).lower() for c in lf.columns]
                labels = {str(r["code"]).strip(): clean_label(r.get("label")) for r in lf.to_dict("records")
                          if r.get("code") is not None}
        except Exception as exc_:  # noqa: BLE001
            self._fail("Exception log", exc_)
            self.checks.append(_check("exceptions:failed", "exceptions", NOT_CHECKED,
                                      f"The exception log ({table}) could not be read.", reason="query failed"))
            return
        self.sources.append({"name": "Exception log", "table": table,
                             "columns": [c for c in (exc["ts"]["column"], exc["ts"].get("time_column"),
                                                     exc.get("warehouse"), exc.get("type"), exc.get("description"))
                                         if c]})
        cube = A.Cube(frame, "n")
        scope = self.wh if self.wh in cube.members["wh"] else None
        where = f" in {scope}" if scope else ""

        def name(code):
            lbl = labels.get(code) if exc.get("type") else None
            return f"{lbl} ({code})" if lbl else clean_label(code)

        total = A.classify(W.total(cube, W.day, wh=scope), [W.total(cube, d, wh=scope) for d in W.comps], A.LOWER)
        per_type = []
        for code in sorted(cube.members["proc"]):
            kw = {"wh": scope, "proc": code}
            res = A.classify(W.total(cube, W.day, **kw), [W.total(cube, d, **kw) for d in W.comps], A.LOWER)
            if (res["actual"] or 0) == 0 and (res["baseline"] or 0) == 0:
                continue
            per_type.append((code, res, _events_status(res)))
        spikes = sorted([x for x in per_type if x[2] == SUPPORTED],
                        key=lambda x: -((x[1]["actual"] or 0) - (x[1]["baseline"] or 0)))
        for code, res, _ in spikes[:MAX_EXCEPTION_CHECKS]:
            label = labels.get(code) if exc.get("type") else code
            hyp = "stock" if problem_category(label) == "stock" else "exceptions"
            self.checks.append(_check(
                f"exceptions:{code}", hyp, SUPPORTED,
                f"'{name(code)}' exceptions{where} {W.label}: {fmt_num(res['actual'])} (normally "
                f"{fmt_num(res['baseline'])}).", subject=name(code), res=res, unit="exceptions", source=table))
        if not spikes:
            self.checks.append(_check(
                "exceptions:all", "exceptions", RULED_OUT,
                f"Exceptions logged{where} {W.label}: {fmt_num(total['actual'])} (normally "
                f"{fmt_num(total['baseline'])}); no exception type is above its normal level.",
                subject="all exception types", res=total, unit="exceptions", source=table))

    # ------------------------------------------------------- Monitor's facts
    def _fact_checks(self):
        f = self.case.get("facts") or {}
        window = getattr(self, "window", None) or _Window(self.case, self.case.get("granularity", "hour"))
        rec = f.get("orders_received")
        if rec and rec.get("classification") not in (None, A.INSUFFICIENT):
            where = f" in {rec['warehouse']}" if rec.get("warehouse") else ""
            self.checks.append(_check(
                "demand:orders_received", "demand", SUPPORTED if rec["classification"] == A.BELOW else RULED_OUT,
                f"Orders received{where} {window.label}: {fmt_num(rec['actual'])} (normally "
                f"{fmt_num(rec['baseline'])}, {fmt_pct(rec['pct_diff'])}).", subject="orders received", res=rec,
                unit="orders"))
        else:
            self.checks.append(_check("demand:none", "demand", NOT_CHECKED,
                                      "Incoming order volume could not be compared (no order-created timestamps "
                                      "or too little history).", reason="no orders received metric"))
        size = f.get("units_per_order")
        if size and size.get("classification") not in (None, A.INSUFFICIENT):
            bigger = size["classification"] == A.ABOVE and (size.get("pct_diff") or 0) >= MIN_ORDER_SIZE_CHANGE_PCT
            where = f" in {size['warehouse']}" if size.get("warehouse") else ""
            self.checks.append(_check(
                "order_size:units_per_order", "order_size", SUPPORTED if bigger else RULED_OUT,
                f"Units per order picked{where} {window.label}: {fmt_num(size['actual'])} (normally "
                f"{fmt_num(size['baseline'])}, {fmt_pct(size['pct_diff'])}).", subject="units per order", res=size,
                unit="units per order"))
        warnings = f.get("freshness_warnings") or []
        self.checks.append(_check(
            "data_feed:freshness", "data_feed", SUPPORTED if warnings else RULED_OUT,
            warnings[0] if warnings else "Records are arriving normally in the most recent hours.",
            subject="recent records"))


def investigate(case, model, data):
    """Runs the Investigator for one Monitor case. Never raises."""
    started = _time.time()
    if not case:
        return {"status": "not_needed", "checks": [], "activity": [], "sources": [], "notes": [],
                "reason": "the Monitor found no deterioration to investigate"}
    inv = Investigator(case, model, data)
    try:
        checks = inv.run()
        status = "partial" if inv.failed else "done"
    except Exception as exc:  # noqa: BLE001 — the report still goes out without the investigation
        logger.exception("warehouse_perf: investigation failed")
        checks, status = inv.checks, "failed"
        inv.notes.append(f"The investigation stopped early: {scrub_text(f'{type(exc).__name__}: {exc}')}")
    W = getattr(inv, "window", None)
    return {
        "status": status,
        "scope": {"warehouse": case.get("warehouse"), "date": case.get("date"),
                  "from": _hh(case["start_hour"]), "to": _hh(case["end_hour"]),
                  "window_label": W.label if W else None, "comparable_dates": case.get("comparable_dates")},
        "checks": checks,
        "activity": [{k: v for k, v in r.items()} for r in inv.activity],
        "sources": inv.sources,
        "notes": inv.notes,
        "summary": {s: sum(1 for c in checks if c["status"] == s) for s in (SUPPORTED, RULED_OUT, NOT_CHECKED)},
        "duration_seconds": round(_time.time() - started, 2),
    }

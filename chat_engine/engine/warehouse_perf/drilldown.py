"""
Phase 4 — automatic internal drill-down ("where did it change, and when?").

Starting from the metric that deteriorated most (most severe classification,
then most negative z-score), the drill-down descends only as far as the
workspace's data supports:

  overall metric → warehouse (largest share of the shortfall)
                 → process within that warehouse (order stages, or the
                   activity-type values of the transaction table)
                 → time window (earliest hour of the sustained adverse run)
                 → secondary dimensions present in the schema
                   (category / zone / shift), within that warehouse

Cross-metric context (orders received, pending orders, processing time) is
reported as INFERENCE, never as a finding. The Monitor never states a cause: its
conclusion says what changed, where and when. Possible causes are checked by the
Investigator agent and ranked by the Advisor agent (investigator.py, advisor.py).
"""
from . import analytics as A
from .evidence import InternalEvidence
from .queries import NOT_RECORDED

NOUN = {
    "units_moved": "units-moved", "transactions": "warehouse activity", "orders_picked": "picking",
    "orders_packed": "packing", "orders_loaded": "loading", "orders_dispatched": "dispatch",
    "orders_completed": "order completion", "pending_orders": "pending orders",
    "processing_time": "order processing time",
}
CONSEQUENCE_METRICS = ("pending_orders", "processing_time")
STAGE_METRICS = ("orders_picked", "orders_packed", "orders_loaded", "orders_dispatched", "orders_completed")
PROCESS_NAME = {"orders_picked": "picking", "orders_packed": "packing", "orders_loaded": "loading",
                "orders_dispatched": "dispatch", "orders_completed": "completion"}


def fmt_num(v, unit=""):
    if v is None:
        return "n/a"
    v = float(v)
    s = f"{v:,.0f}" if abs(v) >= 100 or v == int(v) else f"{v:,.1f}"
    return f"{s} {unit}".strip()


def fmt_pct(p):
    if p is None:
        return "n/a"
    return f"{'+' if p > 0 else '−' if p < 0 else ''}{abs(p):.1f}%"


def _oz(m):
    z = m.get("z_score")
    if z is None:
        return 0.0
    return z if m["direction"] == A.HIGHER else -z


def _headline(metrics):
    cands = [m for m in metrics.values()
             if m.get("status") == "ok" and m["direction"] != A.NEUTRAL and m.get("classification") in A.ADVERSE]
    # Throughput/process metrics outrank their knock-on effects (backlog, processing time)
    # at equal severity, so the drill-down starts from where work actually slowed.
    cands.sort(key=lambda m: (bool(m.get("freshness_warning")), -A.SEVERITY[m["classification"]],
                              m["metric_id"] in CONSEQUENCE_METRICS, _oz(m), A.oriented_pct(m, m["direction"]) or 0))
    return cands


def _row(r, direction):
    return {"name": r["key"], "actual": r.get("actual"), "baseline": r.get("baseline"), "pct_diff": r.get("pct_diff"),
            "z_score": r.get("z_score"), "classification": r.get("classification"),
            "share_of_shortfall_pct": r.get("share_of_shortfall_pct"),
            "usual_range_pct": A.usual_range_pct(r), "oriented_pct": A.oriented_pct(r, direction)}


def _process_rows(run, metrics, headline, wh):
    """Process-level comparison inside `wh` (or overall when wh is None)."""
    stage_rows = []
    for mid in STAGE_METRICS:
        m = metrics.get(mid)
        if not m or m.get("status") != "ok":
            continue
        if wh is None:
            r = {**m, "key": PROCESS_NAME[mid]}
        else:
            r = next((x for x in m.get("by_warehouse") or [] if x["key"] == wh), None)
            if r is None:
                continue
            r = {**r, "key": PROCESS_NAME[mid]}
        stage_rows.append({**_row(r, A.HIGHER), "metric_id": mid})
    activity_rows = []
    act = metrics.get(headline["metric_id"]) if headline["metric_id"] in ("units_moved", "transactions") else \
        metrics.get("transactions")
    if act and act.get("status") == "ok":
        src_rows = (act.get("by_warehouse_process") or {}).get(wh) if wh is not None else act.get("by_process")
        for r in src_rows or []:
            activity_rows.append({**_row(r, act["direction"]), "metric_id": act["metric_id"]})
    prefer_stages = headline["metric_id"] in STAGE_METRICS or headline["metric_id"] in ("pending_orders",
                                                                                         "processing_time")
    rows = stage_rows if (prefer_stages and len(stage_rows) >= 2) or not activity_rows else activity_rows
    if len(rows) < 2 and rows is stage_rows and activity_rows:
        rows = activity_rows
    kind = "order stage" if rows is stage_rows else "activity type"
    rows = sorted(rows, key=lambda r: (r["oriented_pct"] if r["oriented_pct"] is not None else 0))
    return rows, kind


def drill_down(run, metrics, period):
    ev = InternalEvidence()
    out = {"status": "no_deterioration", "headline_metric": None, "metric_ranking": [], "warehouse": None,
           "process": None, "time_window": None, "dimensions": [], "context": [], "conclusion": None,
           "recommendations": []}
    ranked = _headline(metrics)
    out["metric_ranking"] = [{"metric_id": m["metric_id"], "label": m["label"], "pct_diff": m.get("pct_diff"),
                              "z_score": m.get("z_score"), "classification": m["classification"],
                              "freshness_warning": bool(m.get("freshness_warning"))} for m in ranked]
    plabel = (run and period and (f"today up to {period['hours']:02d}:00" if period["type"] == "today_so_far"
                                  else f"on {period['date'].isoformat()}")) or "in the period"

    for m in metrics.values():
        if m.get("status") == "ok" and m.get("actual") is not None and m.get("baseline") is not None:
            ev.add("observed", f"{m['label']}: {fmt_num(m['actual'], m['unit'])} {plabel}.", m["metric_id"])
    for m in metrics.values():
        adj = m.get("demand_adjusted")
        if adj and m.get("raw_classification"):
            ev.add("calculated", f"{m['label']} per order received is {fmt_pct(adj.get('pct_diff'))} against its "
                                 f"baseline ratio — within normal variation, so the {fmt_pct(m.get('pct_diff'))} change "
                                 f"follows incoming order volume.", m["metric_id"])
    if not ranked:
        evaluated = [m for m in metrics.values() if m.get("status") == "ok"]
        out["conclusion"] = ("No deterioration beyond normal historical variation was detected in the metrics that "
                             "could be analysed." if evaluated else
                             "No metric had enough history to compare, so no deterioration can be assessed yet.")
        for m in evaluated:
            if m.get("classification") == A.IMPROVEMENT:
                ev.add("calculated", f"{m['label']} is {fmt_pct(m.get('pct_diff'))} against its baseline of "
                                     f"{fmt_num(m.get('baseline'), m['unit'])} (improvement).", m["metric_id"])
        out["recommendations"] = ["No action is indicated by the available data; monitoring continues automatically."]
        _unknowns(ev, metrics, run)
        return out, ev

    h = ranked[0]
    direction = h["direction"]
    out["status"] = "deterioration_found"
    out["headline_metric"] = {"metric_id": h["metric_id"], "label": h["label"], "actual": h.get("actual"),
                              "baseline": h.get("baseline"), "pct_diff": h.get("pct_diff"),
                              "z_score": h.get("z_score"), "classification": h["classification"],
                              "unit": h["unit"], "baseline_method": h.get("baseline_method_text")}
    ev.add("calculated", f"{h['label']} is {fmt_pct(h.get('pct_diff'))} against a baseline of "
                         f"{fmt_num(h.get('baseline'), h['unit'])} ({h.get('baseline_method_text')}, "
                         f"{h.get('n_comparable')} comparable periods).", h["metric_id"])
    if h.get("z_score") is not None:
        ev.add("anomaly", f"{h['label']} is {abs(h['z_score']):.1f} standard deviations "
                          f"{'below' if h['z_score'] < 0 else 'above'} its historical mean for this window — "
                          f"{h['classification'].replace('_', ' ')}.", h["metric_id"])
    for other in ranked[1:]:
        ev.add("anomaly", f"{other['label']} also shows {other['classification'].replace('_', ' ')} "
                          f"({fmt_pct(other.get('pct_diff'))}).", other["metric_id"])

    # ---- warehouse
    wh = None
    wh_rows = [_row(r, direction) for r in h.get("by_warehouse") or []]
    if wh_rows:
        adverse = [r for r in wh_rows if (r.get("share_of_shortfall_pct") or 0) > 0]
        adverse.sort(key=lambda r: -(r["share_of_shortfall_pct"] or 0))
        if not adverse and h["unit"] == "minutes":
            adverse = [r for r in wh_rows if (r["oriented_pct"] or 0) < 0]
        if adverse:
            top = adverse[0]
            wh = top["name"]
            share = top.get("share_of_shortfall_pct")
            concentrated = share is not None and share >= 50
            out["warehouse"] = {"name": wh, "share_of_shortfall_pct": share, "concentrated": concentrated,
                                "pct_diff": top.get("pct_diff"), "classification": top.get("classification"),
                                "comparison": wh_rows}
            if share is not None:
                ev.add("calculated", f"Warehouse {wh} accounts for {share:.0f}% of the total {NOUN[h['metric_id']]} "
                                     f"shortfall ({fmt_pct(top.get('pct_diff'))} against its own baseline).",
                       h["metric_id"], warehouse=wh)
            else:
                ev.add("calculated", f"Warehouse {wh} shows the largest adverse change "
                                     f"({fmt_pct(top.get('pct_diff'))}).", h["metric_id"], warehouse=wh)
            others = [r for r in wh_rows if r["name"] != wh and r.get("pct_diff") is not None]
            if others:
                ev.add("calculated", "Other warehouses: " + ", ".join(
                    f"{r['name']} {fmt_pct(r['pct_diff'])}" for r in others[:6]) + ".", h["metric_id"])
        else:
            out["warehouse"] = {"name": None, "comparison": wh_rows, "concentrated": False}

    # ---- process
    proc_rows, proc_kind = _process_rows(run, metrics, h, wh)
    primary_proc = None
    if proc_rows:
        worst = next((r for r in proc_rows if r.get("classification") in A.ADVERSE), None)
        primary_proc = worst or (proc_rows[0] if (proc_rows[0]["oriented_pct"] or 0) < 0 else None)
        out["process"] = {"scope": wh, "kind": proc_kind, "comparison": proc_rows,
                          "primary": primary_proc["name"] if primary_proc else None,
                          "primary_is_significant": bool(worst)}
        where = f"Within warehouse {wh}" if wh else "Across the warehouse"
        listing = ", ".join(f"{r['name']} {fmt_pct(r['pct_diff'])}" for r in proc_rows)
        ev.add("calculated", f"{where}, {proc_kind} changes against baseline: {listing}.", h["metric_id"],
               warehouse=wh)
        if primary_proc:
            ev.add("calculated", f"The largest observed decline {('in warehouse ' + wh) if wh else ''} is in "
                                 f"{primary_proc['name']} ({fmt_pct(primary_proc['pct_diff'])})"
                                 f"{'' if worst else ', though it is within normal historical variation'}.".replace(
                                     "decline  is", "decline is"), primary_proc.get("metric_id"), warehouse=wh)

    # ---- time window
    win = None
    comps, p_date, hours = h.get("_comps"), h.get("_p_date"), h.get("_hours")
    cube = run.cubes.get(h["metric_id"]) if run else None
    if cube is not None and comps and run.granularity(h["metric_id"]) == "hour" and hours and hours >= 2:
        prof = A.hourly_profile(cube, p_date, hours, comps, wh=wh if wh in cube.members["wh"] else None)
        w = A.degradation_window(prof, direction)
        if w:
            win = {"scope": wh, "start": f"{w['start_hour']:02d}:00", "end": f"{w['end_hour'] % 24:02d}:00",
                   "ongoing": w["ongoing"], "adverse_hours": w["adverse_hours"],
                   "hourly": [{"hour": r["hour"], "actual": r["actual"], "baseline": r["baseline"]} for r in prof]}
            out["time_window"] = win
            ev.add("calculated", f"Hourly comparison{(' for warehouse ' + wh) if wh else ''}: "
                                 f"{NOUN[h['metric_id']]} has been on the adverse side of its hourly baseline from "
                                 f"{win['start']}{' and still is' if w['ongoing'] else ' until ' + win['end']}.",
                   h["metric_id"], warehouse=wh)
    elif run and run.granularity(h["metric_id"]) != "hour":
        ev.add("unknown", "The timestamps for this metric are date-only, so the time of day at which the change "
                          "began cannot be determined.", h["metric_id"])

    # ---- secondary dimensions
    for key in ("category", "zone", "shift"):
        got = run.fetch_dim(h["metric_id"], key) if run and comps else None
        if not got:
            continue
        dcube, col = got
        rows = []
        for member in sorted(dcube.members["dim"]):
            if member == NOT_RECORDED:      # blank category/zone values say nothing about where to look
                continue
            kw = {"dim": member}
            if wh is not None and wh in dcube.members["wh"]:
                kw["wh"] = wh
            r = A.classify(dcube.value(p_date, hours, **kw), [dcube.value(x, hours, **kw) for x in comps], direction)
            r["key"] = member
            rows.append(r)
        from .analyzer import _shares  # local import: analyzer imports this module
        _shares(rows, direction, False)
        rows = [_row(r, direction) for r in rows if (r.get("share_of_shortfall_pct") or 0) > 0]
        rows.sort(key=lambda r: -(r["share_of_shortfall_pct"] or 0))
        if rows:
            out["dimensions"].append({"dimension": key, "column": col, "scope": wh, "top": rows[:5]})
            top = rows[0]
            ev.add("calculated", f"By {key}{(' in warehouse ' + wh) if wh else ''}: '{top['name']}' accounts for "
                                 f"{top['share_of_shortfall_pct']:.0f}% of the shortfall "
                                 f"({fmt_pct(top['pct_diff'])}).", h["metric_id"], warehouse=wh, dimension=key)

    # ---- cross-metric context (inference only)
    rec = metrics.get("orders_received")
    if rec and rec.get("status") == "ok" and rec.get("classification") == A.BELOW and direction == A.HIGHER:
        msg = (f"Orders received were also below normal ({fmt_pct(rec.get('pct_diff'))}); lower incoming order volume "
               f"may account for part of the decline. This is an interpretation, not a verified cause.")
        out["context"].append(msg)
        ev.add("inference", msg, "orders_received")
    pend = metrics.get("pending_orders")
    if pend and pend.get("status") == "ok" and h["metric_id"] != "pending_orders" and \
            pend.get("classification") in A.ADVERSE:
        msg = (f"Pending orders are {fmt_pct(pend.get('pct_diff'))} against their baseline, which is consistent with "
               f"orders accumulating rather than a drop in demand. This is an interpretation, not a verified cause.")
        out["context"].append(msg)
        ev.add("inference", msg, "pending_orders")
    pt = metrics.get("processing_time")
    if pt and pt.get("status") == "ok" and h["metric_id"] != "processing_time" and \
            pt.get("classification") in A.ADVERSE:
        msg = f"Order processing time is {fmt_pct(pt.get('pct_diff'))} against its baseline."
        out["context"].append(msg)
        ev.add("calculated", msg, "processing_time")
    if h.get("freshness_warning"):
        ev.add("unknown", "Recent hours show no records at all in this source table; a data-feed delay cannot be "
                          "ruled out from the database alone.", h["metric_id"])

    # ---- conclusion (never a cause)
    sig = "significant " if h["classification"] == A.SIGNIFICANT else ""
    noun = NOUN[h["metric_id"]]
    what = f"a {sig}{noun} decline" if direction == A.HIGHER else f"a {sig}increase in {noun}"
    parts = [f"The available warehouse data shows {what}"]
    if out.get("warehouse") and out["warehouse"].get("name"):
        parts.append(f" concentrated in warehouse {wh}" if out["warehouse"]["concentrated"]
                     else f", with the largest share in warehouse {wh}")
    if primary_proc and primary_proc["name"] != PROCESS_NAME.get(h["metric_id"]):
        parts.append(f", where the largest observed decline is in {primary_proc['name']} "
                     f"({fmt_pct(primary_proc['pct_diff'])})")
    if win:
        parts.append(f", beginning around {win['start']}")
    parts.append(". These performance measures show what changed, where and when - not why; the possible causes "
                 "are checked separately against the warehouse records.")
    out["conclusion"] = "".join(parts)
    ev.add("unknown", out["conclusion"], h["metric_id"])
    _unknowns(ev, metrics, run)

    # ---- recommended areas for investigation (deterministic)
    recs = []
    area = primary_proc["name"] if primary_proc else noun
    recs.append(f"Review {area} activity{(' in warehouse ' + wh) if wh else ''}"
                f"{(' from ' + win['start'] + ' onward') if win else ''} ({plabel}).")
    for dim in out["dimensions"][:2]:
        t = dim["top"][0]
        recs.append(f"Check {dim['dimension']} '{t['name']}'{(' in warehouse ' + wh) if wh else ''}, which accounts "
                    f"for {t['share_of_shortfall_pct']:.0f}% of the shortfall.")
    if pend and pend.get("status") == "ok" and pend.get("classification") in A.ADVERSE:
        recs.append("Review the pending-order queue"
                    f"{(' in warehouse ' + wh) if wh else ''}; pending orders are {fmt_pct(pend.get('pct_diff'))} "
                    f"against baseline.")
    if h.get("freshness_warning"):
        recs.append("Confirm that the warehouse system is still recording transactions for the most recent hours.")
    recs.append("Confirm the findings with the operations team.")
    out["recommendations"] = recs
    return out, ev


def _unknowns(ev, metrics, run):
    for u in (run.model.get("unavailable") if run else None) or []:
        ev.add("unknown", u["reason"], u["metric_id"])
    for m in metrics.values():
        if m.get("status") in ("insufficient_data", "query_failed", "data_truncated") and m.get("reason"):
            ev.add("unknown", f"{m['label']}: {m['reason']}", m["metric_id"])

"""
Phase 6 — executive report generation.

The report is rendered deterministically from the structured analysis
result. The only LLM-written text is the executive summary, and it is used
only if validate_narrative() accepts it: every number in it must already
appear in the structured facts, and it may not state a cause, mention
external factors (V1 uses none) or include URLs. Otherwise the deterministic
summary is used and the report says so.

Sections: 1 executive summary · 2 current performance · 3 historical baseline
· 4 major deviations · 5 warehouse comparison · 6 process comparison · 7 time
of degradation · 8 pending/backlog impact · 9 evidence-based internal
findings (each labelled observed / calculated / anomaly / inference /
unknown) · 10 data limitations · 11 recommended areas for investigation
· 12 root-cause investigation (Investigator agent) · 13 likely causes and
recommended actions (Advisor agent) · 14 how the agents worked.

The likely causes come from the Advisor's deterministic ranking of the
Investigator's checks; the LLM summary never states a cause itself, and the
Advisor's one-line summary is appended to it.
"""
import html
import json
import re

from .drilldown import fmt_num, fmt_pct
from .evidence import KIND_LABEL

CLASS_TEXT = {
    "significant_deterioration": "Significant deterioration",
    "deterioration": "Deterioration",
    "normal_variation": "Normal variation",
    "improvement": "Improvement",
    "insufficient_data": "Insufficient data",
    "above_normal": "Above normal",
    "below_normal": "Below normal",
}
STATUS_TEXT = {
    "insufficient_data": "Insufficient history", "query_failed": "Query failed", "data_truncated": "Row limit hit",
    "unavailable": "Unavailable", "no_data": "No data",
}


def cls_text(c):
    return CLASS_TEXT.get(c, c or "—")


def deterministic_summary(result):
    period = (result.get("period") or {}).get("label") or "the latest period"
    if result.get("status") != "ok":
        return result.get("message") or "No analysis could be completed."
    ov = result.get("overall") or {}
    dd = result.get("drilldown") or {}
    parts = []
    idx = ov.get("performance_index_pct")
    if idx is not None:
        parts.append(f"For {period}, overall performance is {fmt_pct(idx)} against the historical baseline "
                     f"({cls_text(ov.get('classification')).lower()}).")
    else:
        parts.append(f"For {period}, there is not yet enough history to establish a baseline.")
    h = dd.get("headline_metric")
    if h:
        parts.append(f"The largest deterioration is in {h['label'].lower()}: {fmt_num(h['actual'], h['unit'])} against "
                     f"a baseline of {fmt_num(h['baseline'], h['unit'])} ({fmt_pct(h['pct_diff'])}, "
                     f"{cls_text(h['classification']).lower()}).")
    if dd.get("conclusion"):
        parts.append(dd["conclusion"])
    diag = (result.get("diagnosis") or {}).get("summary")
    if diag:
        parts.append(diag)
    improvements = [c for c in result.get("changes") or [] if c["classification"] == "improvement"]
    if improvements:
        parts.append("Improvements: " + ", ".join(f"{c['label'].lower()} {fmt_pct(c['pct_diff'])}"
                                                  for c in improvements[:3]) + ".")
    return " ".join(parts)


# -------------------------------------------------------- narrative checks
_NUM_RE = re.compile(r"(?<![\w.])[-+−]?\d[\d,]*(?:\.\d+)?")
_DATE_OR_TIME_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}:\d{2}\b")
_CAUSAL_RE = re.compile(r"\b(caused by|because of|due to|as a result of|resulted from|result of|led to|leading to|"
                        r"driven by|attributable to|the reason|stems from|owing to|thanks to)\b", re.IGNORECASE)
_EXTERNAL_RE = re.compile(r"\b(weather|rain|storm|snow|flood|wind|fog|heat ?wave|traffic|congestion|road|roads|"
                          r"transport|transportation|carrier|carriers|truck|trucks|courier|holiday|strike|"
                          r"public event|festival)\b", re.IGNORECASE)
_URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)


def _numbers_in(result):
    """Numbers the narrative may use: exactly those in the facts sent to the LLM."""
    blob = json.dumps(narrative_facts(result), default=str)
    nums = set()
    for tok in _NUM_RE.findall(blob):
        try:
            v = abs(float(tok.replace(",", "").replace("−", "-")))
        except ValueError:
            continue
        nums.update({round(v, 2), round(v, 1), float(round(v))})
    return nums


def validate_narrative(text, result):
    """Returns (ok, reasons)."""
    reasons = []
    if not text or not text.strip():
        return False, ["empty narrative"]
    if len(text) > 1800:
        reasons.append("narrative too long")
    known = _numbers_in(result)
    for tok in _NUM_RE.findall(_DATE_OR_TIME_RE.sub(" ", text)):
        try:
            v = abs(float(tok.replace(",", "").replace("−", "-")))
        except ValueError:
            continue
        if v in (0.0, 1.0, 2.0, 3.0) and "." not in tok:
            continue
        if round(v, 2) not in known and round(v, 1) not in known and float(round(v)) not in known:
            reasons.append(f"number {tok} does not appear in the computed findings")
    if _CAUSAL_RE.search(text):
        reasons.append("states a cause; V1 reports only what changed, where and when")
    if _EXTERNAL_RE.search(text):
        reasons.append("mentions external factors, which V1 does not analyse")
    if _URL_RE.search(text):
        reasons.append("contains a URL")
    return (not reasons), reasons


NARRATIVE_SYSTEM_PROMPT = (
    "You write the executive summary (at most 5 sentences, plain text) of a warehouse performance analysis for "
    "senior managers. Use ONLY the facts in the JSON you are given and copy numbers exactly as written there. "
    "Say what changed, where and when. Never state or suggest a cause (the likely causes are reported "
    "separately from the investigation): do not use phrases like 'due to', 'because of', 'caused by' or "
    "'driven by'. Never mention weather, traffic, transport, carriers or holidays. No URLs, no lists, no markdown."
)


def generate_narrative(narrator, result):
    """Returns (text_or_None, source, rejection_reasons)."""
    if narrator is None:
        return None, "deterministic", ["no LLM configured for this workspace"]
    if result.get("status") != "ok":
        return None, "deterministic", ["analysis did not complete"]
    try:
        text = narrator.complete(NARRATIVE_SYSTEM_PROMPT, json.dumps(narrative_facts(result), default=str))
    except Exception as exc:  # noqa: BLE001
        return None, "deterministic_fallback", [f"LLM call failed: {type(exc).__name__}"]
    ok, reasons = validate_narrative(text, result)
    if not ok:
        return None, "deterministic_fallback", reasons
    return text.strip(), "llm_validated", []


def narrative_facts(result):
    """The structured facts (never raw rows) given to the LLM."""
    dd = result.get("drilldown") or {}
    return {
        "period": result.get("period"),
        "overall": result.get("overall"),
        "changes": [{k: c.get(k) for k in ("label", "actual", "baseline", "pct_diff", "classification")}
                    for c in (result.get("changes") or [])[:6]],
        "headline": dd.get("headline_metric"),
        "warehouse": {k: (dd.get("warehouse") or {}).get(k) for k in ("name", "share_of_shortfall_pct", "pct_diff")},
        "process": {"primary": (dd.get("process") or {}).get("primary"),
                    "comparison": [{k: x.get(k) for k in ("name", "pct_diff", "classification")}
                                   for x in (dd.get("process") or {}).get("comparison") or []]},
        "time_window": {k: (dd.get("time_window") or {}).get(k) for k in ("start", "ongoing")},
        "context": dd.get("context") or [],
        "conclusion": dd.get("conclusion"),
    }


# ------------------------------------------------------------------ build
def build_report(report_id, result, narrative=None, narrative_source="deterministic", narrative_rejections=None):
    ws = result.get("workspace") or {}
    summary = narrative or deterministic_summary(result)
    diag = (result.get("diagnosis") or {}).get("summary")
    if narrative and diag:
        summary = f"{narrative.strip()} {diag}"
    return {
        "report_id": report_id,
        "workspace_id": ws.get("workspace_id"),
        "workspace_name": ws.get("display_name") or ws.get("name"),
        "generated_at": result.get("generated_at"),
        "title": f"Warehouse Performance Report — {ws.get('display_name') or ws.get('name') or ''}".strip(" —"),
        "period": result.get("period"),
        "status": result.get("status"),
        "overall": result.get("overall"),
        "executive_summary": summary,
        "summary_source": narrative_source if narrative else ("deterministic" if narrative_source == "deterministic"
                                                               else "deterministic_fallback"),
        "narrative_rejections": narrative_rejections or [],
        "alert_worthy": is_alert_worthy(result),
        "result": result,
    }


def is_alert_worthy(result):
    """Automatic delivery is triggered only by a significant deterioration that
    is not accompanied by a data-freshness warning on the same metric."""
    return any(c["classification"] == "significant_deterioration" and not c.get("freshness_warning")
               for c in result.get("changes") or [])


def alert_signature(result):
    ids = sorted(c["metric_id"] for c in result.get("changes") or []
                 if c["classification"] == "significant_deterioration" and not c.get("freshness_warning"))
    return f"{(result.get('period') or {}).get('date')}:{','.join(ids)}"


def _metric_line(m):
    if m.get("status") != "ok":
        return f"- {m['label']}: {STATUS_TEXT.get(m.get('status'), m.get('status'))} — {m.get('reason') or ''}".rstrip(" —")
    return (f"- {m['label']}: {fmt_num(m.get('actual'), m['unit'])} (baseline {fmt_num(m.get('baseline'), m['unit'])}, "
            f"{fmt_pct(m.get('pct_diff'))}, {cls_text(m.get('classification')).lower()})")


def sections(report):
    r = report["result"]
    dd = r.get("drilldown") or {}
    metrics = r.get("metrics") or []
    S = []

    S.append(("1. Executive summary", [report["executive_summary"],
                                       "(Summary written by the workspace's LLM from the calculated findings and "
                                       "checked against them.)" if report["summary_source"] == "llm_validated" else
                                       "(Summary generated deterministically from the calculated findings.)"]))
    cur = [f"Analysis period: {(r.get('period') or {}).get('label') or 'n/a'}."]
    ov = r.get("overall") or {}
    if ov.get("performance_index_pct") is not None:
        cur.append(f"Overall performance: {fmt_pct(ov['performance_index_pct'])} against baseline "
                   f"({cls_text(ov.get('classification')).lower()}; {ov.get('basis')}).")
    cur += [f"- {m['label']}: {fmt_num(m.get('actual'), m['unit'])}" for m in metrics
            if m.get("status") in ("ok", "insufficient_data") and m.get("actual") is not None]
    S.append(("2. Current performance", cur))

    base = []
    for m in metrics:
        if m.get("comparables") is not None and m.get("status") == "ok":
            comp = ", ".join(f"{c['date']}: {fmt_num(c['value'])}" for c in m["comparables"])
            base.append(f"- {m['label']}: baseline {fmt_num(m.get('baseline'), m['unit'])} — "
                        f"{m.get('baseline_method_text')} ({comp}).")
        elif m.get("status") == "insufficient_data":
            base.append(f"- {m['label']}: {m.get('reason')}")
    S.append(("3. Historical baseline", base or ["No baseline could be established."]))

    dev = [f"- {c['label']}: {fmt_num(c['actual'], c['unit'])} vs {fmt_num(c['baseline'], c['unit'])} "
           f"({fmt_pct(c['pct_diff'])}; z = {c['z_score'] if c['z_score'] is not None else 'n/a'}) — "
           f"{cls_text(c['classification'])}" for c in r.get("changes") or []
           if c["classification"] not in ("normal_variation",)]
    dev += list(r.get("demand_adjustments") or [])
    S.append(("4. Major deviations", dev or ["No metric moved beyond normal historical variation."]))

    wh_lines = []
    w = dd.get("warehouse") or {}
    if w.get("comparison"):
        h = dd.get("headline_metric") or {}
        wh_lines.append(f"{h.get('label', 'Headline metric')} by warehouse:")
        wh_lines += [f"- {x['name']}: {fmt_num(x['actual'])} vs {fmt_num(x['baseline'])} ({fmt_pct(x['pct_diff'])})"
                     + (f", {x['share_of_shortfall_pct']:.0f}% of the shortfall" if x.get("share_of_shortfall_pct") else "")
                     + f" — {cls_text(x['classification']).lower()}" for x in w["comparison"]]
    else:
        lead = next((m for m in metrics if m.get("by_warehouse")), None)
        if lead:
            wh_lines.append(f"{lead['label']} by warehouse:")
            wh_lines += [f"- {x['key']}: {fmt_num(x.get('actual'))} vs {fmt_num(x.get('baseline'))} "
                         f"({fmt_pct(x.get('pct_diff'))}) — {cls_text(x.get('classification')).lower()}"
                         for x in lead["by_warehouse"]]
    S.append(("5. Warehouse-level comparison", wh_lines or [
        "No warehouse identifier was found in the data, so warehouses cannot be compared."]))

    p = dd.get("process") or {}
    if p.get("comparison"):
        pl = [f"{('Warehouse ' + p['scope']) if p.get('scope') else 'All warehouses'} — by {p.get('kind')}:"]
        pl += [f"- {x['name']}: {fmt_num(x['actual'])} vs {fmt_num(x['baseline'])} ({fmt_pct(x['pct_diff'])}) — "
               f"{cls_text(x['classification']).lower()}" for x in p["comparison"]]
        if p.get("primary"):
            pl.append(f"Largest observed decline: {p['primary']}"
                      f"{'' if p.get('primary_is_significant') else ' (within normal variation)'}.")
        S.append(("6. Process-level comparison", pl))
    else:
        S.append(("6. Process-level comparison", [
            "No process-level breakdown was produced (no deterioration to investigate, or no stage timestamps / "
            "activity-type column in the data)."]))

    t = dd.get("time_window")
    if t:
        tl = [f"{('Warehouse ' + t['scope'] + ': ') if t.get('scope') else ''}adverse from {t['start']}"
              f"{' and ongoing' if t['ongoing'] else ' until ' + t['end']} ({t['adverse_hours']} adverse hour(s))."]
        tl += [f"- {x['hour']:02d}:00 actual {fmt_num(x['actual'])} vs baseline {fmt_num(x['baseline'])}"
               for x in t.get("hourly") or [] if (x.get("actual") or 0) or (x.get("baseline") or 0)]
        S.append(("7. Time-of-degradation analysis", tl))
    else:
        S.append(("7. Time-of-degradation analysis", [
            "No sustained adverse period was identified." if dd.get("status") == "deterioration_found" else
            "Not applicable — no deterioration was detected."]))

    pend = next((m for m in metrics if m["metric_id"] == "pending_orders"), None)
    if pend and pend.get("status") == "ok":
        bl = [_metric_line(pend)[2:], pend.get("note") or ""]
        for x in (pend.get("by_warehouse") or [])[:8]:
            bl.append(f"- {x['key']}: {fmt_num(x.get('actual'))} vs {fmt_num(x.get('baseline'))} "
                      f"({fmt_pct(x.get('pct_diff'))})")
        if pend.get("current_status_breakdown"):
            bl.append("Current pending orders by status (snapshot, no historical comparison): " + ", ".join(
                f"{s['status']} {fmt_num(s['orders'])}" for s in pend["current_status_breakdown"]))
        S.append(("8. Pending/backlog impact", [x for x in bl if x]))
    else:
        S.append(("8. Pending/backlog impact", [pend.get("reason") if pend else next(
            (u["reason"] for u in r.get("unavailable") or [] if u["metric_id"] == "pending_orders"),
            "Pending orders could not be analysed.")]))

    items = ((r.get("evidence") or {}).get("internal") or {}).get("items") or []
    ev = [f"[{KIND_LABEL[i['kind']]}] {i['statement']}" for i in items]
    S.append(("9. Evidence-based internal findings", ev or ["No findings."]))

    lim = list(r.get("limitations") or [])
    lim += [u["reason"] for u in r.get("unavailable") or []]
    S.append(("10. Data limitations", lim))
    S.append(("11. Recommended areas for investigation", dd.get("recommendations") or [
        "No action is indicated by the available data."]))

    inv = r.get("investigation") or {}
    if inv.get("checks"):
        sc = inv.get("scope") or {}
        il = [f"Scope: {('warehouse ' + sc['warehouse']) if sc.get('warehouse') else 'all warehouses'}, "
              f"{sc.get('date')} {sc.get('window_label') or ''}, compared with the same hours on "
              f"{', '.join(sc.get('comparable_dates') or [])}."]
        il += [f"- [{CHECK_TEXT[c['status']]}] {c['hypothesis_title']}: {c['statement']}" for c in inv["checks"]]
        il += [f"Source: {s['name']} {s['table']} ({', '.join(s['columns'])})." for s in inv.get("sources") or []]
        il += list(inv.get("notes") or [])
        S.append(("12. Root-cause investigation", il))
    else:
        S.append(("12. Root-cause investigation", [inv.get("reason") or "Not run - no deterioration was detected."
                                                   if inv.get("status") in (None, "not_needed") else
                                                   "The investigation could not be completed."]))

    dg = r.get("diagnosis") or {}
    dl = [dg["summary"]] if dg.get("summary") else []
    for c in dg.get("likely_causes") or []:
        dl.append(f"{c['rank']}. {c['title']} - confidence {c['confidence']}, accounts for about "
                  f"{c['explains_pct']}% of the decline.")
        dl += [f"- Evidence: {e}" for e in c["evidence"]]
        dl += [f"- Action: {a}" for a in c["actions"]]
        if c.get("note"):
            dl.append(f"- Note: {c['note']}")
    for c in dg.get("other_findings") or []:
        dl.append(f"- Also seen: {c['title']} ({c['evidence'][0]})")
    if dg.get("likely_causes") is not None and dg.get("status") not in (None, "not_needed"):
        dl.append("Likely causes are strong patterns in the warehouse's own records for the same hours, not proof; "
                  "causes the system does not record (equipment not logged, trucks, power) cannot be seen.")
    S.append(("13. Likely causes and recommended actions", dl or ["Not applicable - no deterioration was detected."]))

    ag = r.get("agents") or []
    S.append(("14. How the agents worked", [f"- {a['name']} ({a['job'].lower()}): {a['status']}, "
                                            f"{a['duration_seconds']}s - {a['output']}" for a in ag]
              or ["Agent trace not available."]))
    return S


CHECK_TEXT = {"supported": "Found", "ruled_out": "Ruled out", "not_checked": "Not checked"}


def render_text(report):
    out = [report["title"], f"Generated: {report['generated_at']}   Report ID: {report['report_id']}", ""]
    for title, lines in sections(report):
        out.append(title)
        out += [f"  {line}" for line in lines]
        out.append("")
    out.append("Data sources: " + "; ".join(f"{s['kind']}: {s['table']}" for s in report["result"].get(
        "data_sources") or []) + ". Read-only analysis of this workspace's own database; no data was modified.")
    return "\n".join(out)


def render_html(report, include_executive=True):
    """Full report page: the management summary with charts first (images embedded as
    data: URIs), then the 11 technical sections."""
    e = html.escape
    parts = []
    if include_executive:
        try:
            from .exec_report import build_executive
            ex = build_executive(report, inline=False)["html"]
            start = ex.index('<table role="presentation" width="640"')
            end = ex.rindex("</table></td></tr></table>")
            parts.append("<div style='margin:0 auto 28px;max-width:640px'>" + ex[start:end] + "</table></div>")
        except Exception:  # noqa: BLE001 — the technical report must still render
            pass
        parts.append("<h1 style='border-top:1px solid #e2e8f0;padding-top:18px'>Technical details</h1>")
    parts += [f"<h1>{e(report['title'])}</h1>",
              f"<p style='color:#555'>Generated {e(str(report['generated_at']))} · Report {e(report['report_id'])}</p>"]
    for title, lines in sections(report):
        parts.append(f"<h2>{e(title)}</h2>")
        bullets = [l for l in lines if l.startswith("- ")]
        paras = [l for l in lines if not l.startswith("- ")]
        parts += [f"<p>{e(p)}</p>" for p in paras]
        if bullets:
            parts.append("<ul>" + "".join(f"<li>{e(b[2:])}</li>" for b in bullets) + "</ul>")
    parts.append("<p style='color:#555;font-size:12px'>Read-only analysis of this workspace's own warehouse "
                 "database. No data was modified. No external data was used.</p>")
    return ("<!doctype html><html><head><meta charset='utf-8'><title>" + e(report["title"]) + "</title>"
            "<style>body{font-family:Segoe UI,Arial,sans-serif;max-width:900px;margin:24px auto;padding:0 16px;"
            "color:#1a202c}h1{font-size:22px}h2{font-size:16px;margin-top:22px;border-bottom:1px solid #e2e8f0;"
            "padding-bottom:4px}li{margin:3px 0}</style></head><body>" + "".join(parts) + "</body></html>")


def csv_rows(report):
    rows = [["metric", "status", "actual", "baseline", "abs_diff", "pct_diff", "z_score", "classification",
             "baseline_method", "comparable_periods", "source_table"]]
    for m in report["result"].get("metrics") or []:
        rows.append([m.get("label"), m.get("status"), m.get("actual"), m.get("baseline"), m.get("abs_diff"),
                     m.get("pct_diff"), m.get("z_score"), m.get("classification"), m.get("baseline_method"),
                     m.get("n_comparable"), m.get("source_table")])
    return rows


def csv_dicts(report):
    """Rows in the shape the app's _send_email / _rows_to_csv expects (list of dicts)."""
    header, *rows = csv_rows(report)
    return [dict(zip(header, r)) for r in rows]

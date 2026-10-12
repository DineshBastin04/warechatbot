"""
Executive (management) version of a report: plain English, a clear status,
KPI tiles, the likely causes and what to do (from the Advisor agent), three
charts, and what was ruled out — built only from the structured analysis
result (no new numbers).

build_executive(report, inline=True) returns
  {"subject", "text", "html", "images": [(content_id, png_bytes, alt)], "status"}
inline=True  -> images referenced as cid:<id> (email; sent as inline attachments)
inline=False -> images embedded as data: URIs (the browser "Full report")

Email-safe HTML: table layout, inline styles, 640px, no scripts, no external
resources. Every chart is also described in words, so the email reads fine even
when images are blocked.
"""
import base64
import html
import re
from datetime import date

from . import charts

STATUS = {
    "significant_deterioration": ("Needs attention", "#d03b3b", "⚠"),
    "deterioration": ("Watch closely", "#c98500", "⚠"),
    "normal_variation": ("All normal", "#0ca30c", "✓"),
    "improvement": ("Better than normal", "#0ca30c", "✓"),
    "insufficient_data": ("Not enough history yet", "#76756f", "○"),
}
PLAIN = {
    "units_moved": "Units moved", "transactions": "Warehouse transactions", "orders_received": "New orders",
    "orders_picked": "Orders picked", "orders_packed": "Orders packed", "orders_loaded": "Orders loaded",
    "orders_dispatched": "Orders shipped", "orders_completed": "Orders completed",
    "pending_orders": "Orders waiting to ship", "processing_time": "Average time to ship",
}
STEP = {"dispatch": "shipping", "picking": "picking", "packing": "packing", "loading": "loading",
        "completion": "completion"}
KPI_ORDER = ("orders_dispatched", "orders_picked", "pending_orders", "units_moved", "orders_received",
             "transactions", "processing_time")
ADVERSE = ("deterioration", "significant_deterioration")
INK, INK_2, INK_3, LINE, BG = "#1a1a19", "#52514e", "#76756f", "#e7e6e2", "#f5f5f3"


def _e(v):
    return html.escape(str(v if v is not None else ""))


def _num(v, unit=""):
    if v is None:
        return "n/a"
    v = float(v)
    if unit == "minutes":
        h, m = divmod(int(round(v)), 60)
        return f"{h} h {m:02d} min" if h else f"{m} min"
    return f"{v:,.0f}" if abs(v) >= 10 or v.is_integer() else f"{v:,.1f}"


def _pct(p):
    return "n/a" if p is None else f"{abs(p):.0f}%"


def _state(m):
    c = m.get("classification")
    if c in ADVERSE:
        return "worse"
    if c == "improvement":
        return "better"
    return "normal"


def _signed(p):
    p = round(p)
    return f"{'+' if p > 0 else '−' if p < 0 else ''}{abs(p)}%"


def _clean_name(n):
    """'Picking (pick) (301)' -> 'Picking': transaction codes mean nothing to a reader."""
    n = re.sub(r"\s*\(\d+\)\s*$", "", str(n or ""))
    m = re.match(r"^(\S+)\s*\(([^)]+)\)$", n)
    if m and m.group(1).lower().startswith(m.group(2).lower()):
        n = m.group(1)
    return n[:1].upper() + n[1:]


RED_RULE = ("Red means a bigger change than this number shows on normal days (the same weekday over the last five "
            "weeks); grey means normal ups and downs; blue means better than normal.")


def _bar_row(x, name, unit=None):
    u = "min" if unit == "minutes" else None
    fmt = lambda v: "n/a" if v is None else (_num(v) + (f" {u}" if u else ""))
    return {"name": name, "pct": x.get("pct_diff"), "state": _state(x),
            "today": fmt(x.get("actual")), "normal": fmt(x.get("baseline"))}


def _versus(m):
    """'20% below normal' / '78% above normal' / 'in line with normal'."""
    p = m.get("pct_diff")
    if p is None:
        return "no comparison yet"
    if abs(p) < 1:
        return "in line with normal"
    return f"{abs(p):.0f}% {'below' if p < 0 else 'above'} normal"


def _metrics(result):
    return {m["metric_id"]: m for m in result.get("metrics") or []}


def _plain(result):
    """Plain names; "Units moved" becomes "Units picked" when only picking types are counted."""
    names = dict(PLAIN)
    if any("picking transaction types only" in str(x) for x in result.get("limitations") or []):
        names["units_moved"] = "Units picked"
    return names


def diagnosis(result):
    d = result.get("diagnosis") or {}
    return d if d.get("status") in ("cause_found", "narrowed_down", "no_internal_cause", "investigation_failed") \
        else None


def recommendations(result):
    """Management actions: the Advisor's (cause-specific) when an investigation ran,
    otherwise built from the facts (warehouse, step, time, backlog)."""
    dd = result.get("drilldown") or {}
    h = dd.get("headline_metric")
    if not h:
        return ["No action needed. The agent keeps checking every hour and will email if something changes."]
    d = diagnosis(result)
    if d and d.get("actions"):
        return list(d["actions"]) + ["You will get another email only if the problem changes or a new one appears."]
    ms = _metrics(result)
    wh = (dd.get("warehouse") or {}).get("name")
    p = dd.get("process") or {}
    step = STEP.get(p.get("primary"), p.get("primary")) if p.get("primary") else         _plain(result).get(h["metric_id"], h["label"]).lower()
    t = dd.get("time_window") or {}
    where = f" in warehouse {wh}" if wh else ""
    recs = [f"Ask the{(' ' + wh) if wh else ''} team what changed in {step}"
            + (f" from about {t['start']}" if t.get("start") else "") + " (staffing, equipment, system or stock issues)."]
    pend = ms.get("pending_orders")
    if pend and pend.get("status") == "ok" and pend.get("classification") in ADVERSE:
        row = next((x for x in pend.get("by_warehouse") or [] if x.get("key") == wh), None) if wh else None
        n, b = (row.get("actual"), row.get("baseline")) if row else (pend.get("actual"), pend.get("baseline"))
        recs.append(f"Plan to clear the backlog{where}: {_num(n)} orders are waiting to ship (normally {_num(b)}).")
    for dim in (dd.get("dimensions") or [])[:1]:
        top = (dim.get("top") or [None])[0]
        if top and top.get("share_of_shortfall_pct"):
            recs.append(f"Check {dim['dimension']} “{top['name']}” first{where}; it accounts for "
                        f"{top['share_of_shortfall_pct']:.0f}% of the shortfall.")
    if any(w for w in result.get("freshness_warnings") or []):
        recs.append("Confirm the warehouse system is still recording activity; recent hours have no records at all.")
    recs.append("You will get another email only if the problem changes or a new one appears.")
    return recs


def _weekday(result):
    try:
        return date.fromisoformat((result.get("period") or {}).get("date")).strftime("%A")
    except (TypeError, ValueError):
        return None


def _period_phrase(result):
    p = result.get("period") or {}
    if p.get("type") == "today_so_far":
        return f"today up to {p.get('end')}"
    return f"on {p.get('date')}"


def headline(result):
    dd = result.get("drilldown") or {}
    h = dd.get("headline_metric")
    if result.get("status") != "ok":
        return result.get("message") or "The analysis could not be completed."
    if not h:
        return "All warehouse measures are within their normal range " + _period_phrase(result) + "."
    m = _metrics(result).get(h["metric_id"], h)
    where = ((dd.get("warehouse") or {}).get("name"))
    text = f"{_plain(result).get(h['metric_id'], h['label'])} {'are' if h['metric_id'] != 'processing_time' else 'is'} " \
           f"{_versus(m)} {_period_phrase(result)}"
    if where:
        text += f", mostly in warehouse {where}" if (dd.get("warehouse") or {}).get("concentrated") else \
            f", with the largest share in warehouse {where}"
    return text + "."


def summary_points(result):
    dd = result.get("drilldown") or {}
    ms = _metrics(result)
    h = dd.get("headline_metric")
    pts = []
    if result.get("status") != "ok":
        return [result.get("message") or "No analysis could be completed."]
    wd = _weekday(result)
    normal_for = f"a normal {wd}" if wd else "a normal day"
    if not h:
        pts.append(f"Every measure the agent can read is within its usual range for {normal_for} at this time.")
        for m in (result.get("changes") or [])[:3]:
            pts.append(f"{_plain(result).get(m['metric_id'], m['label'])}: {_num(m['actual'], m['unit'])} "
                       f"(normally {_num(m['baseline'], m['unit'])}).")
        return pts
    m = ms.get(h["metric_id"], h)
    pts.append(f"{_plain(result).get(h['metric_id'], h['label'])}: {_num(m.get('actual'), m.get('unit'))} "
               f"{_period_phrase(result)}, against {_num(m.get('baseline'), m.get('unit'))} on {normal_for} "
               f"at this time ({_versus(m)}).")
    w = dd.get("warehouse") or {}
    if w.get("name"):
        others = [x for x in w.get("comparison") or [] if x["name"] != w["name"]]
        fine = [x["name"] for x in others if x.get("classification") not in ADVERSE]
        share = w.get("share_of_shortfall_pct")
        line = f"The shortfall is in warehouse {w['name']}" + (f" ({share:.0f}% of it)" if share else "") + "."
        if fine:
            line += f" {', '.join(fine)} {'is' if len(fine) == 1 else 'are'} running normally."
        pts.append(line)
    p = dd.get("process") or {}
    comp = [x for x in p.get("comparison") or [] if x.get("pct_diff") is not None]
    if comp and p.get("kind") == "order stage":
        parts = [f"{STEP.get(x['name'], x['name'])} {_pct(x['pct_diff'])} {'down' if x['pct_diff'] < 0 else 'up'}"
                 for x in comp[:2]]
        pts.append((f"In {w['name']}, " if w.get("name") else "") + " and ".join(parts) + ".")
    t = dd.get("time_window")
    if t:
        pts.append(f"It started around {t['start']}" + (" and is still going on." if t.get("ongoing")
                                                         else f" and lasted until {t['end']}."))
    d = diagnosis(result)
    if d and d.get("likely_causes"):
        top = d["likely_causes"][0]
        pts.append(("Most likely cause: " if d["status"] == "cause_found" else "Narrowed down to: ")
                   + top["title"][0].lower() + top["title"][1:] + ".")
    elif d and d.get("status") == "no_internal_cause":
        pts.append("No cause shows in the warehouse records (staffing, errors, stock and demand are normal).")
    rec = ms.get("orders_received")
    if rec and rec.get("status") == "ok" and h["metric_id"] != "orders_received":
        if rec.get("classification") == "below_normal":
            pts.append(f"New orders are also lower than normal ({_versus(rec)}), which may explain part of it.")
        elif rec.get("classification") in ("normal_variation", "above_normal"):
            pts.append("New orders are coming in as normal, so this is not a drop in demand.")
    pend = ms.get("pending_orders")
    if pend and pend.get("status") == "ok" and pend.get("classification") in ADVERSE and h["metric_id"] != "pending_orders":
        pts.append(f"Orders are piling up: {_num(pend.get('actual'))} waiting to ship, normally "
                   f"{_num(pend.get('baseline'))}.")
    return pts


CONF_WORD = {"High": "likely - strong evidence", "Medium": "likely", "Low": "possible"}
CONF_COLOUR = {"High": "#d03b3b", "Medium": "#c98500", "Low": "#76756f"}


def unknown_text(result):
    dd = result.get("drilldown") or {}
    if not dd.get("headline_metric"):
        return ""
    wh = (dd.get("warehouse") or {}).get("name")
    team = f"the {wh} team" if wh else "the team"
    d = diagnosis(result)
    if d and d.get("status") in ("cause_found", "narrowed_down", "no_internal_cause"):
        gaps = "; ".join(x["statement"] for x in d.get("not_checked") or [])
        return ("The causes above are strong patterns in the warehouse's own records, not proof - please confirm "
                f"them with {team}. Things the system does not record (equipment faults that were not logged, late "
                "trucks, power) cannot be seen." + (f" Could not be checked: {gaps}" if gaps else ""))
    return ("The data shows what changed, where and when - it cannot show why. Please check with "
            f"{team} what happened operationally.")


def why_section_html(d):
    """'Why it happened' block: one card per likely cause with its evidence."""
    if d.get("likely_causes"):
        cards = []
        for c in d["likely_causes"]:
            ev = "".join(f"<li style='margin:3px 0;font-size:13px;color:{INK_2}'>{_e(e)}</li>" for e in c["evidence"][:4])
            cards.append(
                f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:8px 0;'
                f'border:1px solid {LINE};border-left:5px solid {CONF_COLOUR[c["confidence"]]};border-radius:6px">'
                f'<tr><td style="padding:10px 14px"><div style="font-size:12px;color:{INK_3};text-transform:uppercase;'
                f'letter-spacing:.05em">#{c["rank"]} &middot; {_e(CONF_WORD[c["confidence"]])} &middot; about '
                f'{c["explains_pct"]}% of the drop</div>'
                f'<div style="font-size:15px;font-weight:700;color:{INK};margin:3px 0 4px">{_e(c["title"])}</div>'
                f'<ul style="margin:4px 0 0;padding-left:18px">{ev}</ul>'
                + (f'<div style="font-size:12px;color:{INK_3};margin-top:4px">{_e(c["note"])}</div>' if c.get("note") else "")
                + "</td></tr></table>")
        intro = ("The Investigator agent compared staffing, work per person, system exceptions, stock problems and "
                 "incoming orders with the same hours on normal days." if d["status"] == "cause_found" else d["summary"])
        body = f'<div style="font-size:13px;color:{INK_2};margin:4px 0 2px">{_e(intro)}</div>' + "".join(cards)
    else:
        body = f'<div style="font-size:14px;color:{INK};margin-top:6px">{_e(d.get("summary") or "")}</div>'
    return (f'<tr><td style="padding:18px 24px 0"><div style="font-size:16px;font-weight:700;color:{INK}">'
            f'Why it happened</div>{body}</td></tr>')


def _kpis(result):
    ms = _metrics(result)
    out = []
    for mid in KPI_ORDER:
        m = ms.get(mid)
        if m and m.get("status") == "ok" and m.get("actual") is not None:
            out.append(m)
        if len(out) == 4:
            break
    return out


def _chart_specs(result):
    """[(content_id, png, title, answer, note, alt)] - each chart leads with a one-sentence answer, so a reader
    who looks at nothing else still gets the point; the note says how to read the picture."""
    dd = result.get("drilldown") or {}
    ms = _metrics(result)
    h = dd.get("headline_metric")
    day = f"a normal {_weekday(result)}" if _weekday(result) else "a normal day"
    specs = []
    if h:
        label = _plain(result).get(h["metric_id"], h["label"])
        what = label.lower()
        t = dd.get("time_window") or {}
        hourly = t.get("hourly") or (ms.get(h["metric_id"]) or {}).get("hourly")
        if hourly:
            start = int(t["start"][:2]) if t.get("start") else None
            minutes = h.get("unit") == "minutes"
            png = charts.hourly_chart(hourly, start, y_title=f"{label} (minutes)" if minutes else f"{label} per hour")
            if png:
                scope = f" in warehouse {t['scope']}" if t.get("scope") else ""
                if start is not None:
                    ans = f"It started around {t['start']}" + (" and is still going on." if t.get("ongoing", True)
                                                               else f" and lasted until {t.get('end')}.")
                    after = [p for p in hourly if p["hour"] >= start and p.get("baseline")]
                    a = sum(p.get("actual") or 0 for p in after)
                    b = sum(p.get("baseline") or 0 for p in after)
                    if minutes and after:              # an average time: compare the averages
                        a, b = a / len(after), b / len(after)
                        ans += (f" Since then: {_num(a, 'minutes')} on average{scope}, against about "
                                f"{_num(b, 'minutes')} on {day} ({_signed((a - b) / b * 100)}).")
                    elif b and not a:
                        ans += f" Since then nothing has been recorded{scope} - normally about {_num(b)} by now."
                    elif b:
                        ans += (f" Since then: {_num(a)} {what}{scope}, against about {_num(b)} on {day} "
                                f"({_signed((a - b) / b * 100)}).")
                else:
                    ans = f"Today hour by hour{scope}, against {day}."
                note = (f"Blue columns are today, the dark line is {day} at the same hour"
                        + (f"; the shaded part is the problem period from {t['start']}." if start is not None else "."))
                specs.append(("wpa-when", png, "When did it start?", ans, note,
                              f"Hourly {what}{scope}: today vs normal"))
        w = dd.get("warehouse") or {}
        rows = [_bar_row(x, x["name"]) for x in w.get("comparison") or []]
        if rows:
            png = charts.change_bars(rows, y_title="Warehouse")
            if png:
                bad = [r for r in rows if r["state"] == "worse"]
                share = w.get("share_of_shortfall_pct")
                part = f" ({share:.0f}% of the problem)" if share is not None else ""
                if not w.get("name"):
                    ans = "The drop is spread across the warehouses - no single site stands out."
                elif len(bad) > 1 and len(bad) == len(rows):
                    ans = f"All warehouses are affected; {w['name']} has the biggest part{part}."
                elif len(bad) > 1:
                    ans = f"{len(bad)} warehouses are affected, mostly {w['name']}{part}."
                else:
                    ans = f"Mainly in warehouse {w['name']}{part}."
                specs.append(("wpa-where", png, "Where is the problem?", ans,
                              f"Each bar shows how far {what} is from normal in one warehouse. " + RED_RULE,
                              f"{label} by warehouse, % vs normal"))
        p = dd.get("process") or {}
        rows = [_bar_row(x, STEP.get(x["name"], x["name"]).capitalize() if p.get("kind") == "order stage"
                         else _clean_name(x["name"])) for x in p.get("comparison") or []]
        if rows:
            png = charts.change_bars(rows, y_title="Step")
            if png:
                scope = f" in {p['scope']}" if p.get("scope") else ""
                bad = [r for r in rows if r["state"] == "worse"]
                if len(bad) > 1:
                    ans = (f"Steps hit hardest{scope}: " +
                           " and ".join(f"{r['name']} ({_signed(r['pct'])})" for r in bad[:2]) + ".")
                elif bad:
                    ans = f"The {bad[0]['name']} step is hit hardest{scope} ({_signed(bad[0]['pct'])})."
                else:
                    ans = (f"No step is clearly worse than normal{scope}; the biggest change, {rows[0]['name']} "
                           f"({_signed(rows[0]['pct'])}), is within normal ups and downs.")
                specs.append(("wpa-step", png, "Which step is affected?", ans,
                              "Each bar is one step of the work, compared with a normal day. " + RED_RULE,
                              f"Process steps{scope}, % vs normal"))
    else:
        rows = [_bar_row(c, _plain(result).get(c["metric_id"], c["label"]), c.get("unit"))
                for c in result.get("changes") or [] if c.get("pct_diff") is not None][:7]
        if rows:
            png = charts.change_bars(rows, y_title="Measure")
            if png:
                bad = sum(r["state"] == "worse" for r in rows)
                ans = (f"{bad} of {len(rows)} measures are worse than normal." if bad else
                       f"All {len(rows)} measures are within normal ups and downs.")
                specs.append(("wpa-overview", png, "How today compares with normal", ans,
                              f"Each bar compares one measure with {day} at this time. " + RED_RULE,
                              "All measures, % vs normal"))
    seen = False                                         # explain the colours once, under the first bar chart
    for i, (cid, png, title, ans, note, alt) in enumerate(specs):
        if RED_RULE in note:
            specs[i] = (cid, png, title, ans, note.replace(" " + RED_RULE, "") if seen else note, alt)
            seen = True
    return specs


# Shown at the top and bottom of every email and Word report: readers must know this is machine-made.
AI_NOTICE = ("AI-generated report: these results were produced automatically by AI agents and may be right or "
             "wrong. Please check them with the operations team before acting on them.")
AI_DISCLAIMER = ("Disclaimer: this report was generated by AI agents from the warehouse records. The findings, the "
                 "likely causes and the suggested actions are the agents' best assessment, not a confirmed diagnosis, "
                 "and they can be wrong or incomplete. Verify anything important before making a decision.")


def build_executive(report, inline=True):
    r = report["result"]
    ov = r.get("overall") or {}
    cls = ov.get("classification") if r.get("status") == "ok" else "insufficient_data"
    status, colour, icon = STATUS.get(cls, STATUS["insufficient_data"])
    ws = report.get("workspace_name") or ""
    period = (r.get("period") or {}).get("label") or ""
    head = headline(r)
    points = summary_points(r)
    recs = recommendations(r) if r.get("status") == "ok" else []
    specs = _chart_specs(r) if r.get("status") == "ok" else []
    alert = cls in ADVERSE
    dd = r.get("drilldown") or {}
    subject_core = head.rstrip(".")
    subject = (f"Warehouse alert - {ws}: {subject_core}" if alert else f"Warehouse update - {ws}: {subject_core}")[:200]

    def img_src(cid, png):
        return f"cid:{cid}" if inline else "data:image/png;base64," + base64.b64encode(png).decode("ascii")

    tiles = []
    for m in _kpis(r):
        st = _state(m)
        tone = {"worse": "#d03b3b", "better": "#0ca30c", "normal": "#b9b7b0"}[st]
        word = {"worse": "Worse than normal", "better": "Better than normal", "normal": "Normal"}[st]
        arrow = "▼" if (m.get("pct_diff") or 0) < 0 else "▲" if (m.get("pct_diff") or 0) > 0 else "■"
        tiles.append(
            f'<td width="25%" valign="top" style="padding:6px">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#fff;'
            f'border:1px solid {LINE};border-top:4px solid {tone};border-radius:6px"><tr><td style="padding:10px 12px">'
            f'<div style="font-size:12px;color:{INK_2}">{_e(_plain(r).get(m["metric_id"], m["label"]))}</div>'
            f'<div style="font-size:24px;font-weight:700;color:{INK};margin:4px 0 2px">{_e(_num(m.get("actual"), m.get("unit")))}</div>'
            f'<div style="font-size:12px;color:{INK_3}">normal {_e(_num(m.get("baseline"), m.get("unit")))}</div>'
            f'<div style="font-size:12px;color:{INK};font-weight:600;margin-top:6px">{arrow} {_e(_pct(m.get("pct_diff")))} '
            f'&middot; {_e(word)}</div></td></tr></table></td>')
    tiles_html = ("<table role='presentation' width='100%' cellpadding='0' cellspacing='0'><tr>" + "".join(tiles) +
                  "</tr></table>") if tiles else ""

    chart_html = "".join(
        f'<tr><td style="padding:18px 24px 4px"><div style="font-size:13px;font-weight:700;color:{INK_3};'
        f'text-transform:uppercase;letter-spacing:.04em">{_e(title)}</div>'
        f'<div style="font-size:16px;font-weight:700;color:{INK};line-height:1.4;margin:4px 0 2px">{_e(ans)}</div>'
        f'<div style="font-size:12.5px;color:{INK_2};margin:0 0 8px;line-height:1.45">{_e(note)}</div>'
        f'<img src="{img_src(cid, png)}" width="600" alt="{_e(alt)}" style="display:block;width:100%;max-width:600px;'
        f'height:auto;border:1px solid {LINE};border-radius:6px"></td></tr>'
        for cid, png, title, ans, note, alt in specs)

    def ul(items):
        return "<ul style='margin:6px 0 0;padding-left:20px'>" + "".join(
            f"<li style='margin:5px 0;font-size:14px;color:{INK}'>{_e(x)}</li>" for x in items) + "</ul>"

    unknown = unknown_text(r)
    fresh = [w["message"] for w in r.get("freshness_warnings") or []]
    diag = diagnosis(r) if r.get("status") == "ok" else None
    why_html = why_section_html(diag) if diag else ""

    body = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head><body style="margin:0;padding:0;background:{BG}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG}"><tr><td align="center" style="padding:20px 10px">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:100%;max-width:640px;background:#ffffff;border:1px solid {LINE};border-radius:8px;font-family:Segoe UI,Arial,sans-serif">
<tr><td style="padding:20px 24px 8px"><div style="font-size:12px;color:{INK_3};text-transform:uppercase;letter-spacing:.06em">Warehouse Performance &middot; {_e(ws)}</div>
<div style="font-size:13px;color:{INK_3};margin-top:2px">{_e(period)}</div></td></tr>
<tr><td style="padding:6px 24px 14px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-left:6px solid {colour};background:#fafaf8;border-radius:4px"><tr><td style="padding:12px 16px">
<div style="font-size:13px;font-weight:700;color:{INK}">{icon} {_e(status)}</div>
<div style="font-size:19px;font-weight:700;color:{INK};line-height:1.35;margin-top:4px">{_e(head)}</div></td></tr></table></td></tr>
<tr><td style="padding:0 24px 14px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#fff8e6;border:1px solid #f0d49a;border-radius:4px"><tr><td style="padding:8px 12px;font-size:12.5px;color:{INK};line-height:1.45">
&#9432; <b>AI-generated report:</b> {_e(AI_NOTICE.split(": ", 1)[1])}</td></tr></table></td></tr>
<tr><td style="padding:0 24px"><div style="font-size:16px;font-weight:700;color:{INK}">In short</div>{ul(points)}</td></tr>
{('<tr><td style="padding:14px 18px 0">' + tiles_html + '</td></tr>') if tiles_html else ''}
{why_html}
{('<tr><td style="padding:18px 24px 0"><div style="font-size:16px;font-weight:700;color:' + INK + '">What to do now</div>' + ul(recs) + '</td></tr>') if recs else ''}
{chart_html}
{('<tr><td style="padding:14px 24px 0"><div style="font-size:16px;font-weight:700;color:' + INK + '">Checked and ruled out</div>' + ul([x["statement"] for x in (diag or {}).get("ruled_out") or []][:8]) + '</td></tr>') if (diag or {}).get("ruled_out") else ''}
{('<tr><td style="padding:14px 24px 0"><div style="font-size:16px;font-weight:700;color:' + INK + '">What we don&#39;t know yet</div>' + ul([unknown] + fresh) + '</td></tr>') if (unknown or fresh) else ''}
<tr><td style="padding:20px 24px 22px"><div style="border-top:1px solid {LINE};padding-top:12px;font-size:12px;color:{INK_3};line-height:1.5">
&ldquo;Normal&rdquo; means the same weekday over the previous five weeks, over the same hours. A change is flagged only when it is well outside the usual day-to-day variation.
This report was produced automatically by three agents (Monitor: what changed; Investigator: checked the possible causes in the warehouse records; Advisor: ranked them and wrote the actions) &mdash; report {_e(report.get("report_id"))}. They only read the warehouse database and change nothing.
The full report (Word document) and the data (CSV) are attached.
<div style="margin-top:8px;color:{INK_2}"><b>Disclaimer:</b> {_e(AI_DISCLAIMER.split(": ", 1)[1])}</div></div></td></tr>
</table></td></tr></table></body></html>"""

    why_text = []
    if diag and diag.get("likely_causes"):
        why_text = ["", "Why it happened:"]
        for c in diag["likely_causes"]:
            why_text.append(f"{c['rank']}. {c['title']} ({CONF_WORD[c['confidence']]})")
            why_text += [f"   - {e}" for e in c["evidence"][:3]]
    elif diag and diag.get("summary"):
        why_text = ["", "Why it happened:", diag["summary"]]
    text = "\n".join([f"{status.upper()}: {head}", period, "", AI_NOTICE, "", "In short:"] + [f"- {p}" for p in points]
                     + why_text
                     + ([""] + ["What to do now:"] + [f"- {x}" for x in recs] if recs else [])
                     + ([""] + ["Checked and ruled out:"] + [f"- {x['statement']}" for x in diag["ruled_out"][:8]]
                        if (diag or {}).get("ruled_out") else [])
                     + ([""] + [unknown] if unknown else [])
                     + ["", "The full report (Word document) and the data (CSV) are attached.", "", AI_DISCLAIMER, "",
                        f"Warehouse Performance Agent - report {report.get('report_id')}"])
    return {"subject": subject, "text": text, "html": body, "status": status, "alert": alert,
            "images": [(cid, png, alt) for cid, png, _t, _a, _n, alt in specs]}

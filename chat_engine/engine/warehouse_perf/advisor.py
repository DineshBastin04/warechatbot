"""
Agent 3 of 3 — the Advisor: "what is the most likely cause, and what should we do?"

Input: ONLY the Monitor's case file and the Investigator's checks. The Advisor has
no database access and computes no new measurements; every number it writes comes
from a check. It is deterministic (no LLM), so the same evidence always gives the
same advice.

How it reasons:
  * A volume decline in an activity is split into "fewer people" and "less work
    per person" (Investigator: share_of_decline). Fewer people -> a staffing cause.
  * Less work per person needs an explanation: exception spikes, stock problems
    (short picks, denials) or rework found in the same hours are attached to the
    biggest such slowdown. With no recorded explanation it stays an open slowdown
    ("the system records no reason").
  * Fewer incoming orders, bigger orders and a stopped data feed are causes in
    their own right.
  * Each cause gets an impact (how much of the decline it accounts for, 0-1) and a
    confidence (High / Medium / Low) from the impact and how far outside normal
    variation its evidence is. Causes are ranked by impact.
  * Everything checked and found normal is listed as ruled out; everything that
    could not be checked is listed with the reason. When nothing is supported, the
    Advisor says so plainly: the cause is outside what the system records.

The wording is "likely cause": the evidence is a strong pattern in the warehouse's
own records, confirmed by the team on the floor, not a proof.
"""
import math

from . import analytics as A
from .discovery import split_tokens
from .drilldown import fmt_num
from .investigator import NOT_CHECKED, RULED_OUT, SUPPORTED

HIGH, MEDIUM, LOW = "High", "Medium", "Low"
MAX_CAUSES = 3
EXPLANATIONS = ("exceptions", "stock", "rework")


def _strong(c):
    if c.get("classification") == A.SIGNIFICANT:
        return True
    z, p = c.get("z_score"), c.get("pct_diff")
    return z is None and p is not None and abs(p) >= 20 or (z is None and (c.get("baseline") or 0) == 0)


def _confidence(impact, strong):
    if impact >= 0.4 and strong:
        return HIGH
    if impact >= 0.2 or strong:
        return MEDIUM
    return LOW


def _plain(name):
    """'Load (203)' -> 'Load'; activity descriptions read better without the code in actions."""
    s = str(name or "")
    return s[:s.rfind(" (")] if s.endswith(")") and " (" in s else s


def _step(name):
    """'Load (203)' -> 'the Load step' (activity descriptions are nouns or verbs; this reads either way)."""
    return f"the {_plain(name)} step"


_GENERIC = {"the", "of", "and", "a", "to", "in", "step", "close", "closed", "error", "errors", "exception",
            "exceptions", "override", "report", "by", "user"}


def _words(name):
    return set(split_tokens(_plain(name))) - _GENERIC


def _people(n):
    return "person" if n == 1 else "people"


class _Advisor:
    def __init__(self, case, inv):
        self.case = case
        self.inv = inv
        self.checks = inv.get("checks") or []
        self.wh = case.get("warehouse")
        scope = inv.get("scope") or {}
        self.window = scope.get("window_label") or "in the problem hours"
        self.start = scope["from"] if scope.get("from") and scope["from"] != "00:00" else None
        self.since = f"since {self.start}" if self.start else "today"
        self.where = f" in {self.wh}" if self.wh else ""
        self.causes = []

    def by(self, hyp, status=SUPPORTED):
        return [c for c in self.checks if c["hypothesis"] == hyp and c["status"] == status]

    def add(self, cid, kind, title, impact, strong, evidence, actions, note=None, checks=()):
        self.causes.append({"id": cid, "kind": kind, "title": title, "impact": round(max(0.0, min(1.0, impact)), 2),
                            "explains_pct": round(max(0.0, min(1.0, impact)) * 100),
                            "confidence": _confidence(impact, strong), "evidence": evidence, "actions": actions,
                            "note": note, "check_ids": [c["id"] for c in checks]})

    # ------------------------------------------------------------- causes
    def data_feed(self):
        for c in self.by("data_feed"):
            self.add("data_feed", "data_feed", "The warehouse system stopped recording activity", 1.0, True,
                     [c["statement"]],
                     ["Check that the warehouse system and its interfaces are running and still saving transactions."],
                     note="Until records arrive again, the other figures for the most recent hours are incomplete.",
                     checks=[c])

    def demand(self):
        for c in self.by("demand"):
            h = self.case
            share = 0.5
            a, b = c.get("actual"), c.get("baseline")
            if a and b and a < b and h.get("actual") and h.get("baseline") and h["actual"] < h["baseline"]:
                share = math.log(a / b) / math.log(max(h["actual"], h["baseline"] * 0.01) / h["baseline"])
            self.add("demand", "demand", f"Fewer orders came in{self.where}", share, _strong(c), [c["statement"]],
                     [f"No warehouse fix is needed for this part: {fmt_num(a)} orders came in {self.window} "
                      f"(normally {fmt_num(b)}). Consider moving people to other work or to a busier warehouse."],
                     checks=[c])

    def activity(self):
        """Staffing and per-person slowdowns per activity type, with explanations attached."""
        rows = {r.get("code"): r for r in self.inv.get("activity") or []}
        explanations = [c for h in EXPLANATIONS for c in self.by(h)]
        slowdowns = self.by("productivity")
        # Exceptions that no measured slowdown accounts for may mean people were present but held up
        # (not recording work) rather than absent: say so on the staffing cause.
        held_up = not slowdowns and any(x["hypothesis"] == "exceptions" for x in explanations)
        slow = []
        for c in self.by("staffing"):
            if c["id"] == "staffing:all":           # overall headcount: see staffing_overall()
                continue
            row = rows.get(c["activity"]) or {}
            weight = row.get("shortfall_share") or 0
            impact = weight * (c.get("share_of_decline") or 0)
            if impact <= 0 and weight == 0:
                impact = 0.1
            a, b = c.get("actual") or 0, c.get("baseline") or 0
            gap = max(1, math.ceil(b - a - 1e-9))
            name = c["subject"]
            others = self.case.get("other_warehouses_normal") or []
            actions = [f"Put {gap} more {_people(gap)} on {_step(name)}{self.where} now: only {fmt_num(a)} "
                       f"{_people(round(a))} {'per hour ' if 'hour' in (c.get('unit') or '') else ''}have been doing it "
                       f"{self.since} (normally {fmt_num(b)})."]
            if others:
                actions.append(f"{', '.join(others)} {'is' if len(others) == 1 else 'are'} running normally and may "
                               f"be able to lend people.")
            actions.append(f"Check absences, breaks and shift changes{self.where}"
                           + (f" around {self.start}." if self.start else " today."))
            evidence = [c["statement"]] + ([c["volume"]] if c.get("volume") else [])
            note = ("Exceptions were also logged in these hours: some people may be present but held up, rather "
                    "than absent.") if held_up else None
            self.add(f"staffing:{c['activity']}", "staffing", f"Not enough people on {_step(name)}{self.where}",
                     impact, _strong(c), evidence, actions, note=note, checks=[c])
        for c in slowdowns:
            row = rows.get(c["activity"]) or {}
            weight = row.get("shortfall_share") or 0
            slow.append((weight * (c.get("share_of_decline") or 0) or 0.1 * weight or 0.05, c))
        slow.sort(key=lambda x: -x[0])
        # Each explanation goes to the slowdown it names (e.g. "Short Pick Close" -> a Pick slowdown),
        # otherwise to the biggest slowdown in the same hours.
        attached = {}
        for x in explanations:
            if not slow:
                break
            named = [c for _i, c in slow if _words(c["subject"]) & _words(x["subject"])]
            attached.setdefault((named[0] if named else slow[0][1])["id"], []).append(x)
        used = {x["id"] for xs in attached.values() for x in xs}
        for impact, c in slow:
            name = c["subject"]
            pct = abs(c.get("pct_diff") or 0)
            base = [c["statement"]] + ([c["volume"]] if c.get("volume") else [])
            if attached.get(c["id"]):
                exps = sorted(attached[c["id"]], key=lambda x: (-(x.get("actual") or 0) + (x.get("baseline") or 0)))
                self._explained_slowdown(c, name, impact, base, exps)
            else:
                step = _step(name)
                self.add(f"productivity:{c['activity']}", "productivity",
                         f"{step[0].upper() + step[1:]}{self.where} is slower per person, with no recorded reason",
                         impact, _strong(c), base,
                         [f"{step[0].upper() + step[1:]}{self.where} is about {pct:.0f}% slower per person with the "
                          f"same number of people. The system records no reason: check equipment (scanners, printers, "
                          f"forklifts), system speed and pick locations with the team."], checks=[c])
        for x in explanations:              # spikes with no slowdown to attach to: contributing factors
            if x["id"] in used:
                continue
            self._explanation_alone(x)

    def _explained_slowdown(self, c, name, impact, base, exps):
        top = exps[0]
        kind = top["hypothesis"]
        what = {"exceptions": f"'{_plain(top['subject'])}' exceptions",
                "stock": f"stock problems ({_plain(top['subject'])})",
                "rework": f"work being undone ({_plain(top['subject'])})"}[kind]
        title = f"{what[0].upper() + what[1:]} slowing {_step(name)}{self.where}"
        evidence = base + [x["statement"] for x in exps]
        actions = [self._fix(x) for x in exps[:3]]
        actions.append(f"Until it is fixed, expect {_step(name)}{self.where} to stay about "
                       f"{abs(c.get('pct_diff') or 0):.0f}% slower per person.")
        self.add(f"{kind}:{top['id']}", kind, title, impact, _strong(c) and _strong(top), evidence, actions,
                 checks=[c] + exps)

    def _explanation_alone(self, x):
        kind = x["hypothesis"]
        title = {"exceptions": f"More '{_plain(x['subject'])}' exceptions than normal{self.where}",
                 "stock": f"Stock problems{self.where}: {_plain(x['subject'])}",
                 "rework": f"Work being undone{self.where}: {_plain(x['subject'])}"}[kind]
        self.add(x["id"], kind, title, 0.15, _strong(x), [x["statement"]], [self._fix(x)],
                 note="Seen in the same hours, but not linked to a measured slowdown.", checks=[x])

    def _fix(self, x):
        a, b = fmt_num(x.get("actual")), fmt_num(x.get("baseline"))
        label = _plain(x["subject"])
        if x["hypothesis"] == "exceptions":
            return (f"Get the '{label}' problem fixed (IT / system support): it was logged {a} times{self.where} "
                    f"{self.since}, normally {b}.")
        if x["hypothesis"] == "stock":
            items = ", ".join(i["item"] for i in x.get("items") or [])
            return (f"Check stock{self.where}" + (f" for these items: {items}" if items else "")
                    + f". {a} '{label}' {self.since} (normally {b}); replenish the pick locations or correct the "
                      f"stock records.")
        return f"Find out why work is being undone{self.where}: {a} '{label}' {self.since} (normally {b})."

    def order_size(self):
        for c in self.by("order_size"):
            self.add("order_size", "order_size", "Orders are bigger than usual", 0.3, _strong(c), [c["statement"]],
                     [f"Orders are bigger than usual ({fmt_num(c.get('actual'))} units per order, normally "
                      f"{fmt_num(c.get('baseline'))}). Add people to picking if this continues."], checks=[c])

    def staffing_overall(self):
        """Fewer people overall, when no single activity type showed it."""
        if any(c["kind"] == "staffing" for c in self.causes):
            return
        for c in self.by("staffing"):
            if c["id"] != "staffing:all":
                continue
            a, b = c.get("actual") or 0, c.get("baseline") or 0
            gap = max(1, math.ceil(b - a - 1e-9))
            self.add("staffing:all", "staffing", f"Fewer people working{self.where}", 0.3, _strong(c),
                     [c["statement"]],
                     [f"About {gap} fewer {_people(gap)} are recording work{self.where} than normal; check "
                      f"absences, breaks and shift changes."], checks=[c])


def _ruled_out(checks):
    out, seen = [], set()
    for c in checks:
        if c["status"] != RULED_OUT:
            continue
        key = (c["hypothesis"], c["statement"])
        if key in seen:
            continue
        seen.add(key)
        out.append({"hypothesis": c["hypothesis"], "title": c["hypothesis_title"], "statement": c["statement"]})
    return out


def _not_checked(checks):
    return [{"hypothesis": c["hypothesis"], "title": c["hypothesis_title"], "statement": c["statement"]}
            for c in checks if c["status"] == NOT_CHECKED]


def advise(case, investigation):
    """-> diagnosis dict. Never raises on well-formed input."""
    empty = {"likely_causes": [], "other_findings": [], "ruled_out": [], "not_checked": [], "actions": []}
    if not case:
        return {"status": "not_needed", "summary": None, **empty}
    inv = investigation or {}
    if inv.get("status") in ("failed", "not_needed") and not inv.get("checks"):
        return {"status": "investigation_failed",
                "summary": "The possible causes could not be checked this time: "
                           + "; ".join(inv.get("notes") or ["the investigation did not complete"]) + ".",
                **empty, "actions": ["Ask the team what changed in the affected warehouse and hours."]}
    adv = _Advisor(case, inv)
    adv.data_feed()
    adv.demand()
    adv.activity()
    adv.order_size()
    adv.staffing_overall()
    rank = {HIGH: 0, MEDIUM: 1, LOW: 2}
    causes = sorted(adv.causes, key=lambda c: (-c["impact"], rank[c["confidence"]]))
    for i, c in enumerate(causes, 1):
        c["rank"] = i
    likely, other = causes[:MAX_CAUSES], causes[MAX_CAUSES:]
    ruled, unchecked = _ruled_out(adv.checks), _not_checked(adv.checks)

    found = {c["hypothesis"] for c in adv.checks if c["status"] == SUPPORTED}
    normal = sorted({r["title"].lower() for r in ruled if r["hypothesis"] not in found})
    team = f"the {adv.wh} team" if adv.wh else "the team"

    def lower(t):
        return t[0].lower() + t[1:]

    causes = [c for c in likely if c["kind"] != "productivity"]
    unexplained = "; ".join(lower(c["title"]).replace(", with no recorded reason", "")
                            for c in likely if c["kind"] == "productivity")
    checked = (" Checked and normal: " + ", ".join(normal) + ".") if normal else ""
    if likely and likely[0]["kind"] == "productivity":
        # The biggest part of the drop has no recorded reason: say exactly that, first.
        status = "narrowed_down"
        summary = (("No recorded cause was found, but the problem is narrowed down: " if not causes else
                    "No recorded cause explains most of it, but the problem is narrowed down: ") + unexplained + "."
                   + (" Also found: " + "; ".join(lower(c["title"]) for c in causes) + "." if causes else "")
                   + checked
                   + f" The reason is something the system does not record (equipment, system speed, a process "
                     f"change); {team} will know.")
    elif likely:
        status = "cause_found"
        summary = f"Most likely cause: {lower(causes[0]['title'])}"
        if len(causes) > 1:
            summary += "; also " + "; ".join(lower(c["title"]) for c in causes[1:])
        summary += "." + (f" Not explained by the records: {unexplained}." if unexplained else "") + checked
    if likely:
        actions = []
        for c in likely:
            for a in c["actions"]:
                if a not in actions:
                    actions.append(a)
    else:
        status = "no_internal_cause"
        summary = ("No cause was found in the warehouse records: "
                   + (", ".join(normal) if normal else "nothing could be checked")
                   + (" - all normal" if normal else "")
                   + f". The cause is probably something the system does not record (for example an equipment "
                     f"breakdown that was not logged, late trucks or a power problem); {team} will know.")
        actions = [f"Ask {team} what happened {adv.since}: the warehouse records show no staffing, stock, error or "
                   f"demand change that explains it."]
    pend = (case.get("facts") or {}).get("pending_orders")
    if pend and pend.get("classification") in A.ADVERSE:
        actions.append(f"Plan to clear the backlog{adv.where}: {fmt_num(pend.get('actual'))} orders are waiting "
                       f"(normally {fmt_num(pend.get('baseline'))}).")
    return {"status": status, "summary": summary, "likely_causes": likely, "other_findings": other,
            "ruled_out": ruled, "not_checked": unchecked, "actions": actions,
            "explained_pct": round(min(1.0, sum(c["impact"] for c in likely)) * 100)}

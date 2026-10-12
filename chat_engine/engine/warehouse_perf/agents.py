"""
The three agents and how work passes between them.

  1. Monitor       analyzer.py + drilldown.py   what changed, where and when
         |  result["handoff"]: the case file (measure, warehouse, hours, normal days)
  2. Investigator  investigator.py              checks every possible cause in the records
         |  investigation["checks"]: supported / ruled out / not checked, with numbers
  3. Advisor       advisor.py                   ranks the likely causes, rules the rest out,
                                                and writes the actions

Each agent does one job with a narrow input, so none of them has to hold the whole
problem at once: the Investigator never sees the Monitor's working data, and the
Advisor never touches the database. A failure in a later agent never loses the
earlier agents' work: the report still goes out with what was found, and says
which agent could not finish.
"""
import logging
import time

from .advisor import advise
from .analyzer import analyze
from .investigator import investigate
from .workspace_context import scrub_text

logger = logging.getLogger(__name__)

AGENTS = (
    ("monitor", "Monitor", "Finds what changed, where and when"),
    ("investigator", "Investigator", "Checks the possible causes in the warehouse records"),
    ("advisor", "Advisor", "Ranks the likely causes and recommends actions"),
)


def _trace(key, status, started, output):
    name, job = next((n, j) for k, n, j in AGENTS if k == key)
    return {"agent": key, "name": name, "job": job, "status": status, "output": output,
            "duration_seconds": round(time.time() - started, 2)}


def run_agents(workspace_public, model, data, now, settings=None):
    """Monitor -> Investigator -> Advisor for one workspace. The Monitor's errors
    propagate (as before); the Investigator and Advisor never stop the report."""
    t = time.time()
    result = analyze(workspace_public, model, data, now, settings)
    dd = result.get("drilldown") or {}
    trace = [_trace("monitor", "ok" if result.get("status") == "ok" else result.get("status"), t,
                    dd.get("conclusion") or result.get("message") or "")]
    case = result.get("handoff")

    t = time.time()
    investigation = investigate(case, model, data)
    s = investigation.get("summary") or {}
    trace.append(_trace("investigator", investigation["status"], t,
                        "Not needed: nothing deteriorated." if investigation["status"] == "not_needed" else
                        f"{len(investigation.get('checks') or [])} checks: {s.get('supported', 0)} supported, "
                        f"{s.get('ruled_out', 0)} ruled out, {s.get('not_checked', 0)} could not be checked."))

    t = time.time()
    try:
        diagnosis = advise(case, investigation)
        status = "ok" if diagnosis["status"] != "not_needed" else "not_needed"
    except Exception as exc:  # noqa: BLE001 — the report still goes out with the Monitor's findings
        logger.exception("warehouse_perf: advisor failed")
        diagnosis = {"status": "advisor_failed", "summary": None, "likely_causes": [], "other_findings": [],
                     "ruled_out": [], "not_checked": [], "actions": [],
                     "error": scrub_text(f"{type(exc).__name__}: {exc}")}
        status = "failed"
    trace.append(_trace("advisor", status, t, diagnosis.get("summary") or "Not needed: nothing deteriorated."))

    result["investigation"] = investigation
    result["diagnosis"] = diagnosis
    result["agents"] = trace
    return result

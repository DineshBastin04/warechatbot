"""The three agents: Monitor -> Investigator -> Advisor (root causes and actions)."""
import unittest
from datetime import datetime

import pandas as pd

from tests.warehouse_perf.helpers import (NOW, WS_A, WS_B, FakeNarrator, make_flask, make_service, tables, user)
from engine.warehouse_perf.advisor import advise
from engine.warehouse_perf.discovery import MODEL_VERSION
from engine.warehouse_perf.exec_report import build_executive
from engine.warehouse_perf.investigator import investigate, problem_category
from engine.warehouse_perf.synthetic import TABLE_TYPES, SyntheticDatabase


def run(cause="mixed", tbl=None, types=None, data_kw=None, **kw):
    t = tbl if tbl is not None else tables(cause=cause)
    dbs = {"srv-alpha": SyntheticDatabase(t, types=types),
           "srv-beta": SyntheticDatabase(tables(degrade=False, seed=11))}
    svc, sender, store, factory, coll = make_service(dbs=dbs, data_kw=data_kw, **kw)
    rec = svc.run_analysis(WS_A, trigger="manual")
    return rec, store.get_report(WS_A, rec["report_id"]), sender, factory, svc


def check(result, cid):
    return next(c for c in result["investigation"]["checks"] if c["id"] == cid)


def without_table(name):
    return {k: v for k, v in TABLE_TYPES.items() if k != name}


def without_column(table, column):
    return {k: ({c: t for c, t in v.items() if c != column} if k == table else v) for k, v in TABLE_TYPES.items()}


class Discovery(unittest.TestCase):
    def test_finds_people_items_and_the_exception_log(self):
        _rec, report, *_ = run()

        model = report["result"]
        src = {s["kind"]: s for s in model["data_sources"]}
        self.assertEqual(src["activity"]["table"], "dbo.t_tran_log")
        inv = model["investigation"]
        tables_read = {s["table"]: s["columns"] for s in inv["sources"]}
        self.assertIn("employee_id", tables_read["dbo.t_tran_log"])
        self.assertEqual(tables_read["dbo.t_exception_log"],
                         ["exception_date", "exception_time", "wh_id", "tran_type", "description"])

    def test_old_cached_model_is_rescanned(self):
        rec, _report, _sender, _factory, svc = run()
        cached = svc.store.get_catalog(WS_A)
        self.assertEqual(cached["model_version"], MODEL_VERSION)
        cached["model_version"] = 1
        svc.store.save_catalog(WS_A, cached)
        self.assertEqual(svc.run_analysis(WS_A)["discovery"], "discovered")
        self.assertEqual(svc.run_analysis(WS_A)["discovery"], "cached")

    def test_problem_categories_from_descriptions(self):
        self.assertEqual(problem_category("Short Pick Close"), "stock")
        self.assertEqual(problem_category("Full Floor Denial"), "stock")
        self.assertEqual(problem_category("Inventory Adjustment by Item"), "stock")
        self.assertEqual(problem_category("Dir Move Itm not available"), "stock")
        self.assertEqual(problem_category("Unload/Unpick (pick)"), "rework")
        self.assertIsNone(problem_category("Picking (pick)"))
        self.assertIsNone(problem_category("Label Printer Communication Error"))


class PlantedCauses(unittest.TestCase):
    """WH-B from 09:00: one loader missing, and label-printer errors on every lost shipment."""

    @classmethod
    def setUpClass(cls):
        cls.rec, cls.report, cls.sender, cls.factory, cls.svc = run("mixed")
        cls.r = cls.report["result"]
        cls.d = cls.r["diagnosis"]

    def test_monitor_hands_over_a_case_file(self):
        h = self.r["handoff"]
        self.assertEqual((h["metric_id"], h["warehouse"]), ("orders_dispatched", "WH-B"))
        self.assertEqual((h["start_hour"], h["end_hour"]), (9, 13))
        self.assertEqual(len(h["comparable_dates"]), 5)
        self.assertEqual(h["other_warehouses_normal"], ["WH-A", "WH-C"])

    def test_investigator_finds_the_planted_causes_and_rules_out_the_rest(self):
        self.assertEqual(check(self.r, "staffing:203")["status"], "supported")          # one loader missing
        self.assertEqual((check(self.r, "staffing:203")["actual"], check(self.r, "staffing:203")["baseline"]),
                         (3.0, 4.0))
        self.assertEqual(check(self.r, "productivity:203")["status"], "ruled_out")      # the others work normally
        self.assertEqual(check(self.r, "staffing:204")["status"], "ruled_out")          # shippers all there ...
        self.assertEqual(check(self.r, "productivity:204")["status"], "supported")      # ... but ship less each
        exc = check(self.r, "exceptions:317")
        self.assertEqual(exc["status"], "supported")
        self.assertEqual(exc["baseline"], 0)
        self.assertGreaterEqual(exc["actual"], 10)
        for cid in ("stock:376", "demand:orders_received", "order_size:units_per_order", "data_feed:freshness"):
            self.assertEqual(check(self.r, cid)["status"], "ruled_out", cid)
        self.assertEqual(check(self.r, "rework:none")["status"], "not_checked")

    def test_advisor_ranks_causes_with_specific_actions(self):
        self.assertEqual(self.d["status"], "cause_found")
        first, second = self.d["likely_causes"][:2]
        self.assertEqual(first["kind"], "exceptions")
        self.assertIn("Label Printer Communication Error", first["title"])
        self.assertIn("Ship step in WH-B", first["title"])
        self.assertEqual(first["confidence"], "High")
        self.assertEqual(second["kind"], "staffing")
        self.assertEqual(second["title"], "Not enough people on the Load step in WH-B")
        self.assertGreater(first["impact"], second["impact"])
        acts = " ".join(self.d["actions"])
        self.assertIn("Get the 'Label Printer Communication Error' problem fixed", acts)
        self.assertIn("Put 1 more person on the Load step in WH-B now", acts)
        self.assertIn("WH-A, WH-C are running normally and may be able to lend people", acts)
        self.assertIn("Plan to clear the backlog in WH-B", acts)
        self.assertTrue(self.d["summary"].startswith("Most likely cause: 'Label Printer Communication Error'"))
        self.assertIn("fewer orders coming in", self.d["summary"])          # ruled out, named

    def test_every_number_in_the_advice_comes_from_a_check(self):
        import re
        nums = set()
        for c in self.r["investigation"]["checks"]:
            for k in ("actual", "baseline", "pct_diff"):
                if c.get(k) is not None:
                    nums.update({round(abs(c[k]), 1), round(abs(c[k])), round(abs(c[k]) + 0.4999)})
        f = (self.r["handoff"]["facts"] or {}).get("pending_orders") or {}
        nums.update({f.get("actual"), f.get("baseline")})
        for cause in self.d["likely_causes"]:
            for text in cause["actions"] + [cause["title"]]:
                for tok in re.findall(r"(?<![\w(])\d+(?:\.\d+)?(?!\))", re.sub(r"\d{2}:\d{2}|\(\d+\)", "", text)):
                    v = float(tok)
                    self.assertTrue(v in nums or v == 1, f"{tok} in {text!r}")

    def test_agent_trace(self):
        self.assertEqual([a["name"] for a in self.r["agents"]], ["Monitor", "Investigator", "Advisor"])
        self.assertEqual([a["status"] for a in self.r["agents"]], ["ok", "done", "ok"])
        self.assertIn("checks:", self.r["agents"][1]["output"])
        self.assertEqual(self.rec["investigation"], "done")
        self.assertEqual(len(self.rec["likely_causes"]), 2)

    def test_investigator_sql_is_generated_read_only_and_one_day_at_a_time(self):
        data = [d for ws, d in self.factory.instances if ws == WS_A][0]
        inv_sql = [s for s in data.sql_seen if "[employee_id]" in s or "t_exception_log" in s]
        self.assertTrue(inv_sql)
        self.assertTrue(all(s.lstrip().upper().startswith("SELECT") for s in inv_sql))
        self.assertTrue(any("COUNT(DISTINCT [employee_id]) AS [q]" in s for s in inv_sql))
        labels = [q["label"] for q in data.query_log if str(q.get("label")).startswith("investigator:")]
        # problem day + 5 comparable days per breakdown, plus one exception-type lookup
        self.assertEqual(labels.count("investigator: activity and people by type"), 6)
        self.assertEqual(labels.count("investigator: exceptions by type"), 6)

    def test_email_word_and_dashboard_lead_with_the_cause(self):
        call = self.sender.calls[0]
        self.assertIn("Why it happened", call["html"])
        self.assertIn("Label Printer Communication Error", call["html"])
        self.assertIn("Most likely cause:", call["body"])
        from tests.warehouse_perf.helpers import docx_text
        doc = docx_text(call["extra_attachments"][0][2])
        self.assertLess(doc.index("Why it happened"), doc.index("When did it start?"))
        self.assertIn("Put 1 more person on the Load step in WH-B", doc)
        dash = self.svc.dashboard(WS_A, include_admin=True)["report"]
        self.assertEqual(dash["diagnosis"]["status"], "cause_found")
        self.assertEqual([a["name"] for a in dash["agents"]], ["Monitor", "Investigator", "Advisor"])


class NothingRecorded(unittest.TestCase):
    def test_same_decline_with_no_recorded_cause_is_narrowed_down_honestly(self):
        _rec, report, *_ = run("none")
        d = report["result"]["diagnosis"]
        self.assertEqual(d["status"], "narrowed_down")
        self.assertTrue(all(c["kind"] == "productivity" for c in d["likely_causes"]))
        self.assertTrue(d["summary"].startswith("No recorded cause was found, but the problem is narrowed down"))
        self.assertIn("fewer people working", d["summary"])               # checked and normal
        self.assertIn("the WH-B team will know", d["summary"])
        self.assertNotIn("Most likely cause", d["summary"])

    def test_no_supported_check_at_all(self):
        case = {"warehouse": "WH-B", "facts": {}}
        inv = {"status": "done", "scope": {"from": "09:00"}, "activity": [], "checks": [
            {"id": "staffing:all", "hypothesis": "staffing", "hypothesis_title": "Fewer people working",
             "status": "ruled_out", "statement": "People recording work: 16 (normally 16)."},
            {"id": "exceptions:all", "hypothesis": "exceptions", "status": "ruled_out", "statement": "x",
             "hypothesis_title": "Exceptions logged by the warehouse system"}]}
        d = advise(case, inv)
        self.assertEqual(d["status"], "no_internal_cause")
        self.assertIn("No cause was found in the warehouse records", d["summary"])
        self.assertIn("something the system does not record", d["summary"])
        self.assertEqual(d["actions"][0][:20], "Ask the WH-B team wh")


class StockProblems(unittest.TestCase):
    def test_short_pick_spike_names_the_items(self):
        t = tables(cause="none")
        extra = []
        for i in range(14):
            ts = datetime(NOW.year, NOW.month, NOW.day, 10 + i % 3, 5 * i % 60)
            extra.append({"tran_log_id": 10 ** 7 + i, "tran_type": "376", "description": "Short Pick Close",
                          "start_tran_date": pd.Timestamp(ts.date()), "start_tran_time": pd.Timestamp(1900, 1, 1, ts.hour, ts.minute),
                          "wh_id": "WH-B", "item_number": "ITEM0007" if i % 3 else "ITEM0042", "tran_qty": 0,
                          "employee_id": "B201-0", "location_id": "LOC001"})
        t["dbo.t_tran_log"] = pd.concat([t["dbo.t_tran_log"], pd.DataFrame(extra)], ignore_index=True)
        _rec, report, *_ = run(tbl=t)
        r = report["result"]
        c = check(r, "stock:376")
        self.assertEqual(c["status"], "supported")
        self.assertEqual([i["item"] for i in c["items"]], ["ITEM0007", "ITEM0042"])
        d = r["diagnosis"]
        stock = next(x for x in d["likely_causes"] if x["kind"] == "stock")
        self.assertIn("Short Pick Close", stock["title"])
        self.assertTrue(any("Check stock in WH-B for these items: ITEM0007, ITEM0042" in a for a in stock["actions"]))


class MissingEvidence(unittest.TestCase):
    def test_no_exception_log(self):
        _rec, report, *_ = run(types=without_table("dbo.t_exception_log"))
        c = check(report["result"], "exceptions:none")
        self.assertEqual(c["status"], "not_checked")
        self.assertIn("No exception/error log was found", c["statement"])
        self.assertIn(c["statement"], [x["statement"] for x in report["result"]["diagnosis"]["not_checked"]])

    def test_exception_log_without_recent_records(self):
        t = tables(cause="none")
        old = t["dbo.t_exception_log"].copy()
        old["exception_date"] = pd.Timestamp("2025-08-13")
        t["dbo.t_exception_log"] = old
        _rec, report, *_ = run(tbl=t)
        c = check(report["result"], "exceptions:stale")
        self.assertEqual(c["status"], "not_checked")
        self.assertIn("has no recent records (latest 2025-08-13)", c["statement"])

    def test_no_employee_column(self):
        _rec, report, *_ = run(types=without_column("dbo.t_tran_log", "employee_id"))
        r = report["result"]
        self.assertEqual(check(r, "staffing:none")["status"], "not_checked")
        self.assertEqual(check(r, "productivity:none")["status"], "not_checked")
        self.assertEqual(check(r, "exceptions:317")["status"], "supported")             # other checks still run
        self.assertEqual(r["diagnosis"]["likely_causes"][0]["kind"], "exceptions")


class Isolation(unittest.TestCase):
    def test_investigator_failure_never_stops_the_report_or_the_email(self):
        rec, report, sender, *_ = run(data_kw={"srv-alpha": {"fail_labels": ["investigator"]}})
        r = report["result"]
        self.assertEqual(rec["status"], "ok")
        self.assertEqual(r["investigation"]["status"], "partial")
        self.assertTrue(any("could not be read" in n for n in r["investigation"]["notes"]))
        self.assertIn(r["drilldown"]["headline_metric"]["metric_id"], ("orders_dispatched",))
        self.assertEqual(len(sender.calls), 1)                                           # the alert still went out
        self.assertEqual(r["agents"][1]["status"], "partial")

    def test_no_deterioration_means_no_investigation(self):
        svc, sender, store, *_ = make_service()
        rec = svc.run_analysis(WS_B)
        r = store.get_report(WS_B, rec["report_id"])["result"]
        self.assertIsNone(r["handoff"])
        self.assertEqual(r["investigation"]["status"], "not_needed")
        self.assertEqual(r["diagnosis"]["status"], "not_needed")
        self.assertEqual([a["status"] for a in r["agents"]], ["ok", "not_needed", "not_needed"])
        ex = build_executive(store.get_report(WS_B, rec["report_id"]))
        self.assertNotIn("Why it happened", ex["html"])

    def test_llm_summary_still_cannot_state_a_cause(self):
        _rec, report, *_ = run(narrator=FakeNarrator(text="Dispatch fell because of the label printer."))
        self.assertNotEqual(report["summary_source"], "llm_validated")
        self.assertIn("Most likely cause:", report["executive_summary"])   # the Advisor's line, not the LLM's

    def test_dashboard_api_carries_the_diagnosis(self):
        svc = run()[4]
        client = make_flask(svc).test_client()
        res = client.get(f"/api/v0/warehouse_perf/dashboard?workspace_id={WS_A}",
                         headers={"X-Test-User": user("admin")}).get_json()
        rep = res["dashboard"]["report"]
        self.assertEqual(rep["diagnosis"]["likely_causes"][0]["kind"], "exceptions")
        self.assertEqual(rep["investigation"]["scope"]["warehouse"], "WH-B")

    def test_dashboard_chart_data(self):
        svc = run()[4]
        rep = svc.dashboard(WS_A)["report"]
        hourly = rep["charts"]["hourly"]
        self.assertEqual(hourly["title"], "Orders dispatched in warehouse WH-B per hour: today vs a normal day")
        self.assertEqual(hourly["start"], "09:00")
        self.assertEqual([p["hour"] for p in hourly["points"]], list(range(13)))
        labels = {c["id"]: c["label"] for c in rep["investigation"]["checks"]}
        self.assertEqual(labels["staffing:203"], "People on Load (203)")
        self.assertEqual(labels["productivity:204"], "Ship (204) per person")
        self.assertEqual(labels["demand:orders_received"], "Orders received")
        self.assertEqual(labels["staffing:all"], "People working (all activities)")

    def test_dashboard_chart_on_a_normal_day(self):
        svc, *_ = make_service()
        svc.run_analysis(WS_B)
        hourly = svc.dashboard(WS_B)["report"]["charts"]["hourly"]
        self.assertTrue(hourly["title"].endswith("per hour, all warehouses: today vs a normal day"))
        self.assertIsNone(hourly["start"])


if __name__ == "__main__":
    unittest.main()

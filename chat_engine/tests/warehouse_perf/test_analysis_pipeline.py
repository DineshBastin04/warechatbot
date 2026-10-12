"""End-to-end analysis on synthetic data: warehouse comparison, process-level
drill-down, time of degradation, insufficient data, freshness and date-only
timestamps (spec tests 4, 5, 6, 7, 8)."""
import copy
import unittest
from datetime import datetime, timedelta

from tests.warehouse_perf.helpers import NOW, WS_A, make_service, tables
from engine.warehouse_perf.synthetic import TABLE_TYPES, SyntheticDatabase


def run_on(tbls, types=None, now=NOW, **kw):
    dbs = {"srv-alpha": SyntheticDatabase(tbls, types), "srv-beta": SyntheticDatabase(tables(degrade=False))}
    svc, sender, store, factory, coll = make_service(dbs=dbs, now=now, **kw)
    rec = svc.run_analysis(WS_A)
    report = store.get_report(WS_A, rec["report_id"]) if rec.get("report_id") else None
    return rec, report, svc, sender, store


def types_without(*cols):
    t = copy.deepcopy(TABLE_TYPES)
    for c in cols:
        ref, col = c.rsplit(".", 1)
        t[ref].pop(col, None)
    return t


def metric(report, mid):
    return next(m for m in report["result"]["metrics"] if m["metric_id"] == mid)


class DegradedWarehouse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec, cls.report, *_ = run_on(tables())
        cls.r = cls.report["result"]
        cls.dd = cls.r["drilldown"]

    def test_run_record(self):
        self.assertEqual(self.rec["status"], "ok")
        self.assertEqual(self.rec["db_status"], "ok")
        self.assertIn("orders_dispatched", self.rec["anomalies"])
        self.assertTrue(self.rec["report_generated"])

    def test_period_is_today_equal_elapsed(self):
        self.assertEqual(self.r["period"]["type"], "today_so_far")
        self.assertEqual(self.r["period"]["elapsed_hours"], 13)
        m = metric(self.report, "orders_dispatched")
        self.assertEqual(m["baseline_method"], "same_weekday")
        self.assertEqual(m["n_comparable"], 5)
        self.assertTrue(all(datetime.fromisoformat(c["date"]).weekday() == NOW.weekday() for c in m["comparables"]))
        self.assertIn("previous_day", m)
        self.assertIn(m["trend"]["direction"], ("flat", "rising", "falling"))

    def test_dispatch_is_significant_and_headline(self):
        self.assertEqual(metric(self.report, "orders_dispatched")["classification"], "significant_deterioration")
        self.assertEqual(self.dd["headline_metric"]["metric_id"], "orders_dispatched")
        self.assertEqual(self.r["overall"]["classification"], "significant_deterioration")

    def test_warehouse_comparison_isolates_the_degraded_warehouse(self):
        w = self.dd["warehouse"]
        self.assertEqual(w["name"], "WH-B")
        self.assertTrue(w["concentrated"])
        self.assertGreater(w["share_of_shortfall_pct"], 80)
        others = {x["name"]: x for x in w["comparison"]}
        self.assertEqual(set(others), {"WH-A", "WH-B", "WH-C"})
        self.assertNotIn(others["WH-A"]["classification"], ("deterioration", "significant_deterioration"))

    def test_process_drill_down_points_at_dispatch(self):
        p = self.dd["process"]
        self.assertEqual((p["scope"], p["kind"], p["primary"]), ("WH-B", "order stage", "dispatch"))
        by = {x["name"]: x for x in p["comparison"]}
        self.assertLess(by["dispatch"]["pct_diff"], by["loading"]["pct_diff"])
        self.assertLess(by["loading"]["pct_diff"], -10)
        self.assertGreater(by["picking"]["pct_diff"], -6)
        self.assertEqual(p["comparison"][0]["name"], "dispatch")

    def test_time_of_degradation(self):
        t = self.dd["time_window"]
        self.assertEqual(t["scope"], "WH-B")
        self.assertIn(t["start"], ("09:00", "10:00"))
        self.assertTrue(t["ongoing"])

    def test_conclusion_never_asserts_a_cause(self):
        self.assertTrue(self.dd["conclusion"].startswith("The available warehouse data shows a significant dispatch "
                                                         "decline concentrated in warehouse WH-B"))
        self.assertTrue(self.dd["conclusion"].endswith("show what changed, where and when - not why; the possible "
                                                       "causes are checked separately against the warehouse records."))
        for word in ("because", "due to", "caused by", "likely cause"):
            self.assertNotIn(word, self.dd["conclusion"].lower())      # causes are the Advisor's job, not the Monitor's
        kinds = {i["kind"] for i in self.r["evidence"]["internal"]["items"]}
        self.assertTrue({"observed", "calculated", "anomaly", "unknown"} <= kinds)
        self.assertEqual(self.r["evidence"]["external"], [])

    def test_backlog_reflects_accumulation_as_inference(self):
        pend = metric(self.report, "pending_orders")
        self.assertIn(pend["classification"], ("deterioration", "significant_deterioration"))
        self.assertTrue(any("interpretation, not a verified cause" in c for c in self.dd["context"]))
        self.assertEqual(pend["by_warehouse"][0]["key"], "WH-B")     # worst first

    def test_units_moved_counts_only_pick_and_ship(self):
        units = metric(self.report, "units_moved")
        self.assertEqual({p["key"] for p in units["by_process"]}, {"Pick (201)"})
        trans = metric(self.report, "transactions")
        self.assertEqual({p["key"] for p in trans["by_process"]},
                         {"Pick (201)", "Pack (202)", "Load (203)", "Ship (204)", "Short Pick Close (376)"})
        self.assertTrue(any("picking transaction types only (Pick (201))" in x for x in self.r["limitations"]))

    def test_kpis_only_from_derived_metrics(self):
        k = self.r["kpis"]
        self.assertEqual(k["units_moved"]["metric_id"], "units_moved")
        self.assertEqual(k["orders_dispatched"]["metric_id"], "orders_dispatched")
        self.assertEqual(k["pending_orders"]["metric_id"], "pending_orders")

    def test_only_select_queries_were_issued(self):
        _, _, svc, _, _ = run_on(tables())
        data = svc._data_factory.instances[-1][1]
        self.assertTrue(data.sql_seen)
        self.assertTrue(all(s.startswith("SELECT ") for s in data.sql_seen))
        self.assertTrue(data.closed)


class HealthyWarehouse(unittest.TestCase):
    def test_no_deterioration_no_alert(self):
        rec, report, svc, sender, store = run_on(tables(degrade=False, seed=3))
        self.assertEqual(report["result"]["drilldown"]["status"], "no_deterioration")
        self.assertFalse(report["alert_worthy"])
        self.assertEqual(report["delivery"]["status"], "not_required")
        self.assertEqual(sender.calls, [])

    def test_drop_that_follows_lower_incoming_orders_is_not_a_deterioration(self):
        # seed 11: orders received happen to be ~6% below normal today; dispatch falls with them
        rec, report, svc, sender, store = run_on(tables(degrade=False, seed=11))
        r = report["result"]
        self.assertEqual(metric(report, "orders_received")["classification"], "below_normal")
        d = metric(report, "orders_dispatched")
        self.assertEqual(d["raw_classification"], "significant_deterioration")
        self.assertEqual(d["classification"], "normal_variation")
        self.assertIn(d["demand_adjusted"]["classification"], ("normal_variation", "improvement"))
        self.assertIn("orders received", d["basis"])
        self.assertTrue(r["demand_adjustments"])
        self.assertFalse(report["alert_worthy"])
        self.assertEqual(sender.calls, [])

    def test_real_degradation_is_not_explained_away_by_demand(self):
        rec, report, *_ = run_on(tables())
        self.assertNotIn("raw_classification", metric(report, "orders_dispatched"))


class InsufficientData(unittest.TestCase):
    def test_only_one_week_of_history(self):
        rec, report, *_ = run_on(tables(days=8))
        m = metric(report, "orders_dispatched")
        # same-weekday history is too short, so the recent-days fallback is used and labelled as such
        self.assertEqual((m["status"], m["baseline_method"]), ("ok", "recent_operating_days"))
        self.assertIn("recent operating days", m["baseline_method_text"])

    def test_only_two_days_of_history(self):
        rec, report, *_ = run_on(tables(days=2))
        m = metric(report, "orders_dispatched")
        self.assertEqual(m["status"], "insufficient_data")
        self.assertIsNone(m["baseline"])
        self.assertIn("At least 3 comparable periods are required", m["reason"])
        self.assertEqual(report["result"]["overall"]["classification"], "insufficient_data")
        self.assertFalse(report["alert_worthy"])

    def test_tables_exist_but_are_empty(self):
        empty = {k: v.iloc[0:0] for k, v in tables().items()}
        rec, report, *_ = run_on(empty)
        self.assertEqual(report["result"]["status"], "no_recent_data")
        self.assertIn("contain no records in the last 35 days", report["result"]["message"])

    def test_only_old_data_reports_how_old_it_is(self):
        old = tables(now=NOW - timedelta(days=120), days=30)
        rec, report, *_ = run_on(old)
        self.assertEqual(report["result"]["status"], "no_recent_data")
        self.assertIn("(latest record 2026-05-27)", report["result"]["message"])
        self.assertTrue(all("latest record 2026-05-27" in u["reason"] for u in report["result"]["unavailable"]
                            if u["metric_id"] in ("transactions", "orders_dispatched")))
        self.assertFalse(report["alert_worthy"])

    def test_no_warehouse_tables_at_all(self):
        rec, report, *_ = run_on({"dbo.t_item_master": tables()["dbo.t_item_master"]})
        self.assertEqual(report["result"]["status"], "no_metrics")
        self.assertIn("No usable operational data", report["result"]["message"])

    def test_nothing_derivable_is_never_shown_as_zero(self):
        t = {"dbo.t_item_master": tables()["dbo.t_item_master"]}
        rec, report, *_ = run_on(t)
        k = report["result"]["kpis"]
        self.assertIsNone(k["units_moved"])
        self.assertIsNone(k["orders_dispatched"])
        self.assertIsNone(k["overall"]["value"])


class BlankDimensions(unittest.TestCase):
    def test_blank_category_is_never_recommended(self):
        t = tables()
        t["dbo.t_order"]["order_category"] = None                 # like real test rows with no department
        rec, report, *_ = run_on(t)
        dims = report["result"]["drilldown"]["dimensions"]
        self.assertFalse(any(x["name"] == "(not recorded)" for d in dims for x in d["top"]))
        self.assertNotIn("(not recorded)", " ".join(report["result"]["drilldown"]["recommendations"]))


class TransactionTypeFallback(unittest.TestCase):
    def test_without_descriptions_raw_codes_and_all_types_are_used(self):
        rec, report, *_ = run_on(tables(), types=types_without("dbo.t_tran_log.description"))
        units = metric(report, "units_moved")
        self.assertEqual({p["key"] for p in units["by_process"]}, {"201", "202", "203", "204", "376"})
        self.assertTrue(any("may count the same unit more than once" in x for x in report["result"]["limitations"]))


class MissingColumnsEndToEnd(unittest.TestCase):
    def test_no_ship_date_still_analyses_the_rest(self):
        rec, report, *_ = run_on(tables(), types=types_without("dbo.t_order.ship_date"))
        ids = {m["metric_id"] for m in report["result"]["metrics"]}
        self.assertNotIn("orders_dispatched", ids)
        self.assertIn("orders_loaded", ids)
        self.assertTrue(any(u["reason"] == "Dispatch performance cannot be analysed because dispatch timestamps "
                                          "are unavailable." for u in report["result"]["unavailable"]))
        self.assertIsNone(report["result"]["kpis"]["orders_dispatched"])     # not derivable -> not shown

    def test_no_warehouse_column(self):
        rec, report, *_ = run_on(tables(), types=types_without("dbo.t_order.wh_id", "dbo.t_tran_log.wh_id"))
        self.assertTrue(all("by_warehouse" not in m for m in report["result"]["metrics"]))
        self.assertIn("No warehouse identifier was found", report["text"])

    def test_one_failing_query_does_not_stop_other_metrics(self):
        rec, report, *_ = run_on(tables(), data_kw={"srv-alpha": {"fail_labels": {"orders_loaded"}}})
        self.assertEqual(metric(report, "orders_loaded")["status"], "query_failed")
        self.assertEqual(metric(report, "orders_dispatched")["status"], "ok")
        self.assertEqual(rec["db_status"], "partial")

    def test_row_limit_truncation_is_not_analysed(self):
        rec, report, *_ = run_on(tables(), data_kw={"srv-alpha": {"row_limit": 100}})
        m = metric(report, "transactions")
        self.assertEqual(m["status"], "data_truncated")
        self.assertTrue(any("row limit" in x for x in report["result"]["limitations"]))


class FreshnessAndGranularity(unittest.TestCase):
    def test_feed_stopped_is_flagged_not_alerted(self):
        t = tables()
        cut = datetime(2026, 9, 24, 9, 0)
        o = t["dbo.t_order"]
        for c in ("order_date", "picked_date", "packed_date", "loaded_date", "ship_date"):
            o.loc[o[c] >= cut, c] = None
        t["dbo.t_order"] = o[o["order_date"].notna()]
        tl = t["dbo.t_tran_log"]
        full = tl["start_tran_date"] + (tl["start_tran_time"] - tl["start_tran_time"].dt.normalize())
        t["dbo.t_tran_log"] = tl[full < cut]
        rec, report, svc, sender, store = run_on(t)
        warnings = report["result"]["freshness_warnings"]
        self.assertTrue(warnings)
        self.assertIn("data-feed delay", warnings[0]["message"])
        self.assertFalse(report["alert_worthy"])
        self.assertEqual(sender.calls, [])

    def test_date_only_timestamps_use_previous_complete_day(self):
        t = tables()
        types = types_without("dbo.t_tran_log.start_tran_time")
        for c in ("order_date", "picked_date", "packed_date", "loaded_date", "ship_date"):
            t["dbo.t_order"][c] = t["dbo.t_order"][c].dt.normalize()
        rec, report, *_ = run_on(t, types=types)
        r = report["result"]
        self.assertEqual(r["period"]["type"], "previous_operating_day")
        self.assertEqual(r["period"]["date"], (NOW.date() - timedelta(days=1)).isoformat())
        self.assertTrue(any("dates without times" in n for n in r["discovery_notes"]))

    def test_early_morning_analyses_previous_operating_day(self):
        early = datetime(2026, 9, 24, 1, 15)
        rec, report, *_ = run_on(tables(), now=early)
        self.assertEqual(report["result"]["period"]["type"], "previous_operating_day")


if __name__ == "__main__":
    unittest.main()

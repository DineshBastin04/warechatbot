"""Report generation and LLM-narrative guardrails (spec test 12)."""
import json
import unittest

from tests.warehouse_perf.helpers import WS_A, FakeNarrator, make_service, tables
from engine.warehouse_perf.reporting import (csv_rows, render_html, render_text, sections, validate_narrative)
from engine.warehouse_perf.synthetic import SyntheticDatabase

SECTIONS = ["1. Executive summary", "2. Current performance", "3. Historical baseline", "4. Major deviations",
            "5. Warehouse-level comparison", "6. Process-level comparison", "7. Time-of-degradation analysis",
            "8. Pending/backlog impact", "9. Evidence-based internal findings", "10. Data limitations",
            "11. Recommended areas for investigation", "12. Root-cause investigation",
            "13. Likely causes and recommended actions", "14. How the agents worked"]


class Report(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svc, cls.sender, cls.store, *_ = make_service()
        rec = cls.svc.run_analysis(WS_A, trigger="manual")
        cls.report = cls.store.get_report(WS_A, rec["report_id"])

    def test_all_sections_in_order(self):
        self.assertEqual([t for t, _ in sections(self.report)], SECTIONS)
        text = render_text(self.report)
        positions = [text.index(s) for s in SECTIONS]
        self.assertEqual(positions, sorted(positions))

    def test_evidence_kinds_are_labelled_distinctly(self):
        text = render_text(self.report)
        for label in ("[Observed fact]", "[Calculated comparison]", "[Detected anomaly]",
                      "[Inferred interpretation]", "[Unknown / insufficient evidence]"):
            self.assertIn(label, text)

    def test_content(self):
        text = render_text(self.report)
        self.assertIn("WH-B", text)
        self.assertIn("same weekday", text)
        self.assertIn("show what changed, where and when - not why", text)
        self.assertIn("Most likely cause:", text)
        self.assertIn("[Ruled out]", text)
        self.assertIn("not proof", text)
        self.assertIn("No external data", text)
        self.assertNotIn("weather", text.split("10. Data limitations")[0].lower())

    def test_html_is_escaped(self):
        rep = json.loads(json.dumps(self.report))
        rep["executive_summary"] = "<script>alert(1)</script>"
        rep["result"]["drilldown"]["recommendations"] = ["<img src=x onerror=alert(1)>"]
        html = render_html(rep)
        self.assertNotIn("<script>alert", html)
        self.assertNotIn("<img src=x", html)
        self.assertIn("&lt;script&gt;", html)

    def test_csv_has_one_row_per_metric(self):
        rows = csv_rows(self.report)
        self.assertEqual(rows[0][0], "metric")
        self.assertEqual(len(rows) - 1, len(self.report["result"]["metrics"]))


class Narrative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        svc, _, store, *_ = make_service()
        rec = svc.run_analysis(WS_A, trigger="manual")
        cls.result = store.get_report(WS_A, rec["report_id"])["result"]
        h = cls.result["drilldown"]["headline_metric"]
        cls.good = (f"Orders dispatched were {h['actual']:.0f} against a baseline of {h['baseline']:.0f}. "
                    f"The decline is concentrated in warehouse WH-B and began around 09:00. The available data is "
                    f"insufficient to determine the underlying cause.")

    def test_accepts_numbers_from_the_findings(self):
        ok, reasons = validate_narrative(self.good, self.result)
        self.assertTrue(ok, reasons)

    def test_rejects_invented_numbers(self):
        ok, reasons = validate_narrative("Dispatch fell by 87.3% across 7 warehouses.", self.result)
        self.assertFalse(ok)
        self.assertTrue(any("87.3" in r for r in reasons))

    def test_rejects_causes_and_external_factors(self):
        self.assertFalse(validate_narrative("Dispatch fell due to staff shortages.", self.result)[0])
        self.assertFalse(validate_narrative("Heavy rain slowed the dispatch area.", self.result)[0])
        self.assertFalse(validate_narrative("Carriers arrived late at WH-B.", self.result)[0])
        self.assertFalse(validate_narrative("See https://example.com for details.", self.result)[0])

    def test_valid_llm_summary_is_used(self):
        narrator = FakeNarrator(text=self.good)
        svc, _, store, *_ = make_service(narrator=narrator)
        rec = svc.run_analysis(WS_A, trigger="manual")
        rep = store.get_report(WS_A, rec["report_id"])
        self.assertEqual(rep["summary_source"], "llm_validated")
        self.assertTrue(rep["executive_summary"].startswith(self.good))
        # the Advisor's one-line diagnosis is appended to the validated LLM text
        self.assertIn("Most likely cause:", rep["executive_summary"][len(self.good):])
        sent = json.loads(narrator.prompts[0])
        self.assertNotIn("query_log", sent)
        self.assertNotIn("comparables", json.dumps(sent))       # structured facts only, no raw rows

    def test_invalid_llm_summary_falls_back_to_deterministic(self):
        svc, _, store, *_ = make_service(narrator=FakeNarrator(text="Dispatch fell 99.9% because of traffic."))
        rec = svc.run_analysis(WS_A, trigger="manual")
        rep = store.get_report(WS_A, rec["report_id"])
        self.assertEqual(rep["summary_source"], "deterministic_fallback")
        self.assertTrue(rep["narrative_rejections"])
        self.assertIn("The available warehouse data shows", rep["executive_summary"])

    def test_llm_error_falls_back(self):
        svc, _, store, *_ = make_service(narrator=FakeNarrator(exc=TimeoutError("slow")))
        rec = svc.run_analysis(WS_A, trigger="manual")
        self.assertEqual(store.get_report(WS_A, rec["report_id"])["summary_source"], "deterministic_fallback")


class NoDataReport(unittest.TestCase):
    def test_report_for_empty_database_explains_itself(self):
        empty = {k: v.iloc[0:0] for k, v in tables().items()}
        svc, _, store, *_ = make_service(dbs={"srv-alpha": SyntheticDatabase(empty),
                                              "srv-beta": SyntheticDatabase(empty)})
        rec = svc.run_analysis(WS_A)
        rep = store.get_report(WS_A, rec["report_id"])
        text = render_text(rep)
        self.assertIn("contain no records in the last 35 days", text)
        self.assertIn("cannot be analysed", text)


if __name__ == "__main__":
    unittest.main()

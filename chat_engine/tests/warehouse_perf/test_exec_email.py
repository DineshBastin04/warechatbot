"""The management email: plain English, status, KPI tiles, charts, attachments."""
import io
import json
import re
import unittest

from PIL import Image

from tests.warehouse_perf.helpers import WS_A, docx_text, make_service, tables
from engine.warehouse_perf import charts
from engine.warehouse_perf.exec_report import build_executive
from engine.warehouse_perf.reporting import render_html
from engine.warehouse_perf.synthetic import SyntheticDatabase


def run(healthy=False, **kw):
    dbs = {"srv-alpha": SyntheticDatabase(tables(degrade=False, seed=3) if healthy else tables()),
           "srv-beta": SyntheticDatabase(tables(degrade=False))}
    svc, sender, store, *_ = make_service(dbs=dbs, **kw)
    rec = svc.run_analysis(WS_A)
    return svc, sender, store, store.get_report(WS_A, rec["report_id"])


class ExecutiveEmail(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svc, cls.sender, cls.store, cls.report = run()
        cls.ex = build_executive(cls.report, inline=True)

    def test_plain_english_headline_and_status(self):
        self.assertEqual(self.ex["status"], "Needs attention")
        self.assertTrue(self.ex["subject"].startswith("Warehouse alert - Alpha: Orders shipped are"))
        self.assertIn("below normal", self.ex["subject"])
        self.assertIn("mostly in warehouse WH-B", self.ex["subject"])
        for jargon in ("z =", "z-score", "baseline", "significant_deterioration", "standard deviation"):
            self.assertNotIn(jargon, self.ex["text"])

    def test_summary_points_cover_what_where_when_and_demand(self):
        text = self.ex["text"]
        self.assertIn("The shortfall is in warehouse WH-B", text)
        self.assertIn("It started around 09:00", text)
        self.assertIn("not a drop in demand", text)
        self.assertIn("Orders are piling up", text)

    def test_three_charts_are_valid_pngs_and_referenced_by_cid(self):
        ids = [cid for cid, _png, _alt in self.ex["images"]]
        self.assertEqual(ids, ["wpa-when", "wpa-where", "wpa-step"])
        for cid, png, alt in self.ex["images"]:
            img = Image.open(io.BytesIO(png))
            self.assertEqual(img.format, "PNG")
            self.assertGreater(img.width, 300)
            self.assertIn(f'src="cid:{cid}"', self.ex["html"])
            self.assertIn(f'alt="{alt}"', self.ex["html"])
        self.assertNotIn("<script", self.ex["html"].lower())
        self.assertNotIn("http", re.sub(r"cid:[\w-]+", "", self.ex["html"]))     # no external resources

    def test_kpi_tiles_and_management_recommendations(self):
        html = self.ex["html"]
        for label in ("Orders shipped", "Orders picked", "Orders waiting to ship", "Units picked"):
            self.assertIn(label, html)
        text = self.ex["text"]
        self.assertIn("Most likely cause: 'Label Printer Communication Error' exceptions slowing the Ship step in WH-B",
                      text)
        self.assertIn("Why it happened:", text)
        self.assertIn("Get the 'Label Printer Communication Error' problem fixed", text)
        self.assertIn("Put 1 more person on the Load step in WH-B", text)
        self.assertIn("Plan to clear the backlog in WH-B", text)
        self.assertIn("Checked and ruled out:", text)
        for h in ("Why it happened", "What to do now", "Checked and ruled out"):
            self.assertIn(h, self.ex["html"])

    def test_sent_email_is_the_rich_version_with_attachments(self):
        call = self.sender.calls[0]
        self.assertIn("Warehouse alert", call["subject"])
        self.assertTrue(call["html"].startswith("<!doctype html>"))
        self.assertEqual([cid for cid, _ in call["inline_images"]], ["wpa-when", "wpa-where", "wpa-step"])
        names = [n for n, _m, _d in call["extra_attachments"]]
        self.assertTrue(names[0].endswith("_report.docx"))
        self.assertTrue(call["filename"].endswith("_data.csv"))
        self.assertIn("1. Executive summary", docx_text(call["extra_attachments"][0][2]))

    def test_every_chart_leads_with_a_plain_answer(self):
        from engine.warehouse_perf.exec_report import RED_RULE, _chart_specs, _clean_name
        specs = {cid: (ans, note) for cid, _png, _t, ans, note, _alt in _chart_specs(self.report["result"])}
        self.assertTrue(specs["wpa-when"][0].startswith("It started around 09:00"))
        self.assertIn("Since then:", specs["wpa-when"][0])
        self.assertTrue(specs["wpa-where"][0].startswith("Mainly in warehouse WH-B"))
        self.assertIn("hit hardest", specs["wpa-step"][0])
        self.assertEqual(sum(RED_RULE in n for _a, n in specs.values()), 1)      # colour rule said once
        for ans, _n in specs.values():
            self.assertIn(ans, self.ex["html"].replace("&#x27;", "'"))
        self.assertEqual(_clean_name("Picking (pick) (301)"), "Picking")
        self.assertEqual(_clean_name("Load (203)"), "Load")

    def test_email_says_it_is_ai_generated_at_the_top_and_bottom(self):
        from engine.warehouse_perf.exec_report import AI_DISCLAIMER, AI_NOTICE
        html, text = self.ex["html"], self.ex["text"]
        self.assertIn("AI-generated report:", html)
        self.assertLess(html.index("AI-generated report:"), html.index("In short"))   # seen before the findings
        self.assertIn("Disclaimer:", html)
        self.assertLess(text.index(AI_NOTICE), text.index("In short:"))
        self.assertIn(AI_DISCLAIMER, text)

    def test_full_report_page_leads_with_the_management_view(self):
        page = render_html(self.report)
        self.assertLess(page.index("Needs attention"), page.index("Technical details"))
        self.assertIn("data:image/png;base64,", page)
        self.assertNotIn("cid:", page)


class WordReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from engine.warehouse_perf.word_report import build_docx
        _svc, _sender, _store, cls.report = run()
        cls.data = build_docx(cls.report)

    def test_is_a_real_word_document_with_charts_and_tables(self):
        import io
        import zipfile
        from docx import Document
        doc = Document(io.BytesIO(self.data))
        self.assertEqual(len(doc.inline_shapes), 3)                       # the three charts
        media = [n for n in zipfile.ZipFile(io.BytesIO(self.data)).namelist() if n.startswith("word/media/")]
        self.assertEqual(len(media), 3)
        headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
        for h in ("In short", "Key numbers", "When did it start?", "Where is the problem?", "Which step is affected?",
                  "Why it happened", "What to do now", "Checked and ruled out", "Technical details",
                  "1. Executive summary", "12. Root-cause investigation", "13. Likely causes and recommended actions"):
            self.assertIn(h, headings)

    def test_content_is_management_language_first(self):
        text = docx_text(self.data)
        self.assertIn("Needs attention", text)
        self.assertIn("Orders shipped are", text)
        self.assertIn("Worse than normal", text)
        self.assertLess(text.index("In short"), text.index("Technical details"))

    def test_says_it_is_ai_generated(self):
        from engine.warehouse_perf.exec_report import AI_DISCLAIMER
        text = docx_text(self.data)
        self.assertIn("AI-generated report: these results were produced automatically by AI agents", text)
        self.assertIn(AI_DISCLAIMER, text)


class NormalDay(unittest.TestCase):
    def test_all_normal_update_has_an_overview_chart(self):
        svc, sender, store, report = run(healthy=True)
        ex = build_executive(report)
        self.assertEqual(ex["status"], "All normal")
        self.assertTrue(ex["subject"].startswith("Warehouse update - Alpha: All warehouse measures are within"))
        self.assertEqual([c for c, _p, _a in ex["images"]], ["wpa-overview"])
        self.assertIn("No action needed", ex["text"])


class Fallbacks(unittest.TestCase):
    def test_old_style_sender_still_gets_plain_text(self):
        calls = []

        def old_sender(recipients, subject, body, rows, filename):     # no html support
            calls.append(subject)
            return True
        svc, _s, store, *_ = make_service()
        svc.delivery._send = old_sender
        rec = svc.run_analysis(WS_A)
        self.assertEqual(rec["email_status"], "sent")
        self.assertEqual(len(calls), 1)

    def test_chart_helpers_handle_empty_input(self):
        self.assertIsNone(charts.hourly_chart([]))
        self.assertIsNone(charts.change_bars([]))
        png = charts.change_bars([{"name": "A very long warehouse name", "pct": 12, "state": "better"},
                                  {"name": "B", "pct": -80, "state": "worse"}])
        self.assertEqual(Image.open(io.BytesIO(png)).format, "PNG")


if __name__ == "__main__":
    unittest.main()

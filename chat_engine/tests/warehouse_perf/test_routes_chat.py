"""Dashboard/report API, authorization and the optional chat interface."""
import json
import unittest

from tests.warehouse_perf.helpers import WS_A, WS_B, make_flask, make_service, user
from engine.warehouse_perf.chat import WarehouseChat, is_warehouse_command


class Routes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svc, cls.sender, cls.store, cls.factory, cls.coll = make_service()
        cls.rec = cls.svc.run_analysis(WS_A, trigger="manual")
        cls.client = make_flask(cls.svc).test_client()

    def get(self, path, who):
        return self.client.get(path, headers={"X-Test-User": who})

    def post(self, path, payload, who):
        return self.client.post(path, data=json.dumps(payload), content_type="application/json",
                                headers={"X-Test-User": who})

    def test_unauthenticated_is_redirected(self):
        self.assertEqual(self.client.get(f"/api/v0/warehouse_perf/dashboard?workspace_id={WS_A}").status_code, 302)
        self.assertEqual(self.client.get("/warehouse-performance").status_code, 302)

    def test_dashboard_for_own_workspace_user(self):
        r = self.get(f"/api/v0/warehouse_perf/dashboard?workspace_id={WS_A}", user("user", "Alpha"))
        self.assertEqual(r.status_code, 200)
        d = r.get_json()["dashboard"]
        self.assertEqual(d["report"]["report_id"], self.rec["report_id"])
        self.assertEqual(d["report"]["where"]["warehouse"]["name"], "WH-B")
        self.assertIn("units_moved", d["report"]["kpis"])
        self.assertNotIn("recipients", d)                       # admins only
        blob = json.dumps(d)
        self.assertNotIn("db-secret-pw-123", blob)
        self.assertNotIn("ops@alpha.example", blob)
        self.assertNotIn("api_key", blob)

    def test_user_cannot_read_another_workspace(self):
        r = self.get(f"/api/v0/warehouse_perf/dashboard?workspace_id={WS_B}", user("user", "Alpha"))
        self.assertEqual(r.status_code, 403)
        r = self.get("/api/v0/warehouse_perf/dashboard?workspace_id=does-not-exist", user("user", "Alpha"))
        self.assertEqual(r.status_code, 403)                    # same answer as "forbidden": no probing

    def test_pinned_admin_is_limited_to_their_workspace(self):
        self.assertEqual(self.get(f"/api/v0/warehouse_perf/dashboard?workspace_id={WS_B}",
                                  user("admin", "Alpha")).status_code, 403)
        self.assertEqual(self.get(f"/api/v0/warehouse_perf/dashboard?workspace_id={WS_B}",
                                  user("admin", "")).status_code, 200)

    def test_admin_dashboard_includes_masked_recipients(self):
        d = self.get(f"/api/v0/warehouse_perf/dashboard?workspace_id={WS_A}", user("admin")).get_json()["dashboard"]
        self.assertEqual(d["recipients"]["recipients"], [{"label": "Operations Head",
                                                          "address_masked": "o***@alpha.example"}])

    def test_report_formats(self):
        base = f"/api/v0/warehouse_perf/report?workspace_id={WS_A}&report_id={self.rec['report_id']}"
        who = user("user", "Alpha")
        self.assertIn("1. Executive summary", self.get(base + "&format=text", who).get_data(as_text=True))
        html = self.get(base + "&format=html", who)
        self.assertIn("default-src 'none'", html.headers["Content-Security-Policy"])
        self.assertTrue(self.get(base + "&format=csv", who).get_data(as_text=True).startswith("metric,"))
        word = self.get(base + "&format=docx", who)
        self.assertEqual(word.status_code, 200)
        self.assertIn("wordprocessingml", word.headers["Content-Type"])
        self.assertIn(".docx", word.headers["Content-Disposition"])
        self.assertEqual(word.get_data()[:2], b"PK")                         # a real .docx (zip)
        body = self.get(base, who).get_json()
        self.assertNotIn("query_log", body["report"]["result"])
        self.assertEqual(self.get(f"/api/v0/warehouse_perf/reports?workspace_id={WS_A}", who).get_json()["reports"][0]
                         ["report_id"], self.rec["report_id"])

    def test_send_requires_admin(self):
        before = len(self.sender.calls)
        r = self.post("/api/v0/warehouse_perf/report/send", {"workspace_id": WS_A}, user("user", "Alpha"))
        self.assertEqual(r.status_code, 403)
        self.assertEqual(len(self.sender.calls), before)

    def test_admin_send_and_run(self):
        r = self.post("/api/v0/warehouse_perf/report/send", {"workspace_id": WS_A, "report_id": self.rec["report_id"]},
                      user("admin"))
        self.assertEqual(r.get_json()["delivery"]["status"], "sent")
        r = self.post("/api/v0/warehouse_perf/run", {"workspace_id": WS_A}, user("user", "Alpha"))
        self.assertEqual(r.status_code, 200)

    def test_dashboard_js_and_page(self):
        js = self.get("/api/v0/warehouse_perf/dashboard.js", user("user", "Alpha"))
        js_text = js.get_data(as_text=True)
        self.assertIn("showWarehousePerfAgent", js_text)
        self.assertIn("Download Word", js_text)
        self.assertNotIn("Download text", js_text)
        self.assertIn("autoRefresh", js_text)
        page = self.get(f"/warehouse-performance?workspace_id={WS_A}", user("user", "Alpha")).get_data(as_text=True)
        self.assertIn("renderWarehousePerfDashboard", page)

    def test_there_is_no_configuration_api(self):
        for path in ("/api/v0/warehouse_perf/config", "/api/v0/warehouse_perf/config/save"):
            self.assertEqual(self.post(path, {"workspace_id": WS_A}, user("admin")).status_code, 404)


class PinnedClock(unittest.TestCase):
    def test_as_of_setting_pins_the_analysis_clock_and_is_shown(self):
        from datetime import datetime
        svc, *_ = make_service(now=None, as_of="2026-09-24T13:30")
        svc._clock = None
        self.assertEqual(svc.now().replace(tzinfo=None), datetime(2026, 9, 24, 13, 30))
        rec = svc.run_analysis(WS_A, trigger="manual")
        self.assertEqual(rec["status"], "ok")
        self.assertEqual(svc.dashboard(WS_A)["monitoring"]["clock_pinned_to"], "2026-09-24T13:30")

    def test_moving_the_pinned_clock_back_does_not_block_manual_runs(self):
        svc, *_ = make_service(now=None, as_of="2026-09-24T13:30", manual_cooldown_seconds=60)
        svc._clock = None
        svc.run_analysis(WS_A, trigger="manual")
        svc.settings.as_of = "2023-10-26T16:00"         # runs recorded "in the future" relative to the new clock
        self.assertFalse(svc.recently_ran(WS_A))


class Chat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svc, cls.sender, cls.store, *_ = make_service(manual_cooldown_seconds=0)
        cls.chat = WarehouseChat(cls.svc)

    def say(self, text, who=None):
        return self.chat.handle(json.loads(who or user("admin")), WS_A, text)

    def test_detection(self):
        self.assertTrue(is_warehouse_command("/warehouse report"))
        self.assertFalse(is_warehouse_command("/warehousing"))
        self.assertFalse(is_warehouse_command("how is the warehouse doing"))

    def test_report_before_and_after_a_run(self):
        svc, *_ = make_service()
        body, _ = WarehouseChat(svc).handle(json.loads(user("admin")), WS_A, "/warehouse report")
        self.assertIn("No analysis has completed", body["text"])
        body, _ = self.say("/warehouse run")                       # no scheduler -> runs inline
        self.assertIn("What changed", body["text"])
        body, _ = self.say("/warehouse report")
        self.assertIn("WH-B", body["text"])

    def test_send_needs_confirmation_and_admin(self):
        self.say("/warehouse run")                          # the run itself may auto-email the problem
        before = len(self.sender.calls)
        body, status = self.say("/warehouse send", user("user", "Alpha"))
        self.assertEqual(status, 403)
        body, _ = self.say("/warehouse send")
        self.assertIn("Operations Head", body["text"])
        self.assertEqual(len(self.sender.calls), before)          # preview never sends
        rid = self.store.latest_report(WS_A)["report_id"]
        body, _ = self.say(f"/warehouse send confirm {rid}")
        self.assertIn("Sent to Operations Head", body["text"])
        self.assertEqual(len(self.sender.calls), before + 1)
        body, _ = self.say("/warehouse send confirm 20000101-000000-abcdef")
        self.assertIn("not the latest report", body["text"])

    def test_other_workspace_is_refused(self):
        body, status = self.chat.handle(json.loads(user("user", "Beta")), WS_A, "/warehouse report")
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()

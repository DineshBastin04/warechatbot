"""Configurable report email: which saved recipients get the report, and when."""
import json
import unittest

from tests.warehouse_perf.helpers import WS_A, WS_B, make_flask, make_service, tables, two_workspaces, user
from engine.warehouse_perf.service import ServiceError
from engine.warehouse_perf.synthetic import SyntheticDatabase

THREE = [{"label": "Operations Head", "address": "ops@alpha.example"},
         {"label": "Shift Lead", "address": "lead@alpha.example"},
         {"label": "Planner", "address": "plan@alpha.example"}]


def setup(recipients=THREE, healthy=False, **settings):
    coll = two_workspaces()
    coll.update_meta(WS_A, email_recipients=json.dumps(recipients))
    dbs = {"srv-alpha": SyntheticDatabase(tables(degrade=False, seed=3) if healthy else tables()),
           "srv-beta": SyntheticDatabase(tables(degrade=False))}
    return make_service(coll=coll, dbs=dbs, **settings)


def sent_to(sender):
    return sorted(c["recipients"][0] for c in sender.calls)


class Selection(unittest.TestCase):
    def test_default_is_every_saved_recipient(self):
        svc, sender, *_ = setup()
        self.assertEqual(svc.email_settings(WS_A)["recipients"], None)
        svc.run_analysis(WS_A)
        self.assertEqual(sent_to(sender), ["lead@alpha.example", "ops@alpha.example", "plan@alpha.example"])

    def test_only_ticked_recipients_get_the_report(self):
        svc, sender, *_ = setup()
        svc.save_email_settings(WS_A, {"mode": "significant", "recipients": ["shift lead", "Planner"]}, "admin")
        rec = svc.run_analysis(WS_A)
        self.assertEqual(rec["email_status"], "sent")
        self.assertEqual(sent_to(sender), ["lead@alpha.example", "plan@alpha.example"])

    def test_nobody_ticked_means_no_email_with_a_reason(self):
        svc, sender, store, *_ = setup()
        svc.save_email_settings(WS_A, {"mode": "significant", "recipients": []}, "admin")
        rec = svc.run_analysis(WS_A)
        self.assertEqual(rec["email_status"], "not_sent_no_recipients")
        self.assertEqual(sender.calls, [])
        self.assertIn("no recipients are selected", store.latest_report(WS_A)["delivery"]["reason"])

    def test_unknown_names_and_bad_modes_are_rejected(self):
        svc, *_ = setup()
        with self.assertRaises(ServiceError):
            svc.save_email_settings(WS_A, {"mode": "significant", "recipients": ["Nobody"]}, "admin")
        with self.assertRaises(ServiceError):
            svc.save_email_settings(WS_A, {"mode": "hourly-spam", "recipients": None}, "admin")

    def test_a_newly_added_recipient_receives_the_current_problem(self):
        svc, sender, *_ = setup()
        svc.save_email_settings(WS_A, {"recipients": ["Operations Head"]}, "admin")
        svc.run_analysis(WS_A)
        self.assertEqual(sent_to(sender), ["ops@alpha.example"])
        svc.save_email_settings(WS_A, {"recipients": ["Operations Head", "Shift Lead"]}, "admin")
        rec = svc.run_analysis(WS_A)                      # same problem, same day
        self.assertEqual(rec["email_status"], "sent")
        self.assertEqual(sent_to(sender), ["lead@alpha.example", "ops@alpha.example"])   # ops not re-sent

    def test_settings_are_per_workspace(self):
        svc, sender, *_ = setup()
        svc.save_email_settings(WS_A, {"recipients": []}, "admin")
        self.assertIsNone(svc.email_settings(WS_B)["recipients"])


class Modes(unittest.TestCase):
    def test_significant_mode_sends_nothing_on_a_normal_day(self):
        svc, sender, *_ = setup(healthy=True)
        rec = svc.run_analysis(WS_A)
        self.assertEqual(rec["email_status"], "not_required")
        self.assertEqual(sender.calls, [])

    def test_every_run_mode_sends_every_report_even_when_normal(self):
        svc, sender, *_ = setup(healthy=True)
        svc.save_email_settings(WS_A, {"mode": "every_run", "recipients": ["Planner"]}, "admin")
        first = svc.run_analysis(WS_A)
        second = svc.run_analysis(WS_A)
        self.assertEqual((first["email_status"], second["email_status"]), ("sent", "sent"))
        self.assertEqual(sent_to(sender), ["plan@alpha.example", "plan@alpha.example"])

    def test_every_run_mode_sends_problems_every_run_too(self):
        svc, sender, *_ = setup()
        svc.save_email_settings(WS_A, {"mode": "every_run", "recipients": ["Planner"]}, "admin")
        runs = [svc.run_analysis(WS_A) for _ in range(5)]          # more than the daily limit of 3
        self.assertEqual([r["email_status"] for r in runs], ["sent"] * 5)
        self.assertEqual(len(sender.calls), 5)

    def test_automatic_runs_keep_once_per_problem(self):
        svc, sender, *_ = setup()
        svc.save_email_settings(WS_A, {"mode": "significant", "recipients": ["Planner"]}, "admin")
        svc.run_analysis(WS_A)
        again = svc.run_analysis(WS_A)
        self.assertEqual(again["email_status"], "duplicate_skipped")
        self.assertEqual(len(sender.calls), 1)

    def test_run_analysis_now_always_emails_a_problem(self):
        """A person clicked Run analysis now: the problem is emailed even if it was already
        emailed today and the automatic daily limit is used up."""
        svc, sender, *_ = setup(max_auto_emails_per_day=1)
        svc.save_email_settings(WS_A, {"mode": "significant", "recipients": ["Planner"]}, "admin")
        self.assertEqual(svc.run_analysis(WS_A)["email_status"], "sent")                   # automatic: uses the limit
        self.assertEqual(svc.run_analysis(WS_A)["email_status"], "not_sent_daily_cap")    # automatic again: blocked
        manual = [svc.run_analysis(WS_A, trigger="manual", actor="admin") for _ in range(2)]
        self.assertEqual([r["email_status"] for r in manual], ["sent", "sent"])
        self.assertEqual(len(sender.calls), 3)
        self.assertFalse(svc.dashboard(WS_A)["last_email"]["automatic"])

    def test_run_analysis_now_does_not_email_when_all_is_normal(self):
        svc, sender, *_ = setup(healthy=True)
        rec = svc.run_analysis(WS_A, trigger="manual", actor="admin")
        self.assertEqual(rec["email_status"], "not_required")
        self.assertEqual(sender.calls, [])


class Api(unittest.TestCase):
    def test_admin_can_save_user_cannot_and_dashboard_shows_the_choice(self):
        svc, *_ = setup()
        client = make_flask(svc).test_client()
        post = lambda who, payload: client.post("/api/v0/warehouse_perf/email_settings", data=json.dumps(payload),
                                                content_type="application/json", headers={"X-Test-User": who})
        payload = {"workspace_id": WS_A, "mode": "every_run", "recipients": ["Planner"]}
        self.assertEqual(post(user("user", "Alpha"), payload).status_code, 403)
        r = post(user("admin"), payload)
        self.assertEqual(r.get_json()["email_settings"]["recipients"], ["planner"])
        dash = client.get(f"/api/v0/warehouse_perf/dashboard?workspace_id={WS_A}",
                          headers={"X-Test-User": user("admin")}).get_json()["dashboard"]
        es = dash["email_settings"]
        self.assertEqual(es["mode"], "every_run")
        self.assertEqual({x["label"]: x["selected"] for x in es["saved"]},
                         {"Operations Head": False, "Shift Lead": False, "Planner": True})
        self.assertNotIn("plan@alpha.example", json.dumps(dash))          # addresses stay masked
        self.assertEqual(dash["recipients"]["recipients"], [{"label": "Planner", "address_masked": "p***@alpha.example"}])
        bad = post(user("admin"), {"workspace_id": WS_A, "recipients": ["Nobody"]})
        self.assertEqual(bad.status_code, 400)


if __name__ == "__main__":
    unittest.main()

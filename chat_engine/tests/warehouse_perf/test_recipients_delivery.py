"""Saved-recipient resolution, no-recipient behaviour and delivery rules
(spec tests 10, 11)."""
import json
import unittest

from tests.warehouse_perf.helpers import (docx_text, WS_A, WS_B, EmailConfig, RecordingSender, make_service, tables,
                                          two_workspaces)
from engine.warehouse_perf import recipients as recip
from engine.warehouse_perf.synthetic import SyntheticDatabase


def ctx_for(coll, ws):
    from engine.warehouse_perf.workspace_context import WorkspaceResolver
    return WorkspaceResolver(coll).get(ws)


class Resolution(unittest.TestCase):
    def test_resolves_every_saved_recipient_of_the_workspace(self):
        coll = two_workspaces()
        resolved, problems = recip.resolve_workspace_recipients(ctx_for(coll, WS_B), WS_B)
        self.assertEqual(sorted(r["address"] for r in resolved), ["only@beta.example", "ops@beta.example"])
        self.assertEqual(problems, [])

    def test_never_resolves_against_another_workspace(self):
        coll = two_workspaces()
        resolved, problems = recip.resolve_workspace_recipients(ctx_for(coll, WS_B), WS_A)
        self.assertEqual(resolved, [])
        self.assertEqual(problems[0]["reason"], recip.REASON_WRONG_WORKSPACE)
        a, _ = recip.resolve_workspace_recipients(ctx_for(coll, WS_A), WS_A)
        self.assertEqual([r["address"] for r in a], ["ops@alpha.example"])

    def test_duplicate_and_invalid_saved_entries_are_skipped_not_guessed(self):
        coll = two_workspaces()
        coll.update_meta(WS_A, email_recipients=json.dumps([
            {"label": "Ops Head", "address": "one@alpha.example"}, {"label": "ops  head", "address": "two@alpha.example"},
            {"label": "Broken", "address": "not-an-email"}, {"label": "Lead", "address": "lead@alpha.example"}]))
        resolved, problems = recip.resolve_workspace_recipients(ctx_for(coll, WS_A), WS_A)
        self.assertEqual([r["address"] for r in resolved], ["lead@alpha.example"])
        self.assertEqual({p["reason"] for p in problems}, {recip.REASON_AMBIGUOUS, recip.REASON_INVALID})

    def test_optional_deployment_label_filter(self):
        coll = two_workspaces()
        resolved, problems = recip.resolve_workspace_recipients(ctx_for(coll, WS_B), WS_B,
                                                                [recip.normalize_label("  OPERATIONS head ")])
        self.assertEqual([r["label"] for r in resolved], ["Operations Head"])
        _, problems = recip.resolve_workspace_recipients(ctx_for(coll, WS_B), WS_B, ["nobody"])
        self.assertEqual(problems[0]["reason"], recip.REASON_MISSING)

    def test_public_summary_masks_addresses(self):
        s = recip.public_summary(ctx_for(two_workspaces(), WS_A), WS_A)
        self.assertEqual(s["recipients"], [{"label": "Operations Head", "address_masked": "o***@alpha.example"}])


class AutomaticDelivery(unittest.TestCase):
    def test_significant_deterioration_is_emailed_to_saved_recipients(self):
        svc, sender, store, *_ = make_service()
        rec = svc.run_analysis(WS_A, trigger="scheduled")
        self.assertEqual(rec["email_status"], "sent")
        self.assertEqual([c["recipients"] for c in sender.calls], [["ops@alpha.example"]])
        call = sender.calls[0]
        self.assertTrue(call["subject"].startswith("Warehouse alert - Alpha:"))
        self.assertIn("NEEDS ATTENTION", call["body"])                     # plain-text part of the email
        self.assertTrue(call["extra_attachments"][0][0].endswith("_report.docx"))                # Word report
        self.assertIn("1. Executive summary", docx_text(call["extra_attachments"][0][2]))
        report = store.latest_report(WS_A)
        dash = svc.dashboard(WS_A)
        self.assertEqual(dash["last_email"]["sent_to"], ["Operations Head"])
        self.assertTrue(dash["last_email"]["automatic"])
        self.assertEqual(dash["last_email"]["report_id"], report["report_id"])
        self.assertTrue(call["filename"].endswith(".csv"))
        self.assertIsInstance(call["rows"][0], dict)
        report = store.get_report(WS_A, rec["report_id"])
        self.assertEqual(report["delivery"]["sent_to"], [{"label": "Operations Head",
                                                          "address_masked": "o***@alpha.example"}])

    def test_same_incident_is_not_emailed_twice(self):
        svc, sender, store, *_ = make_service()
        svc.run_analysis(WS_A, trigger="scheduled")
        rec2 = svc.run_analysis(WS_A, trigger="scheduled")
        self.assertEqual(rec2["email_status"], "duplicate_skipped")
        self.assertEqual(len(sender.calls), 1)

    def test_daily_cap(self):
        svc, sender, store, *_ = make_service(max_auto_emails_per_day=0)
        rec = svc.run_analysis(WS_A, trigger="scheduled")
        self.assertEqual(rec["email_status"], "not_sent_daily_cap")
        self.assertEqual(sender.calls, [])

    def test_manual_and_rescan_runs_also_email_automatically(self):
        for trigger in ("manual", "rediscover", "chat"):
            svc, sender, *_ = make_service()
            rec = svc.run_analysis(WS_A, trigger=trigger)
            self.assertEqual(rec["email_status"], "sent", trigger)
            self.assertEqual([c["recipients"] for c in sender.calls], [["ops@alpha.example"]])

    def test_manual_then_scheduled_run_does_not_email_the_same_problem_twice(self):
        svc, sender, *_ = make_service()
        svc.run_analysis(WS_A, trigger="manual")
        again = svc.run_analysis(WS_A, trigger="scheduled")
        self.assertEqual(again["email_status"], "duplicate_skipped")
        self.assertEqual(len(sender.calls), 1)

    def test_auto_email_can_be_switched_off(self):
        svc, sender, *_ = make_service(auto_email=False)
        rec = svc.run_analysis(WS_A, trigger="manual")
        self.assertEqual(rec["email_status"], "not_sent_auto_email_off")
        self.assertEqual(sender.calls, [])

    def test_kill_switch(self):
        svc, sender, store, *_ = make_service(email_cfg=EmailConfig(enabled=False))
        rec = svc.run_analysis(WS_A, trigger="scheduled")
        self.assertEqual(rec["email_status"], "suppressed_kill_switch")
        self.assertEqual(sender.calls, [])

    def test_provider_failure_retries_then_records_without_secrets(self):
        svc, sender, store, *_ = make_service(sender=RecordingSender(fail_times=10))
        rec = svc.run_analysis(WS_A, trigger="scheduled")
        self.assertEqual(rec["email_status"], "failed")
        self.assertEqual(len(sender.calls), 3)
        self.assertNotIn("db-secret-pw-123", json.dumps(store.list_deliveries(WS_A)))


class NoRecipients(unittest.TestCase):
    def test_report_is_generated_but_not_sent_and_reason_is_recorded(self):
        coll = two_workspaces()
        coll.update_meta(WS_A, email_recipients=json.dumps([]))
        svc, sender, store, *_ = make_service(coll=coll)
        rec = svc.run_analysis(WS_A, trigger="scheduled")
        self.assertTrue(rec["report_generated"])
        self.assertEqual(rec["email_status"], "not_sent_no_recipients")
        self.assertEqual(sender.calls, [])
        report = store.get_report(WS_A, rec["report_id"])
        self.assertIn("no saved email recipients", report["delivery"]["reason"])
        dash = svc.dashboard(WS_A, include_admin=True)
        self.assertEqual(dash["report"]["delivery"]["status"], "not_sent_no_recipients")
        self.assertEqual(dash["recipients"]["recipients"], [])
        audit = store.list_deliveries(WS_A)
        self.assertEqual(audit[0]["status"], "not_sent_no_recipients")

    def test_manual_send_without_recipients(self):
        coll = two_workspaces()
        coll.update_meta(WS_A, email_recipients=json.dumps([{"label": "Broken", "address": "nope"}]))
        svc, sender, store, *_ = make_service(coll=coll)
        svc.run_analysis(WS_A, trigger="manual")
        out = svc.send_report(WS_A, None, "admin")
        self.assertEqual(out["status"], "not_sent_no_recipients")
        self.assertEqual(sender.calls, [])

    def test_manual_send_goes_only_to_saved_recipients_once(self):
        dbs = {"srv-alpha": SyntheticDatabase(tables()), "srv-beta": SyntheticDatabase(tables())}
        svc, sender, store, *_ = make_service(dbs=dbs)
        rec = svc.run_analysis(WS_B, trigger="manual")      # auto-emails once (significant problem)
        before = len(sender.calls)
        out = svc.send_report(WS_B, rec["report_id"], "admin")
        self.assertEqual(sorted(c["recipients"][0] for c in sender.calls[before:]),
                         ["only@beta.example", "ops@beta.example"])
        again = svc.send_report(WS_B, rec["report_id"], "admin")
        self.assertEqual(again["status"], "duplicate_skipped")
        self.assertEqual(len(sender.calls), before + 2)
        self.assertEqual(out["status"], "sent")


if __name__ == "__main__":
    unittest.main()

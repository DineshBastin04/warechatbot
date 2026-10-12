"""Scheduling on the existing APScheduler for multiple workspaces, and
failure isolation (spec tests 13, 14)."""
import unittest

from apscheduler.schedulers.background import BackgroundScheduler

from tests.warehouse_perf.helpers import (WS_A, WS_B, BrokenCollection, make_service, tables, two_workspaces,
                                          ws_meta)
from engine.warehouse_perf.jobs import JOB_PREFIX, RECONCILE_ID, WarehousePerfJobs
from engine.warehouse_perf.synthetic import SyntheticDatabase
from engine.warehouse_perf.workspace_context import WorkspaceResolver

WS_C = "cccccccc-0000-4000-8000-00000000000c"


class Scheduling(unittest.TestCase):
    def setUp(self):
        self.scheduler = BackgroundScheduler()      # stands in for scheduled_agents_scheduler; never started
        self.svc, self.sender, self.store, self.factory, self.coll = make_service()
        self.jobs = WarehousePerfJobs(self.scheduler, self.svc, interval_minutes=60)
        self.svc.jobs = self.jobs

    def ids(self):
        return {j.id for j in self.scheduler.get_jobs()}

    def test_registers_on_the_supplied_scheduler_only(self):
        self.assertTrue(self.jobs.start())
        self.assertEqual(self.ids(), {RECONCILE_ID})
        self.assertFalse(WarehousePerfJobs(None, self.svc).start())

    def test_every_workspace_gets_its_own_job_without_configuration(self):
        self.jobs.reconcile()
        self.assertEqual({i for i in self.ids() if i.startswith(JOB_PREFIX)},
                         {JOB_PREFIX + WS_A, JOB_PREFIX + WS_B})
        job = self.scheduler.get_job(JOB_PREFIX + WS_B)
        self.assertEqual(tuple(job.args), (WS_B,))                    # the explicit workspace id is the job's only input
        self.assertEqual(job.max_instances, 1)
        self.assertTrue(job.coalesce)

    def test_new_workspace_is_picked_up_and_deleted_one_removed(self):
        self.jobs.reconcile()
        self.coll.add(WS_C, ws_meta("Gamma", "srv-alpha"))
        self.coll.delete(WS_A)
        self.jobs.reconcile()
        self.assertEqual({i for i in self.ids() if i.startswith(JOB_PREFIX)},
                         {JOB_PREFIX + WS_B, JOB_PREFIX + WS_C})

    def test_unreadable_workspace_list_changes_nothing(self):
        self.jobs.reconcile()
        before = self.ids()
        self.svc.resolver = WorkspaceResolver(BrokenCollection())
        self.jobs.reconcile()
        self.assertEqual(self.ids(), before)

    def test_scheduled_run_for_multiple_workspaces(self):
        out = self.jobs.run_all_once()
        self.assertEqual(set(out), {WS_A, WS_B})
        self.assertTrue(all(r["status"] == "ok" and r["trigger"] == "scheduled" for r in out.values()))
        self.assertEqual([w for w, _ in self.factory.requests], [WS_A, WS_B])
        self.assertIsNotNone(self.store.latest_report(WS_A))
        self.assertIsNotNone(self.store.latest_report(WS_B))

    def test_job_body_runs_the_right_workspace(self):
        self.jobs.reconcile()
        job = self.scheduler.get_job(JOB_PREFIX + WS_B)
        job.func(*job.args)
        self.assertEqual(self.factory.requests, [(WS_B, "srv-beta")])

    def test_next_run_and_queue_now(self):
        self.jobs.reconcile()
        self.assertIsNotNone(self.jobs.next_run(WS_A))
        self.assertTrue(self.jobs.queue_now(WS_A, "manual", "admin"))
        self.assertTrue(self.jobs.is_queued(WS_A))

    def test_overlapping_run_for_same_workspace_is_skipped(self):
        release = self.store.try_run_lock(WS_A)
        try:
            rec = self.svc.run_analysis(WS_A)
        finally:
            release()
        self.assertEqual(rec["status"], "skipped")
        self.assertEqual(self.factory.requests, [])


class FailureIsolation(unittest.TestCase):
    def test_database_failure_in_one_workspace_does_not_stop_the_other(self):
        svc, sender, store, factory, coll = make_service(data_kw={"srv-alpha": {"fail_all": True}})
        jobs = WarehousePerfJobs(BackgroundScheduler(), svc)
        out = jobs.run_all_once()
        self.assertEqual(out[WS_A]["status"], "failed")
        self.assertEqual(out[WS_A]["db_status"], "failed")
        self.assertIn("schema discovery failed", out[WS_A]["failure_reason"])
        self.assertEqual(out[WS_B]["status"], "ok")
        self.assertIsNotNone(store.latest_report(WS_B))
        self.assertIsNone(store.latest_report(WS_A))
        self.assertEqual(store.last_run(WS_A)["status"], "failed")

    def test_every_query_failing_after_discovery(self):
        svc, sender, store, factory, coll = make_service(data_kw={"srv-alpha": {"fail_labels": {"orders_", "transactions",
                                                                                                "pending"}}})
        rec = svc.run_analysis(WS_A)
        self.assertEqual(rec["db_status"], "partial")
        rep = store.latest_report(WS_A)
        self.assertEqual(rep["result"]["status"], "query_failed")

    def test_crash_inside_a_run_is_contained(self):
        svc, *_ = make_service()

        def boom(*a, **k):
            raise RuntimeError("unexpected")
        svc._data_factory = boom
        rec = svc.run_analysis(WS_A)
        self.assertEqual(rec["status"], "failed")
        self.assertIn("RuntimeError", rec["failure_reason"])
        self.assertEqual(svc.run_analysis(WS_B)["status"], "failed")   # same boom, but still returns

    def test_job_body_never_raises(self):
        svc, *_ = make_service()
        jobs = WarehousePerfJobs(BackgroundScheduler(), svc)

        def explode(*a, **k):
            raise RuntimeError("service down")
        svc.run_analysis = explode
        jobs.run_workspace(WS_A)          # must not raise
        jobs.reconcile()

    def test_one_slow_or_broken_workspace_does_not_share_state(self):
        dbs = {"srv-alpha": SyntheticDatabase(tables()), "srv-beta": SyntheticDatabase(tables())}
        svc, _, store, factory, _ = make_service(dbs=dbs, data_kw={"srv-beta": {"fail_catalog": True}})
        a = svc.run_analysis(WS_A)
        b = svc.run_analysis(WS_B)
        a2 = svc.run_analysis(WS_A)
        self.assertEqual((a["status"], b["status"], a2["status"]), ("ok", "failed", "ok"))


if __name__ == "__main__":
    unittest.main()

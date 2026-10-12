"""Workspace isolation (spec test 1): every run resolves its own workspace,
reads only that workspace's database and writes only its own store."""
import json
import logging
import os
import re
import unittest

from tests.warehouse_perf.helpers import (DB_PASSWORD, WS_A, WS_B, SyntheticDatabase, make_service, tables,
                                          two_workspaces)

PKG = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "engine",
                   "warehouse_perf")


def two_dbs():
    beta = tables(degrade=False, seed=3, warehouses={"BETA-1": 300, "BETA-2": 200})
    return {"srv-alpha": SyntheticDatabase(tables()), "srv-beta": SyntheticDatabase(beta)}


class Isolation(unittest.TestCase):
    def setUp(self):
        self.svc, self.sender, self.store, self.factory, self.coll = make_service(dbs=two_dbs())

    def test_each_run_reads_only_its_own_workspace_database(self):
        a = self.svc.run_analysis(WS_A)
        b = self.svc.run_analysis(WS_B)
        self.assertEqual(self.factory.requests, [(WS_A, "srv-alpha"), (WS_B, "srv-beta")])
        ra = self.store.get_report(WS_A, a["report_id"])
        rb = self.store.get_report(WS_B, b["report_id"])
        wa = {x["key"] for m in ra["result"]["metrics"] for x in m.get("by_warehouse") or []}
        wb = {x["key"] for m in rb["result"]["metrics"] for x in m.get("by_warehouse") or []}
        self.assertEqual(wa, {"WH-A", "WH-B", "WH-C"})
        self.assertEqual(wb, {"BETA-1", "BETA-2"})
        self.assertEqual(ra["workspace_id"], WS_A)
        self.assertEqual(rb["workspace_id"], WS_B)

    def test_results_catalogs_and_reports_are_stored_per_workspace(self):
        a = self.svc.run_analysis(WS_A)
        b = self.svc.run_analysis(WS_B)
        self.assertIsNone(self.store.get_report(WS_B, a["report_id"]))
        self.assertIsNone(self.store.get_report(WS_A, b["report_id"]))
        self.assertEqual([r["report_id"] for r in self.store.list_reports(WS_A)], [a["report_id"]])
        self.assertTrue(os.path.isfile(os.path.join(self.store.root, WS_A, "catalog.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.store.root, WS_B, "catalog.json")))

    def test_baselines_are_not_shared(self):
        a = self.svc.run_analysis(WS_A)
        b = self.svc.run_analysis(WS_B)
        ma = next(m for m in self.store.get_report(WS_A, a["report_id"])["result"]["metrics"]
                  if m["metric_id"] == "orders_dispatched")
        mb = next(m for m in self.store.get_report(WS_B, b["report_id"])["result"]["metrics"]
                  if m["metric_id"] == "orders_dispatched")
        self.assertNotEqual(ma["comparables"], mb["comparables"])

    def test_changing_one_workspace_database_invalidates_only_its_catalog(self):
        self.svc.run_analysis(WS_A)
        self.svc.run_analysis(WS_B)
        cfg = json.loads(self.coll._ws[WS_A]["db_config"])
        cfg["serverName"] = "srv-beta"
        self.coll.update_meta(WS_A, db_config=json.dumps(cfg))
        rec = self.svc.run_analysis(WS_A)
        self.assertEqual(rec["discovery"], "discovered")
        self.assertEqual(self.svc.run_analysis(WS_B)["discovery"], "cached")

    def test_empty_scan_is_not_cached_so_new_data_is_picked_up(self):
        from engine.warehouse_perf.synthetic import SyntheticDatabase as SDB
        empty = SDB({k: v.iloc[0:0] for k, v in tables().items()})
        self.factory.dbs["srv-alpha"] = empty
        first = self.svc.run_analysis(WS_A)
        self.assertEqual(first["status"], "no_recent_data")
        self.factory.dbs["srv-alpha"] = SDB(tables())            # data arrives (e.g. test rows inserted)
        second = self.svc.run_analysis(WS_A)                      # plain run, no "Re-scan database"
        self.assertEqual((second["discovery"], second["status"]), ("discovered", "ok"))
        self.assertEqual(self.svc.run_analysis(WS_A)["discovery"], "cached")   # a useful scan is cached

    def test_path_traversal_workspace_ids_are_rejected(self):
        rec = self.svc.run_analysis("../../etc")
        self.assertEqual(rec["failure_reason"], "workspace not found")
        from engine.warehouse_perf.store import StoreError
        with self.assertRaises(StoreError):
            self.store.get_report("../x", "r")

    def test_deleted_workspace_is_not_analysed(self):
        self.coll.delete(WS_A)
        rec = self.svc.run_analysis(WS_A)
        self.assertEqual(rec["status"], "failed")
        self.assertEqual(self.factory.requests, [])

    def test_workspace_without_database_is_not_configured(self):
        self.coll.update_meta(WS_A, db_config=json.dumps({}))
        rec = self.svc.run_analysis(WS_A)
        self.assertEqual(rec["status"], "not_configured")
        self.assertEqual(self.factory.requests, [])

    def test_no_secrets_in_logs_reports_or_store(self):
        with self.assertLogs("engine.warehouse_perf", level=logging.INFO) as logs:
            a = self.svc.run_analysis(WS_A)
        blob = "\n".join(logs.output)
        for root, _, files in os.walk(self.store.root):
            for f in files:
                with open(os.path.join(root, f), encoding="utf-8") as fh:
                    blob += fh.read()
        self.assertNotIn(DB_PASSWORD, blob)
        self.assertNotIn("ops@alpha.example", blob)          # addresses only ever stored masked
        self.assertIn(f"workspace={WS_A}", blob)

    def test_package_never_uses_the_global_vn_or_active_workspace(self):
        for name in os.listdir(PKG):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(PKG, name), encoding="utf-8") as fh:
                src = fh.read()
            code = re.sub(r'""".*?"""', "", src, flags=re.S)
            code = re.sub(r"#.*", "", code)
            self.assertIsNone(re.search(r"\bvn\b|ensure_vanna_initialized|session\[|current_workspace", code), name)


if __name__ == "__main__":
    unittest.main()

"""Automatic data discovery and missing-column handling (spec test 8)."""
import unittest

from tests.warehouse_perf.helpers import tables
from engine.warehouse_perf import discovery as D
from engine.warehouse_perf.synthetic import TABLE_TYPES, SyntheticDatabase


def catalog(drop=None, only=None, rename=None, extra=None):
    """Synthetic catalog with columns dropped/renamed, or tables limited."""
    types = {}
    for ref, cols in TABLE_TYPES.items():
        if only and ref not in only:
            continue
        cols = {(rename or {}).get(f"{ref}.{c}", c): t for c, t in cols.items()
                if f"{ref}.{c}" not in (drop or ())}
        types[ref] = cols
    types.update(extra or {})
    rows = []
    for ref, cols in types.items():
        schema, table = ref.split(".")
        for c, t in cols.items():
            name, length = t if isinstance(t, tuple) else (t, None)
            rows.append({"schema": schema, "table": table, "column": c, "data_type": name, "max_length": length,
                         "table_type": "BASE TABLE"})
    return rows


def ids(model):
    return {m["metric_id"] for m in model["metrics"]}


def reason(model, mid):
    return next(u["reason"] for u in model["unavailable"] if u["metric_id"] == mid)


class Tokens(unittest.TestCase):
    def test_splits_snake_camel_and_compound_names(self):
        self.assertEqual(D.split_tokens("start_tran_date"), ["start", "tran", "date"])
        self.assertEqual(D.split_tokens("OrderNumber"), ["order", "number"])
        self.assertEqual(D.split_tokens("shipdate"), ["ship", "date"])
        self.assertEqual(D.split_tokens("WH_ID"), ["wh", "id"])


class Discovery(unittest.TestCase):
    def test_finds_activity_and_order_sources_and_ignores_noise(self):
        model = D.discover(catalog())
        act, orders = model["sources"]["activity"], model["sources"]["orders"]
        self.assertEqual(act["table"], "t_tran_log")                      # not the _archive copy
        self.assertEqual(act["ts"], {"column": "start_tran_date", "time_column": "start_tran_time",
                                     "granularity": "hour"})
        self.assertEqual((act["quantity"], act["process"], act["warehouse"]), ("tran_qty", "tran_type", "wh_id"))
        self.assertEqual(orders["table"], "t_order")
        self.assertEqual(orders["order_key"], "order_number")
        self.assertEqual(set(orders["stages"]), {"created", "picked", "packed", "loaded", "dispatched"})
        self.assertEqual(orders["stages"]["dispatched"]["column"], "ship_date")      # not required_ship_date
        self.assertEqual(orders["dims"].get("category"), "order_category")
        self.assertEqual(ids(model), {"transactions", "units_moved", "orders_received", "orders_picked",
                                      "orders_packed", "orders_loaded", "orders_dispatched", "pending_orders",
                                      "processing_time"})

    def test_probe_picks_the_candidate_with_recent_rows_and_detects_date_only(self):
        def probe(cand, ts, wide=False):
            return {"rows": 500, "midnight_rows": 500 if cand["table"] == "t_tran_log" else 0}
        model = D.discover(catalog(drop={"dbo.t_tran_log.start_tran_time"}), probe=probe)
        self.assertEqual(model["sources"]["activity"]["ts"]["granularity"], "day")
        self.assertTrue(any("dates without times" in n for n in model["notes"]))

    def test_planning_dates_are_not_event_timestamps(self):
        extra = {"dbo.t_order": {**TABLE_TYPES["dbo.t_order"], "earliest_ship_date": "datetime"}}
        extra["dbo.t_order"].pop("ship_date")
        model = D.discover(catalog(extra=extra))
        self.assertNotIn("dispatched", model["sources"]["orders"]["stages"])

    def test_empty_best_candidate_reports_latest_record(self):
        def probe(cand, ts, wide=False):
            return {"rows": 900, "last_ts": "2025-03-14T17:00:00"} if wide else {"rows": 0}
        model = D.discover(catalog(), probe=probe)
        self.assertEqual(model["sources"]["activity"]["probe"]["latest_record"], "2025-03-14T17:00:00")
        self.assertTrue(any("latest record is from 2025-03-14" in n for n in model["notes"]))
        self.assertEqual(model["metrics"], [])

    def test_candidate_that_cannot_be_read_is_skipped(self):
        def probe(cand, ts, wide=False):
            raise RuntimeError("permission denied")
        model = D.discover(catalog(), probe=probe)
        self.assertIsNone(model["sources"]["activity"])
        self.assertTrue(any("could not be read" in n for n in model["notes"]))


class TransactionTypes(unittest.TestCase):
    def test_description_column_is_found_for_the_type_code(self):
        model = D.discover(catalog())
        self.assertEqual(model["sources"]["activity"]["process_description"], "description")

    def test_real_highjump_labels(self):
        # labels as they appear in a real HighJump t_tran_log
        rows = [{"code": c, "label": l} for c, l in [
            ("301", "Picking (bot-pick)"), ("302", "Picking (bot-put)"), ("309", "Picking (WAVESTAGE pick)"),
            ("308", "Picking (WAVESTAGE Put)"), ("340", "Shipping"), ("341", "Will Call Shipping"),
            ("342", "Consolidated Shipping"), ("904", "Void Shipment"), ("201", "Move (Pick)"),
            ("211", "2PRT Move (Pick)"), ("257", "Slot Move (Pick)"), ("251", "Directed Move (Pick)"),
            ("313", "PICK Move (Pick)"), ("305", "Replenishment (pick)"), ("376", "Short Pick Close"),
            ("391", "Unload/Unpick (pick)"), ("323", "Will Call Loading (pick)"),
            ("320", "Loading (non-system directed)"), ("152", "Inbound Order Receipt (put)"),
            ("852", "Inventory Adjustment by Item"), ("100", "System Login/Logout Transaction")]]
        out = D.classify_process_labels(rows)
        self.assertEqual(out["pick_codes"], ["301", "309"])
        self.assertEqual(out["ship_codes"], ["340", "341", "342"])
        self.assertEqual(out["outbound_codes"], ["301", "309"])      # one stage only: no double counting
        self.assertEqual(out["labels"]["152"], "Inbound Order Receipt (put)")

    def test_ship_types_are_used_when_there_are_no_pick_types(self):
        out = D.classify_process_labels([{"code": "1", "label": "Shipping"}, {"code": "2", "label": "Receipt"}])
        self.assertEqual((out["outbound_codes"], out["outbound_stage"]), (["1"], "ship"))

    def test_units_moved_is_scoped_to_outbound_codes(self):
        def labels(cand):
            return [{"code": "201", "label": "Pick", "rows": 9}, {"code": "202", "label": "Pack", "rows": 9},
                    {"code": "204", "label": "Ship", "rows": 9}]
        model = D.discover(catalog(), probe=lambda c, ts, wide=False: {"rows": 10}, process_labels=labels)
        units = next(m for m in model["metrics"] if m["metric_id"] == "units_moved")
        self.assertEqual(units["outbound_codes"], ["201"])
        self.assertIn("picking transaction types only (Pick (201)), so each unit is counted once", units["scope_note"])
        self.assertIn("Shipping types are not added", units["scope_note"])

    def test_falls_back_to_all_types_when_nothing_is_identifiable(self):
        model = D.discover(catalog(drop={"dbo.t_tran_log.description"}), probe=lambda c, ts, wide=False: {"rows": 10},
                           process_labels=lambda c: self.fail("no description column -> no label query"))
        units = next(m for m in model["metrics"] if m["metric_id"] == "units_moved")
        self.assertEqual(units["outbound_codes"], [])
        self.assertIn("sums tran_qty over all transaction types", units["scope_note"])

    def test_label_query_failure_is_not_fatal(self):
        def boom(cand):
            raise RuntimeError("timeout")
        model = D.discover(catalog(), probe=lambda c, ts, wide=False: {"rows": 10}, process_labels=boom)
        self.assertIn("units_moved", ids(model))
        self.assertTrue(any("raw codes are shown" in n for n in model["notes"]))


class MissingColumns(unittest.TestCase):
    def test_no_dispatch_timestamp(self):
        model = D.discover(catalog(drop={"dbo.t_order.ship_date"}))
        self.assertNotIn("orders_dispatched", ids(model))
        self.assertEqual(reason(model, "orders_dispatched"),
                         "Dispatch performance cannot be analysed because dispatch timestamps are unavailable.")
        self.assertIn("orders_loaded", ids(model))

    def test_no_quantity_column(self):
        model = D.discover(catalog(drop={"dbo.t_tran_log.tran_qty"}))
        self.assertIn("transactions", ids(model))
        self.assertNotIn("units_moved", ids(model))
        self.assertIn("no quantity column", reason(model, "units_moved"))

    def test_no_created_timestamp_disables_backlog_and_processing_time(self):
        model = D.discover(catalog(drop={"dbo.t_order.order_date"}))
        self.assertNotIn("pending_orders", ids(model))
        self.assertNotIn("processing_time", ids(model))
        self.assertIn("order-created timestamp", reason(model, "pending_orders"))

    def test_no_warehouse_identifier(self):
        model = D.discover(catalog(drop={"dbo.t_order.wh_id", "dbo.t_tran_log.wh_id"}))
        self.assertIsNone(model["sources"]["orders"]["warehouse"])
        self.assertIsNone(model["sources"]["activity"]["warehouse"])

    def test_no_order_table_at_all(self):
        model = D.discover(catalog(only={"dbo.t_tran_log", "dbo.t_item_master"}))
        self.assertEqual(ids(model), {"transactions", "units_moved"})
        self.assertIn("no order table", reason(model, "orders_dispatched"))

    def test_nothing_usable(self):
        model = D.discover(catalog(only={"dbo.t_item_master"}))
        self.assertEqual(model["metrics"], [])
        self.assertEqual(len(model["unavailable"]), len(D.METRICS))

    def test_hostile_column_names_are_just_names(self):
        extra = {"dbo.t_activity": {"event_date": "datetime", "x]; DROP TABLE t_order--": "int",
                                    "qty": "int", "wh_id": ("nvarchar", 10)}}
        model = D.discover(catalog(only={"dbo.t_item_master"}, extra=extra))
        self.assertEqual(model["sources"]["activity"]["table"], "t_activity")

    def test_real_synthetic_db_catalog(self):
        rows = SyntheticDatabase(tables()).catalog_rows()
        self.assertEqual(D.discover(rows)["sources"]["orders"]["table"], "t_order")


if __name__ == "__main__":
    unittest.main()

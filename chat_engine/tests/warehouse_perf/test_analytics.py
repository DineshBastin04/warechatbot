"""Baseline calculation, percentage deviation, historical comparison and
classification — the deterministic core (spec tests 2, 3, 4)."""
import unittest
from datetime import date, timedelta

import pandas as pd

from tests.warehouse_perf import helpers  # noqa: F401  (sets sys.path)
from engine.warehouse_perf import analytics as A

THU = date(2026, 9, 24)


def frame(rows):
    """rows: [(date, hour, wh, n)]"""
    return pd.DataFrame([{"bucket_date": d, "bucket_hour": h, "wh": wh, "proc": None, "dim": None, "n": float(n),
                          "q": float(n) * 2, "dur_sum": 0.0} for d, h, wh, n in rows])


class Comparables(unittest.TestCase):
    def test_same_weekday_preferred(self):
        days = {THU - timedelta(days=k) for k in range(1, 36)}
        comps, method = A.select_comparables(THU, days)
        self.assertEqual(method, "same_weekday")
        self.assertEqual(comps, [THU - timedelta(weeks=k) for k in range(1, 6)])
        self.assertTrue(all(c.weekday() == THU.weekday() for c in comps))

    def test_falls_back_to_recent_operating_days(self):
        days = {THU - timedelta(days=k) for k in range(1, 9)}      # only 1 same weekday in range
        comps, method = A.select_comparables(THU, days)
        self.assertEqual(method, "recent_operating_days")
        self.assertEqual(comps[0], THU - timedelta(days=1))

    def test_insufficient_history_is_reported_not_fabricated(self):
        comps, method = A.select_comparables(THU, {THU - timedelta(days=1), THU - timedelta(days=2)})
        self.assertEqual(method, "insufficient")
        res = A.classify(100, [50, 60], A.HIGHER)
        self.assertEqual(res["classification"], A.INSUFFICIENT)
        self.assertIsNone(res["baseline"])
        self.assertIsNone(res["pct_diff"])
        self.assertIn("At least 3 comparable periods are required (found 2)", res["basis"])

    def test_closed_days_are_not_comparables(self):
        days = {THU - timedelta(weeks=k) for k in (1, 3, 4, 5)}    # week 2 was closed / no data
        comps, _ = A.select_comparables(THU, days)
        self.assertNotIn(THU - timedelta(weeks=2), comps)


class Classification(unittest.TestCase):
    def test_median_baseline_abs_and_pct_deviation(self):
        res = A.classify(80, [100, 104, 96, 102, 98], A.HIGHER)
        self.assertEqual(res["baseline"], 100)
        self.assertEqual(res["abs_diff"], -20)
        self.assertEqual(res["pct_diff"], -20.0)

    def test_significant_deterioration_uses_historical_variation(self):
        res = A.classify(80, [100, 104, 96, 102, 98], A.HIGHER)
        self.assertLess(res["z_score"], -3)
        self.assertEqual(res["classification"], A.SIGNIFICANT)

    def test_same_change_on_volatile_history_is_normal(self):
        res = A.classify(80, [100, 140, 60, 130, 70], A.HIGHER)
        self.assertEqual(res["classification"], A.NORMAL)

    def test_moderate_deviation_is_deterioration(self):
        res = A.classify(82, [100, 110, 90, 105, 95], A.HIGHER)    # z ~ -2.3: unusual, not extreme
        self.assertTrue(-3 < res["z_score"] < -2)
        self.assertEqual(res["classification"], A.DETERIORATION)

    def test_improvement_and_lower_is_better(self):
        self.assertEqual(A.classify(130, [100, 104, 96, 102, 98], A.HIGHER)["classification"], A.IMPROVEMENT)
        self.assertEqual(A.classify(130, [100, 104, 96, 102, 98], A.LOWER)["classification"], A.SIGNIFICANT)
        self.assertEqual(A.classify(70, [100, 104, 96, 102, 98], A.LOWER)["classification"], A.IMPROVEMENT)

    def test_materiality_floor_blocks_tiny_but_unusual_moves(self):
        res = A.classify(97, [100, 100.2, 99.8, 100.1, 99.9], A.HIGHER)
        self.assertLess(res["z_score"], -3)
        self.assertEqual(res["classification"], A.NORMAL)

    def test_zero_variation_history(self):
        self.assertEqual(A.classify(100, [100, 100, 100], A.HIGHER)["classification"], A.NORMAL)
        res = A.classify(50, [100, 100, 100], A.HIGHER)
        self.assertEqual(res["classification"], A.DETERIORATION)
        self.assertIsNone(res["z_score"])

    def test_neutral_metric_is_never_deterioration(self):
        res = A.classify(60, [100, 104, 96, 102, 98], A.NEUTRAL)
        self.assertEqual(res["classification"], A.BELOW)

    def test_usual_range_matches_the_colour_rule(self):
        # the band drawn behind each chart bar: outside it on the bad side = deterioration, inside = normal
        for history in ([100, 104, 96, 102, 98], [100, 140, 60, 130, 70], [100, 100.2, 99.8, 100.1, 99.9]):
            for actual in range(40, 161, 3):
                res = A.classify(actual, history, A.HIGHER)
                lo, hi = A.usual_range_pct(res)
                outside = res["pct_diff"] < lo or res["pct_diff"] > hi
                self.assertEqual(res["classification"] != A.NORMAL, outside, (history, actual, lo, hi))
        self.assertEqual(A.usual_range_pct(A.classify(50, [100, 100, 100], A.HIGHER)), [-5.0, 5.0])
        self.assertIsNone(A.usual_range_pct(A.classify(50, [100], A.HIGHER)))

    def test_pct_change_edge_cases(self):
        self.assertIsNone(A.pct_change(5, 0))
        self.assertIsNone(A.pct_change(None, 5))
        self.assertEqual(A.pct_change(150, 100), 50.0)
        self.assertEqual(A.oriented_pct({"pct_diff": 20.0}, A.LOWER), -20.0)


class EqualElapsedWindow(unittest.TestCase):
    def test_cube_compares_only_elapsed_hours(self):
        rows = [(THU, h, "W1", 10) for h in range(6, 13)]
        for k in (1, 2, 3):
            rows += [(THU - timedelta(weeks=k), h, "W1", 10) for h in range(6, 21)]
        cube = A.Cube(frame(rows), "n")
        self.assertEqual(cube.value(THU, 13), 70)
        self.assertEqual(cube.value(THU - timedelta(weeks=1), 13), 70)       # same hours, not the whole day
        self.assertEqual(cube.value(THU - timedelta(weeks=1), 24), 150)
        self.assertEqual(cube.value(THU, 13, wh="W1"), 70)
        self.assertEqual(A.Cube(frame(rows), "q").value(THU, 13), 140)

    def test_degradation_window_finds_sustained_start(self):
        prof = []
        for h in range(12):
            base = 100
            actual = 100 if h < 8 else 60
            prof.append({"hour": h, "actual": actual, "baseline": base, "mean": base, "std": 5})
        w = A.degradation_window(prof, A.HIGHER)
        self.assertEqual((w["start_hour"], w["ongoing"]), (8, True))

    def test_degradation_window_tolerates_one_gap_hour_and_reports_recovery(self):
        vals = [100, 100, 60, 60, 98, 60, 60, 100, 100]
        prof = [{"hour": h, "actual": v, "baseline": 100, "mean": 100, "std": 5} for h, v in enumerate(vals)]
        w = A.degradation_window(prof, A.HIGHER)
        self.assertEqual((w["start_hour"], w["end_hour"], w["ongoing"]), (2, 7, False))
        self.assertIsNone(A.degradation_window([{"hour": 0, "actual": 100, "baseline": 100, "mean": 100,
                                                 "std": 5}], A.HIGHER))

    def test_trend(self):
        start = THU - timedelta(days=14)
        rising = [(start + timedelta(days=i), 100 + 5 * i) for i in range(10)]
        self.assertEqual(A.trend(rising)["direction"], "rising")
        flat = [(start + timedelta(days=i), 100 + (3 if i % 2 else -3)) for i in range(10)]
        self.assertEqual(A.trend(flat)["direction"], "flat")
        self.assertEqual(A.trend(rising[:3])["direction"], "unknown")


if __name__ == "__main__":
    unittest.main()

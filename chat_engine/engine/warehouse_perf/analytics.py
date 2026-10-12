"""
Phases 2–3 — deterministic performance analytics, baselines and deviation
classification. Pure functions over the bucket frames from queries.py; no I/O,
no LLM.

Baseline methodology (fixed, not configurable):
  * The current period is compared over an EQUAL ELAPSED WINDOW: today
    00:00 up to the last complete hour is compared with the same hours of each
    comparable day, never with whole days.
  * Comparable days, in order of preference:
      1. the same weekday in each of the previous 5 weeks (operating days only)
      2. if fewer than MIN_COMPARABLE of those exist, the most recent operating
         days in the previous 21 days (up to 10)
    An "operating day" is a day on which the metric's source table recorded
    any activity — so closed days, and days before the data begins, never
    drag a baseline to zero.
  * Baseline = median of the comparable values. Fewer than MIN_COMPARABLE
    comparable periods => "insufficient_data"; no baseline is fabricated.
  * Unusualness is judged from historical variation: z = (actual - mean) /
    sample std of the comparables — the same formula and default threshold
    (|z| > 2.0) as the app's generic z_score anomaly engine. |z| >= 3 is
    "significant". A 5% materiality floor stops a statistically unusual but
    immaterial wobble (on very stable history) from being flagged; it is a
    guard, not the primary mechanism.
"""
import math
from datetime import timedelta

import numpy as np

MIN_COMPARABLE = 3
SAME_WEEKDAY_WEEKS = 5
RECENT_WINDOW_DAYS = 21
RECENT_MAX = 10
Z_NOTABLE = 2.0
Z_SIGNIFICANT = 3.0
MATERIALITY_PCT = 5.0
HOURLY_Z = 1.0
TREND_DAYS = 14
TREND_MIN_POINTS = 5

HIGHER, LOWER, NEUTRAL = "higher_is_better", "lower_is_better", "neutral"

IMPROVEMENT = "improvement"
NORMAL = "normal_variation"
DETERIORATION = "deterioration"
SIGNIFICANT = "significant_deterioration"
INSUFFICIENT = "insufficient_data"
ABOVE = "above_normal"
BELOW = "below_normal"

SEVERITY = {SIGNIFICANT: 4, DETERIORATION: 3, ABOVE: 2, BELOW: 2, IMPROVEMENT: 1, NORMAL: 0, INSUFFICIENT: -1}
ADVERSE = (SIGNIFICANT, DETERIORATION)


# ------------------------------------------------------------------- cube
class Cube:
    """Hour-resolved sums for one measure, indexed by day and (wh, proc, dim).
    kind: "n" (count), "q" (sum of quantity) or "avg_duration" (dur_sum / n)."""

    def __init__(self, frame, kind="n"):
        self.kind = kind
        self.days = {}
        self.members = {"wh": set(), "proc": set(), "dim": set()}
        if frame is None or not len(frame):
            return
        cols = ["bucket_date", "wh", "proc", "dim", "bucket_hour"]
        f = frame.copy()
        for c in ("wh", "proc", "dim"):
            f[c] = f[c].where(f[c].notna(), "") if c in f else ""
        g = f.groupby(cols, dropna=False)[["n", "q", "dur_sum"]].sum().reset_index()
        for row in g.itertuples(index=False):
            d, wh, proc, dim, h, n, q, dur = row
            key = (wh or None, proc or None, dim or None)
            arr = self.days.setdefault(d, {}).get(key)
            if arr is None:
                arr = np.zeros((3, 24))
                self.days[d][key] = arr
            hour = int(h) if 0 <= int(h) < 24 else 0
            arr[0, hour] += n
            arr[1, hour] += q
            arr[2, hour] += dur
            for name, v in (("wh", wh), ("proc", proc), ("dim", dim)):
                if v:
                    self.members[name].add(v)

    def active_days(self):
        return {d for d, keys in self.days.items() if any(a[0].sum() > 0 for a in keys.values())}

    def _sum(self, day, hours, wh, proc, dim, hour=None):
        tot = np.zeros(3)
        for (k_wh, k_proc, k_dim), arr in (self.days.get(day) or {}).items():
            if (wh is not None and k_wh != wh) or (proc is not None and k_proc != proc) or \
                    (dim is not None and k_dim != dim):
                continue
            tot += arr[:, hour] if hour is not None else arr[:, :hours].sum(axis=1)
        return tot

    def value(self, day, hours=24, wh=None, proc=None, dim=None, hour=None):
        n, q, dur = self._sum(day, hours, wh, proc, dim, hour)
        if self.kind == "avg_duration":
            return (dur / n) if n > 0 else None
        return float(q if self.kind == "q" else n)

    def last_active_hour(self, day, hours=24):
        last = None
        for arr in (self.days.get(day) or {}).values():
            nz = np.nonzero(arr[0, :hours])[0]
            if len(nz):
                last = int(nz[-1]) if last is None else max(last, int(nz[-1]))
        return last


# ----------------------------------------------------------------- stats
def pct_change(actual, baseline):
    if actual is None or baseline is None or baseline == 0:
        return None
    return (actual - baseline) / abs(baseline) * 100.0


def describe(values):
    vals = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    if not vals:
        return {"n": 0, "median": None, "mean": None, "std": None, "min": None, "max": None}
    arr = np.array(vals)
    return {"n": len(vals), "median": float(np.median(arr)), "mean": float(arr.mean()),
            "std": float(arr.std(ddof=1)) if len(vals) >= 2 else None,
            "min": float(arr.min()), "max": float(arr.max())}


def classify(actual, comparable_values, direction, min_comparable=MIN_COMPARABLE):
    """Deterministic deviation classification. Returns a dict with baseline,
    abs/pct difference, z-score, classification and a plain-English basis."""
    st = describe(comparable_values)
    out = {"actual": _r(actual), "baseline": _r(st["median"]), "baseline_mean": _r(st["mean"]),
           "baseline_std": _r(st["std"]), "baseline_min": _r(st["min"]), "baseline_max": _r(st["max"]),
           "n_comparable": st["n"], "abs_diff": None, "pct_diff": None, "z_score": None,
           "classification": INSUFFICIENT, "basis": None}
    if actual is None:
        out["basis"] = "no value could be calculated for the current period"
        return out
    if st["n"] < min_comparable:
        for k in ("baseline", "baseline_mean", "baseline_std", "baseline_min", "baseline_max"):
            out[k] = None      # never present a baseline built from too little history
        out["basis"] = (f"No historical baseline is available yet. At least {min_comparable} comparable periods "
                        f"are required (found {st['n']}).")
        return out
    base = st["median"]
    out["abs_diff"] = _r(actual - base)
    pct = pct_change(actual, base)
    out["pct_diff"] = _r(pct)
    z = (actual - st["mean"]) / st["std"] if st["std"] else None
    out["z_score"] = _r(z)
    oriented_up = actual > base
    if direction == NEUTRAL:
        if z is None:
            unusual = pct is not None and abs(pct) >= MATERIALITY_PCT * 2
        else:
            unusual = abs(z) >= Z_NOTABLE and (pct is None or abs(pct) >= MATERIALITY_PCT)
        out["classification"] = (ABOVE if oriented_up else BELOW) if unusual and actual != base else NORMAL
        out["basis"] = _basis(z, pct, st["n"])
        return out
    adverse = (actual < base) if direction == HIGHER else (actual > base)
    if z is None:
        # every comparable period was identical: there is no variation to measure against
        if actual == base:
            cls = NORMAL
        elif pct is None:     # baseline exactly zero
            cls = DETERIORATION if adverse else IMPROVEMENT
        elif abs(pct) < MATERIALITY_PCT:
            cls = NORMAL
        else:
            cls = DETERIORATION if adverse else IMPROVEMENT
        out["classification"] = cls
        out["basis"] = (f"the {st['n']} comparable periods were identical, so no historical variation exists; "
                        f"classified on the relative change")
        return out
    if abs(z) < Z_NOTABLE or (pct is not None and abs(pct) < MATERIALITY_PCT):
        cls = NORMAL
    elif not adverse:
        cls = IMPROVEMENT
    else:
        cls = SIGNIFICANT if abs(z) >= Z_SIGNIFICANT else DETERIORATION
    out["classification"] = cls
    out["basis"] = _basis(z, pct, st["n"])
    return out


def usual_range_pct(r):
    """The band, in % against the baseline, inside which `classify` calls a value normal:
    within Z_NOTABLE standard deviations of the comparable periods' mean, and never narrower
    than +/- MATERIALITY_PCT. A value outside it on the adverse side is a deterioration (red);
    inside it, the change is the size normal days show too (grey). [low, high] or None."""
    base, mean, std = r.get("baseline"), r.get("baseline_mean"), r.get("baseline_std")
    if not base or mean is None:
        return None
    if std:
        lo, hi = pct_change(mean - Z_NOTABLE * std, base), pct_change(mean + Z_NOTABLE * std, base)
    else:
        lo = hi = 0.0
    return [round(min(lo, -MATERIALITY_PCT), 1), round(max(hi, MATERIALITY_PCT), 1)]


def _basis(z, pct, n):
    if z is None:
        return f"relative change against {n} comparable periods"
    return f"{abs(z):.1f} standard deviations {'above' if z > 0 else 'below'} the mean of {n} comparable periods"


def oriented_pct(result, direction):
    """Percentage change with the sign flipped for lower-is-better metrics, so
    negative always means worse."""
    p = result.get("pct_diff")
    if p is None or direction == NEUTRAL:
        return None
    return p if direction == HIGHER else -p


def _r(v, nd=2):
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return round(f, nd)


# ------------------------------------------------------------ comparables
def select_comparables(period_date, operating_days, min_comparable=MIN_COMPARABLE):
    """-> (dates newest-first, method). method: same_weekday | recent_operating_days | insufficient."""
    same = [period_date - timedelta(weeks=k) for k in range(1, SAME_WEEKDAY_WEEKS + 1)]
    same = [d for d in same if d in operating_days]
    if len(same) >= min_comparable:
        return same, "same_weekday"
    lo = period_date - timedelta(days=RECENT_WINDOW_DAYS)
    recent = sorted((d for d in operating_days if lo <= d < period_date), reverse=True)[:RECENT_MAX]
    if len(recent) >= min_comparable:
        return recent, "recent_operating_days"
    return (same if len(same) >= len(recent) else recent), "insufficient"


METHOD_TEXT = {
    "same_weekday": "median of the same weekday in previous weeks, over the same hours",
    "recent_operating_days": "median of recent operating days (too few same-weekday history), over the same hours",
    "insufficient": "not enough comparable history",
}


def previous_operating_day(period_date, operating_days):
    prior = [d for d in operating_days if d < period_date]
    return max(prior) if prior else None


# ----------------------------------------------------------- time profile
def hourly_profile(cube, period_date, hours, comparable_dates, wh=None, proc=None):
    out = []
    for h in range(hours):
        actual = cube.value(period_date, wh=wh, proc=proc, hour=h)
        comps = [cube.value(d, wh=wh, proc=proc, hour=h) for d in comparable_dates]
        st = describe(comps)
        out.append({"hour": h, "actual": _r(actual), "baseline": _r(st["median"]),
                    "mean": st["mean"], "std": st["std"]})
    return out


def degradation_window(profile, direction):
    """Earliest hour of the most recent sustained adverse run (one non-adverse
    hour inside a run is tolerated). An hour is adverse when it is on the bad
    side of its hourly baseline by >= 1 historical std (or >= 5% when history
    has no variation). Returns None if no adverse hour exists."""
    if direction == NEUTRAL or not profile:
        return None

    def adverse(p):
        a, b = p["actual"], p["baseline"]
        if a is None or b is None:
            return False
        worse = (a < b) if direction == HIGHER else (a > b)
        if not worse:
            return False
        if p["std"]:
            return abs(a - p["mean"]) / p["std"] >= HOURLY_Z and abs(a - b) > 0
        return b != 0 and abs(a - b) / abs(b) * 100 >= MATERIALITY_PCT

    flags = [adverse(p) for p in profile]
    if not any(flags):
        return None
    runs, i = [], 0
    while i < len(flags):
        if not flags[i]:
            i += 1
            continue
        start = end = i
        j = i + 1
        while j < len(flags):
            if flags[j]:
                end = j
                j += 1
            elif j + 1 < len(flags) and flags[j + 1]:
                j += 1
            else:
                break
        runs.append((start, end))
        i = end + 1
    def gap(run):
        return sum(abs((profile[h]["actual"] or 0) - (profile[h]["baseline"] or 0)) for h in range(run[0], run[1] + 1))
    last = runs[-1]
    ongoing = last[1] == len(flags) - 1
    chosen = last if ongoing else max(runs, key=gap)
    return {"start_hour": chosen[0], "end_hour": chosen[1] + 1, "ongoing": chosen == last and ongoing,
            "adverse_hours": sum(flags[chosen[0]:chosen[1] + 1]), "gap": _r(gap(chosen))}


def trend(daily_points):
    """daily_points: [(date, value)] oldest-first (complete days only).
    Least-squares slope with a t-test (|t| >= 2 => a real trend)."""
    pts = [(d, v) for d, v in daily_points if v is not None]
    if len(pts) < TREND_MIN_POINTS:
        return {"direction": "unknown", "points": len(pts),
                "basis": f"at least {TREND_MIN_POINTS} complete operating days are needed"}
    x = np.array([(d - pts[0][0]).days for d, _ in pts], dtype=float)
    y = np.array([v for _, v in pts], dtype=float)
    mean = float(y.mean())
    if np.ptp(x) == 0:
        return {"direction": "unknown", "points": len(pts), "basis": "no spread in dates"}
    slope, intercept = np.polyfit(x, y, 1)
    resid = y - (slope * x + intercept)
    dof = len(pts) - 2
    se = math.sqrt(float((resid ** 2).sum()) / dof / float(((x - x.mean()) ** 2).sum())) if dof > 0 else 0.0
    t = slope / se if se > 0 else (math.inf if slope != 0 else 0.0)
    weekly_pct = (slope * 7 / mean * 100) if mean else None
    direction = "flat"
    if abs(t) >= 2 and slope != 0:
        direction = "rising" if slope > 0 else "falling"
    return {"direction": direction, "points": len(pts), "slope_per_day": _r(slope),
            "weekly_change_pct": _r(weekly_pct), "t_stat": _r(t if math.isfinite(t) else 99.0),
            "basis": f"linear trend over the last {len(pts)} complete operating days"}

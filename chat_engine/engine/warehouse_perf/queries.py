"""
Generated, read-only analytical SQL.

The agent never takes SQL from a user or an LLM. Every query is built here
from a QuerySpec whose table/column names come from the workspace's own
catalog (discovery.py); names are always emitted as [bracket]-quoted
identifiers with "]" escaped, and every query still passes through the full
read-only policy (sql_policy.validate_select_sql) at execution time with an
allowlist of exactly the one table it reads. Time bounds are bound
parameters (:window_start / :window_end), never interpolated.

Every output alias is [bracket]-quoted too (e.g. "proc" is a reserved word in
T-SQL — an unquoted alias of that name fails on a real SQL Server).

Query shapes:
  buckets  — per (date, hour[, warehouse][, process][, dimension]) counts,
             distinct counts, sums or duration sums over the look-back window
             (measure count_and_distinct: row count AS n plus distinct values of
             one column AS q — e.g. activity and the people who recorded it)
  backlog  — distinct orders created in [T-30d, T) and not yet done at T
  probe    — COUNT / MIN / MAX over the window (+ how many rows sit exactly at
             midnight, to detect date-only timestamps)
  labels   — each activity-type code with its description (e.g. tran_type 201 -> "Pick")
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime

import pandas as pd

from .workspace_context import scrub_text

logger = logging.getLogger(__name__)

NOT_RECORDED = "(not recorded)"

CATALOG_SQL = (
    "SELECT c.TABLE_SCHEMA AS table_schema, c.TABLE_NAME AS table_name, c.COLUMN_NAME AS column_name, "
    "c.DATA_TYPE AS data_type, c.CHARACTER_MAXIMUM_LENGTH AS max_length, t.TABLE_TYPE AS table_type "
    "FROM INFORMATION_SCHEMA.COLUMNS c JOIN INFORMATION_SCHEMA.TABLES t "
    "ON t.TABLE_SCHEMA = c.TABLE_SCHEMA AND t.TABLE_NAME = c.TABLE_NAME "
    "WHERE t.TABLE_TYPE IN ('BASE TABLE', 'VIEW') "
    "ORDER BY c.TABLE_SCHEMA, c.TABLE_NAME, c.ORDINAL_POSITION"
)


@dataclass(frozen=True)
class QuerySpec:
    kind: str                       # buckets | backlog | probe
    schema: str
    table: str
    ts: dict                        # {"column", "time_column", "granularity"}
    measure: str = "count"          # count | count_distinct | count_and_distinct | sum | duration
    measure_column: str = None
    start_ts: dict = None           # duration: interval start
    done_ts: dict = None            # backlog: completion timestamp
    group_warehouse: str = None
    group_process: str = None
    group_dim: str = None
    label: str = ""
    columns_used: tuple = field(default_factory=tuple)
    description_column: str = None  # labels: human-readable name of each activity-type code

    @property
    def table_ref(self):
        return f"{self.schema}.{self.table}"


def qi(name):
    return "[" + str(name).replace("]", "]]") + "]"


def _table(spec):
    return f"{qi(spec.schema)}.{qi(spec.table)}"


def ts_sql(ts):
    if ts.get("time_column"):
        return (f"(CAST(CAST({qi(ts['column'])} AS date) AS datetime) + "
                f"CAST(CAST({qi(ts['time_column'])} AS time) AS datetime))")
    return qi(ts["column"])


def _window_filter(ts):
    col = qi(ts["column"])
    return f"{col} >= :window_start AND {col} < :window_end"


def _groups(spec):
    sel, grp = [], []
    for alias, col in (("wh", spec.group_warehouse), ("proc", spec.group_process), ("dim", spec.group_dim)):
        if col:
            expr = f"CAST({qi(col)} AS nvarchar(100))"
            sel.append(f"{expr} AS {qi(alias)}")
            grp.append(expr)
    return sel, grp


def build_sql(spec):
    if spec.kind == "probe":
        t = ts_sql(spec.ts)
        return (f"SELECT COUNT(*) AS [n], MIN({t}) AS [first_ts], MAX({t}) AS [last_ts], "
                f"SUM(CASE WHEN DATEPART(hour, {t}) = 0 AND DATEPART(minute, {t}) = 0 "
                f"AND DATEPART(second, {t}) = 0 THEN 1 ELSE 0 END) AS [midnight_rows] "
                f"FROM {_table(spec)} WHERE {_window_filter(spec.ts)}")
    if spec.kind == "backlog":
        created, done = ts_sql(spec.ts), ts_sql(spec.done_ts)
        sel, grp = _groups(spec)
        where = [_window_filter(spec.ts), f"{created} < :window_end", f"({done} IS NULL OR {done} >= :window_end)"]
        sql = (f"SELECT {', '.join(sel + [f'COUNT(DISTINCT {qi(spec.measure_column)}) AS [n]'])} "
               f"FROM {_table(spec)} WHERE {' AND '.join(where)}")
        return sql + (f" GROUP BY {', '.join(grp)}" if grp else "")
    if spec.kind == "labels":
        code = f"CAST({qi(spec.group_process)} AS nvarchar(100))"
        return (f"SELECT {code} AS [code], MIN(CAST({qi(spec.description_column)} AS nvarchar(200))) AS [label], "
                f"COUNT(*) AS [rows] FROM {_table(spec)} WHERE {_window_filter(spec.ts)} GROUP BY {code}")
    if spec.kind != "buckets":
        raise ValueError(f"unknown query kind {spec.kind!r}")

    t = ts_sql(spec.ts)
    sel = [f"CAST({t} AS date) AS [bucket_date]"]
    grp = [f"CAST({t} AS date)"]
    if spec.ts.get("granularity") == "hour":
        sel.append(f"DATEPART(hour, {t}) AS [bucket_hour]")
        grp.append(f"DATEPART(hour, {t})")
    else:
        sel.append("0 AS [bucket_hour]")
    gsel, ggrp = _groups(spec)
    sel += gsel
    grp += ggrp
    where = [_window_filter(spec.ts)]
    if spec.measure == "count":
        sel.append("COUNT(*) AS [n]")
    elif spec.measure == "count_distinct":
        sel.append(f"COUNT(DISTINCT {qi(spec.measure_column)}) AS [n]")
    elif spec.measure == "count_and_distinct":
        sel += ["COUNT(*) AS [n]", f"COUNT(DISTINCT {qi(spec.measure_column)}) AS [q]"]
    elif spec.measure == "sum":
        sel += ["COUNT(*) AS [n]", f"SUM(CAST({qi(spec.measure_column)} AS float)) AS [q]"]
    elif spec.measure == "duration":
        start = ts_sql(spec.start_ts)
        sel += ["COUNT(*) AS [n]", f"SUM(CAST(DATEDIFF(minute, {start}, {t}) AS float)) AS [dur_sum]"]
        where += [f"{start} IS NOT NULL", f"{t} >= {start}"]
    else:
        raise ValueError(f"unknown measure {spec.measure!r}")
    return f"SELECT {', '.join(sel)} FROM {_table(spec)} WHERE {' AND '.join(where)} GROUP BY {', '.join(grp)}"


def _to_date(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return pd.to_datetime(v).date()


def normalize_frame(frame):
    """Canonical bucket frame: bucket_date (date), bucket_hour (int), wh, proc,
    dim (str), n, q, dur_sum (float)."""
    f = frame.copy() if frame is not None else pd.DataFrame()
    f.columns = [str(c).lower() for c in f.columns]
    if "bucket_date" in f:
        f["bucket_date"] = [_to_date(v) for v in f["bucket_date"]]
    if "bucket_hour" in f:
        f["bucket_hour"] = pd.to_numeric(f["bucket_hour"], errors="coerce").fillna(0).astype(int)
    for c in ("wh", "proc", "dim"):
        if c in f:
            f[c] = [NOT_RECORDED if (v is None or (isinstance(v, float) and pd.isna(v)) or not str(v).strip())
                    else str(v).strip() for v in f[c]]
        else:
            f[c] = None
    for c in ("n", "q", "dur_sum"):
        f[c] = pd.to_numeric(f[c], errors="coerce").fillna(0.0).astype(float) if c in f else 0.0
    return f


@dataclass
class FetchResult:
    frame: pd.DataFrame
    truncated: bool = False


class WorkspaceData:
    """Data access for ONE explicitly resolved workspace, used for one run.
    Every query goes through ReadOnlyExecutor (policy re-check, read-only
    intent, rollback, timeout, row cap). Keeps a per-run query log (no SQL
    text, no values — just label, status, rows, duration, SQL hash)."""

    def __init__(self, ctx, executor, timeout_seconds=30, row_limit=50000, catalog_row_limit=200000):
        self.ctx = ctx
        self.executor = executor
        self.timeout = timeout_seconds
        self.row_limit = row_limit
        self.catalog_row_limit = catalog_row_limit
        self.query_log = []

    def _log(self, label, status, rows=None, truncated=False, duration=None, sql_sha256=None, error=None):
        self.query_log.append({"label": label, "status": status, "rows": rows, "truncated": truncated,
                               "duration_seconds": duration, "sql_sha256": sql_sha256,
                               "error": scrub_text(error) if error else None})

    def catalog(self):
        try:
            res = self.executor.run_catalog(self.ctx, CATALOG_SQL, self.timeout, self.catalog_row_limit)
        except Exception as exc:
            self._log("catalog", "failed", error=str(exc))
            raise
        self._log("catalog", "ok", res.rows_returned, res.truncated, res.duration_seconds, res.sql_sha256)
        f = res.frame
        f.columns = [str(c).lower() for c in f.columns]
        return [{"schema": r.get("table_schema"), "table": r.get("table_name"), "column": r.get("column_name"),
                 "data_type": r.get("data_type"), "max_length": r.get("max_length"),
                 "table_type": r.get("table_type")} for r in f.to_dict("records")]

    def fetch(self, spec, window_start, window_end):
        sql = build_sql(spec)
        try:
            res = self.executor.run(self.ctx, sql, [spec.table_ref], window_start, window_end,
                                    self.timeout, self.row_limit)
        except Exception as exc:
            self._log(spec.label or spec.kind, "failed", error=str(exc))
            raise
        self._log(spec.label or spec.kind, "ok", res.rows_returned, res.truncated, res.duration_seconds,
                  res.sql_sha256)
        if spec.kind in ("probe", "labels"):
            return FetchResult(res.frame, res.truncated)
        return FetchResult(normalize_frame(res.frame), res.truncated)

    def probe(self, spec, window_start, window_end):
        f = self.fetch(spec, window_start, window_end).frame
        if f is None or not len(f):
            return {"rows": 0}
        row = {str(k).lower(): v for k, v in f.iloc[0].to_dict().items()}
        return {"rows": int(row.get("n") or 0), "first_ts": row.get("first_ts"), "last_ts": row.get("last_ts"),
                "midnight_rows": int(row.get("midnight_rows") or 0)}

    def close(self):
        """Connections are per-query and already closed; nothing is pooled."""
        self.query_log = list(self.query_log)

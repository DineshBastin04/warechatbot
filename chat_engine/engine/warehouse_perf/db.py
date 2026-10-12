"""
Read-only query execution against a workspace's own SQL Server.

Differences from VannaBase.run_sql (which this deliberately does not use):
- a fresh, per-run pyodbc connection built from the explicitly resolved
  workspace's db_config — never the shared global `vn` engine;
- autocommit OFF and an unconditional ROLLBACK before close — nothing is ever
  committed (run_sql runs inside SQLAlchemy engine.begin(), which commits);
- ApplicationIntent=ReadOnly so an Availability-Group listener routes to a
  readable secondary where one exists (harmless on a standalone server);
- the policy check runs again at execution time against the CURRENT workspace
  scope, in case the workspace's databases changed since the SQL was approved;
- :window_start / :window_end are bound parameters, not string-interpolated;
- a per-query timeout and a hard row cap (fetchmany(limit + 1)).
The one query that is NOT generated from a spec is the fixed catalog read
(queries.CATALOG_SQL over INFORMATION_SCHEMA, which the policy otherwise
forbids); run_catalog() executes that exact constant and nothing else.
"""
import hashlib
import os
import time
from dataclasses import dataclass

import pandas as pd

from .sql_policy import SqlPolicyError, bind_window_parameters, validate_select_sql
from .workspace_context import scrub_text


def sql_fingerprint(sql):
    return hashlib.sha256(str(sql or "").strip().encode("utf-8")).hexdigest()

DEFAULT_DRIVER = os.environ.get("WPA_ODBC_DRIVER", "ODBC Driver 17 for SQL Server")
LOGIN_TIMEOUT_SECONDS = 15


class QueryExecutionError(RuntimeError):
    pass


@dataclass
class QueryResult:
    frame: pd.DataFrame
    truncated: bool
    rows_returned: int
    executed_at: float
    duration_seconds: float
    sql_sha256: str


def _odbc_value(value):
    text = "" if value is None else str(value)
    if any(c in text for c in ";{}") or text != text.strip():
        return "{" + text.replace("}", "}}") + "}"
    return text


def build_connection_string(db_config, credentials=None, driver=None):
    server = str(db_config.get("serverName") or "").strip()
    database = str(db_config.get("databaseName") or "").strip()
    if not server or not database:
        raise QueryExecutionError("the workspace has no database connection configured")
    port = str(db_config.get("port") or "").strip()
    username = (credentials or {}).get("username") or db_config.get("username") or ""
    password = (credentials or {}).get("password") or db_config.get("password") or ""
    return (
        f"DRIVER={{{driver or DEFAULT_DRIVER}}};"
        f"SERVER={_odbc_value(server + (',' + port if port else ''))};"
        f"DATABASE={_odbc_value(database)};"
        f"UID={_odbc_value(username)};"
        f"PWD={_odbc_value(password)};"
        f"ApplicationIntent=ReadOnly;"
        f"Connection Timeout={LOGIN_TIMEOUT_SECONDS};"
    )


def _naive(value):
    """DB timestamps are the warehouse's local wall-clock time; bind naive values."""
    return value.replace(tzinfo=None) if getattr(value, "tzinfo", None) is not None else value


class ReadOnlyExecutor:
    def __init__(self, connect=None):
        self._connect = connect

    def _get_connect(self):
        if self._connect is not None:
            return self._connect
        import pyodbc
        return pyodbc.connect

    def run(self, ctx, sql, allowed_tables, window_start, window_end, timeout_seconds, row_limit, credentials=None):
        policy = validate_select_sql(sql, allowed_tables, ctx.scope())
        if not policy.ok:
            raise SqlPolicyError("; ".join(policy.errors))
        bound_sql, order = bind_window_parameters(sql)
        values = {"window_start": _naive(window_start), "window_end": _naive(window_end)}
        params = [values[name] for name in order]
        return self._execute(ctx, bound_sql, params, sql, timeout_seconds, row_limit, credentials)

    def run_catalog(self, ctx, sql, timeout_seconds, row_limit, credentials=None):
        from .queries import CATALOG_SQL
        if sql != CATALOG_SQL:
            raise SqlPolicyError("only the fixed catalog query may bypass the table allowlist")
        return self._execute(ctx, sql, [], sql, timeout_seconds, row_limit, credentials)

    def _execute(self, ctx, bound_sql, params, sql, timeout_seconds, row_limit, credentials=None):
        conn_str = build_connection_string(ctx.db_config, credentials)
        started = time.time()
        conn = None
        try:
            try:
                conn = self._get_connect()(conn_str, autocommit=False, timeout=LOGIN_TIMEOUT_SECONDS)
            except Exception as exc:
                raise QueryExecutionError(f"could not connect to the workspace database: {scrub_text(exc)}") from None
            conn.timeout = int(timeout_seconds)
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(bound_sql, params)
                else:
                    cursor.execute(bound_sql)
            except Exception as exc:
                raise QueryExecutionError(f"query failed: {scrub_text(exc)}") from None
            if cursor.description is None:
                raise QueryExecutionError("the query returned no result set")
            columns = [d[0] for d in cursor.description]
            rows = cursor.fetchmany(int(row_limit) + 1)
            truncated = len(rows) > int(row_limit)
            rows = rows[: int(row_limit)]
            frame = pd.DataFrame.from_records([tuple(r) for r in rows], columns=columns)
            return QueryResult(
                frame=frame,
                truncated=truncated,
                rows_returned=len(frame),
                executed_at=started,
                duration_seconds=round(time.time() - started, 3),
                sql_sha256=sql_fingerprint(sql),
            )
        finally:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass

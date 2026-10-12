"""Read-only SQL enforcement (spec test 9): the policy, the generated SQL and
the executor's connection handling."""
import unittest
from types import SimpleNamespace

from tests.warehouse_perf import helpers  # noqa: F401
from engine.warehouse_perf.db import ReadOnlyExecutor, build_connection_string
from engine.warehouse_perf.queries import CATALOG_SQL, QuerySpec, build_sql
from engine.warehouse_perf.sql_policy import SqlPolicyError, bind_window_parameters, validate_select_sql

SCOPE = {"primary_db_name": "WMS_DB", "secondary_db_name": None, "same_instance": False, "secondary_db_alias": None}
OK_SQL = "SELECT COUNT(*) AS n FROM dbo.t_order WHERE order_date >= :window_start AND order_date < :window_end"
TS = {"column": "start_tran_date", "time_column": "start_tran_time", "granularity": "hour"}


def ok(sql, tables=("dbo.t_order",)):
    return validate_select_sql(sql, list(tables), SCOPE)


class Policy(unittest.TestCase):
    def test_accepts_bounded_select(self):
        self.assertTrue(ok(OK_SQL).ok)

    def test_rejects_every_write_and_ddl(self):
        for bad in ("DELETE FROM dbo.t_order WHERE 1=1", "UPDATE dbo.t_order SET status='X'",
                    "INSERT INTO dbo.t_order VALUES (1)", "DROP TABLE dbo.t_order", "ALTER TABLE dbo.t_order ADD x int",
                    "EXEC sp_who", "CREATE TABLE x (a int)", "TRUNCATE TABLE dbo.t_order", "MERGE dbo.t_order AS t"):
            self.assertFalse(ok(bad).ok, bad)

    def test_rejects_stacked_statements_and_select_into(self):
        self.assertFalse(ok(OK_SQL + "; DELETE FROM dbo.t_order").ok)
        self.assertFalse(ok(OK_SQL.replace("AS n FROM", "AS n INTO #tmp FROM")).ok)

    def test_rejects_other_tables_system_objects_and_unbounded_queries(self):
        self.assertFalse(ok(OK_SQL.replace("dbo.t_order", "dbo.t_employee")).ok)
        self.assertFalse(ok("SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE 1 = :window_start AND 2 = :window_end").ok)
        self.assertFalse(ok("SELECT COUNT(*) FROM dbo.t_order").ok)

    def test_keyword_inside_literal_or_comment_does_not_hide_a_write(self):
        self.assertFalse(ok(OK_SQL + " /* harmless */ ; UPDATE dbo.t_order SET x=1").ok)
        self.assertTrue(ok(OK_SQL + " AND status <> 'UPDATE PENDING'").ok)


class GeneratedSql(unittest.TestCase):
    SPECS = [
        QuerySpec("buckets", "dbo", "t_tran_log", TS, measure="sum", measure_column="tran_qty",
                  group_warehouse="wh_id", group_process="tran_type"),
        QuerySpec("buckets", "dbo", "t_order", {"column": "ship_date", "time_column": None, "granularity": "hour"},
                  measure="count_distinct", measure_column="order_number", group_warehouse="wh_id",
                  group_dim="order_category"),
        QuerySpec("buckets", "dbo", "t_order", {"column": "ship_date", "time_column": None, "granularity": "day"},
                  measure="duration", start_ts={"column": "order_date", "time_column": None}),
        QuerySpec("backlog", "dbo", "t_order", {"column": "order_date", "time_column": None, "granularity": "hour"},
                  measure_column="order_number", done_ts={"column": "ship_date", "time_column": None},
                  group_warehouse="wh_id", group_dim="status"),
        QuerySpec("probe", "dbo", "t_tran_log", TS),
        QuerySpec("labels", "dbo", "t_tran_log", TS, group_process="tran_type", description_column="description"),
    ]

    def test_every_generated_query_passes_the_policy(self):
        for spec in self.SPECS:
            sql = build_sql(spec)
            res = validate_select_sql(sql, [spec.table_ref], SCOPE)
            self.assertTrue(res.ok, (sql, res.errors))
            self.assertTrue(sql.startswith("SELECT "))
            bound, order = bind_window_parameters(sql)
            self.assertNotIn(":window_", bound)
            self.assertTrue(set(order) <= {"window_start", "window_end"})

    def test_every_output_alias_is_bracket_quoted(self):
        # regression: "AS proc" failed on a real SQL Server (PROC is a reserved word)
        import re
        for spec in self.SPECS:
            sql = build_sql(spec)
            self.assertEqual(re.findall(r"AS\s+(?!\[|date|datetime|time|float|nvarchar)(\w+)", sql), [],
                             sql)
            self.assertNotRegex(sql, r"AS proc")

    def test_hostile_identifier_stays_a_quoted_identifier(self):
        spec = QuerySpec("buckets", "dbo", "t_order", {"column": "x]; DROP TABLE t_order--", "time_column": None,
                                                       "granularity": "hour"}, measure="count")
        sql = build_sql(spec)
        self.assertIn("[x]]; DROP TABLE t_order--]", sql)
        self.assertTrue(validate_select_sql(sql, [spec.table_ref], SCOPE).ok)

    def test_catalog_sql_is_fixed_and_otherwise_forbidden(self):
        self.assertFalse(validate_select_sql(CATALOG_SQL, ["dbo.t_order"], SCOPE, require_window_tokens=False).ok)


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.description = [("n",)]

    def execute(self, sql, *params):
        self.conn.executed.append((sql, params))

    def fetchmany(self, n):
        return [(5,)]


class FakeConn:
    def __init__(self):
        self.executed, self.rolled_back, self.committed, self.closed = [], False, False, False
        self.timeout = None

    def cursor(self):
        return FakeCursor(self)

    def rollback(self):
        self.rolled_back = True

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def ctx():
    return SimpleNamespace(db_config={"serverName": "srv", "databaseName": "WMS_DB", "username": "u",
                                      "password": "p;w{d}"}, scope=lambda: SCOPE)


class Executor(unittest.TestCase):
    def setUp(self):
        self.conns, self.args = [], []

        def connect(conn_str, **kw):
            self.args.append((conn_str, kw))
            c = FakeConn()
            self.conns.append(c)
            return c
        self.ex = ReadOnlyExecutor(connect=connect)

    def test_read_only_intent_no_autocommit_rollback_never_commit(self):
        res = self.ex.run(ctx(), OK_SQL, ["dbo.t_order"], "2026-01-01", "2026-01-02", 30, 100)
        conn_str, kw = self.args[0]
        self.assertIn("ApplicationIntent=ReadOnly", conn_str)
        self.assertIs(kw["autocommit"], False)
        c = self.conns[0]
        self.assertTrue(c.rolled_back and c.closed)
        self.assertFalse(c.committed)
        self.assertEqual(c.timeout, 30)
        self.assertEqual(res.rows_returned, 1)
        self.assertEqual(c.executed[0][0].count("?"), 2)

    def test_policy_violation_never_opens_a_connection(self):
        with self.assertRaises(SqlPolicyError):
            self.ex.run(ctx(), "DELETE FROM dbo.t_order", ["dbo.t_order"], None, None, 30, 100)
        self.assertEqual(self.conns, [])

    def test_only_the_fixed_catalog_query_may_skip_the_allowlist(self):
        with self.assertRaises(SqlPolicyError):
            self.ex.run_catalog(ctx(), CATALOG_SQL + " ; DROP TABLE x", 30, 100)
        self.ex.run_catalog(ctx(), CATALOG_SQL, 30, 100)
        self.assertTrue(self.conns[0].rolled_back)

    def test_connection_string_escapes_values(self):
        s = build_connection_string({"serverName": "srv", "databaseName": "db", "username": "u", "password": "p;w{d}"})
        self.assertIn("PWD={p;w{d}}}", s)


if __name__ == "__main__":
    unittest.main()

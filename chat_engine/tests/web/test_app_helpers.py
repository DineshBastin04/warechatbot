"""Billing, question ids, session-cookie settings, the feedback DB schema, and
import-time side effects. No database, LLM or network is touched."""
import inspect
import os
import re
import sys
import tempfile
import unittest
import uuid
from unittest.mock import MagicMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from flask import Flask  # noqa: E402

import engine.flask as ef  # noqa: E402

normalize_model_name = ef.VannaFlaskApp.normalize_model_name


class Billing(unittest.TestCase):
    def norm(self, name):
        return normalize_model_name(None, name)

    def test_mini_is_not_billed_as_full_model(self):
        self.assertEqual(self.norm("gpt-4.1-mini"), "gpt-4.1-mini")
        self.assertEqual(self.norm("gpt-4.1-mini-2025-04-14"), "gpt-4.1-mini")
        self.assertEqual(self.norm("GPT-4.1-Mini"), "gpt-4.1-mini")
        self.assertEqual(self.norm("gpt-4.1-2025-04-14"), "gpt-4.1")
        self.assertEqual(self.norm("gpt-4.1-nano"), "gpt-4.1-nano")

    def test_other_models(self):
        self.assertEqual(self.norm("gpt-5.1-2025-11-13"), "gpt-5.1")
        self.assertEqual(self.norm("gpt-4o-mini"), "gpt-4o-mini")
        self.assertEqual(self.norm("o3-mini"), "o3-mini")
        self.assertEqual(self.norm("o3"), "o3")
        self.assertEqual(self.norm("exact_match"), "exact_match")   # cache hits: unknown, cost 0
        self.assertEqual(self.norm(""), "unknown")

    def test_cost(self):
        # 1M uncached in + 1M out on mini = 0.40 + 1.60
        self.assertAlmostEqual(ef.compute_cost_usd("gpt-4.1-mini", 1_000_000, 1_000_000), 2.00)
        # half the input cached: 0.5M * 0.40 + 0.5M * 0.10
        self.assertAlmostEqual(ef.compute_cost_usd("gpt-4.1-mini", 1_000_000, 0, 500_000), 0.25)
        # cached can't exceed input
        self.assertAlmostEqual(ef.compute_cost_usd("gpt-4.1-mini", 100, 0, 10_000), 100 / 1e6 * 0.10)
        self.assertEqual(ef.compute_cost_usd("exact_match", 5000, 5000), 0.0)

    def test_every_price_entry_is_complete(self):
        for model, price in ef.MODEL_PRICING.items():
            with self.subTest(model=model):
                self.assertEqual(set(price), {"input", "cached_input", "output"})


class QuestionId(unittest.TestCase):
    def test_canonical(self):
        u = uuid.uuid4()
        self.assertEqual(ef._canonical_question_id(str(u)), str(u))
        self.assertEqual(ef._canonical_question_id(u.hex), str(u))           # 32-hex form normalised
        self.assertEqual(ef._canonical_question_id(str(u).upper()), str(u))

    def test_rejects_non_uuid(self):
        for bad in ("abc", "", None, "1; DROP TABLE users", 42):
            with self.subTest(bad=bad):
                self.assertIsNone(ef._canonical_question_id(bad))


class SessionCookie(unittest.TestCase):
    def test_matrix(self):
        secure = {"SESSION_COOKIE_SAMESITE": "None", "SESSION_COOKIE_SECURE": True,
                  "SESSION_COOKIE_PARTITIONED": True}
        # The non-Secure path now sets SameSite=Lax explicitly instead of leaving
        # it to Flask's own (version-dependent) default.
        not_secure = {"SESSION_COOKIE_SAMESITE": "Lax"}
        # (env, expected_config, expected_tab_without_secure, expected_secure_unconfigured)
        cases = [
            ({}, not_secure, False, True),
            ({"TEAMS_TAB_ENABLED": "true"}, secure, False, False),
            ({"TEAMS_TAB_ENABLED": "true", "SESSION_COOKIE_SECURE": "false"}, not_secure, True, False),
            ({"SESSION_COOKIE_SECURE": "1"}, secure, False, False),
            ({"TEAMS_TAB_ENABLED": "no", "SESSION_COOKIE_SECURE": "no"}, not_secure, False, False),
        ]
        for env, config, tab_warn, secure_unconfigured in cases:
            with self.subTest(env=env):
                self.assertEqual(
                    ef.session_cookie_settings(env), (config, tab_warn, secure_unconfigured)
                )


def _columns_of_create(sql):
    body = re.search(r"CREATE TABLE dbo\.users\s*\((.*?)\n\s*\)\s*\n\s*END", sql, re.S).group(1)
    body = re.sub(r"--[^\n]*", "", body)
    return {line.split()[0].lower() for line in body.splitlines() if line.strip()}


class FeedbackSchema(unittest.TestCase):
    def test_every_column_written_exists_in_the_table(self):
        """The bug this guards: log_user_activity wrote parent_question_id, which
        CREATE TABLE never defined, so every insert on a fresh DB failed."""
        created = _columns_of_create(inspect.getsource(ef._ensure_feedback_schema))
        source = inspect.getsource(ef.VannaFlaskApp.log_user_activity)
        insert = re.search(r"INSERT INTO dbo\.users \((.*?)\)\s*VALUES", source, re.S).group(1)
        written = {c.strip().lower() for c in insert.split(",") if c.strip()}
        self.assertTrue(written, "could not find the INSERT column list")
        self.assertEqual(written - created, set())

    def test_existing_tables_get_the_column(self):
        source = inspect.getsource(ef._ensure_feedback_schema)
        self.assertIn("ALTER TABLE dbo.users ADD parent_question_id", source)


class ImportHasNoSideEffects(unittest.TestCase):
    def test_constructor_defaults_are_not_prebuilt(self):
        for cls in (ef.VannaFlaskAPI, ef.VannaFlaskApp):
            params = inspect.signature(cls.__init__).parameters
            with self.subTest(cls=cls.__name__):
                self.assertIsNone(params["cache"].default)
                self.assertIsNone(params["auth"].default)


class SeedUsers(unittest.TestCase):
    def test_restart_does_not_reset_passwords(self):
        from engine.flask.auth import BasicAuth
        old_cwd = os.getcwd()
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            os.chdir(tmp)                      # BasicAuth uses a relative "admin_store"
            try:
                first = BasicAuth()
                meta = first.users_collection.get(ids=["admin"])["metadatas"][0]
                meta["password_hash"] = "changed-by-admin"
                first.users_collection.update(ids=["admin"], metadatas=[meta])

                second = BasicAuth()           # simulates a restart
                again = second.users_collection.get(ids=["admin"])["metadatas"][0]
                self.assertEqual(again["password_hash"], "changed-by-admin")
                self.assertEqual(len(second.users_collection.get()["ids"]), 3)
            finally:
                os.chdir(old_cwd)


class WorkspaceRef(unittest.TestCase):
    """The chat UI names a workspace; generate_sql must resolve it to an id
    rather than fall back to an unconfigured instance."""

    def resolve(self, ref):
        rows = {"ws-1": {"name": "Alpha", "display_name": "Alpha WH"}}

        class Coll:
            def get(self, ids=None, where=None):
                if ids is not None:
                    return {"ids": [i for i in ids if i in rows]}
                (field, value), = where.items()
                return {"ids": [i for i, m in rows.items() if m.get(field) == value]}

        stub = MagicMock()
        stub.workspace_collection = Coll()
        return ef.VannaFlaskApp._workspace_id_from_ref(stub, ref)

    def test_by_id_name_and_display_name(self):
        self.assertEqual(self.resolve("ws-1"), "ws-1")
        self.assertEqual(self.resolve("Alpha"), "ws-1")
        self.assertEqual(self.resolve(" Alpha WH "), "ws-1")

    def test_unknown(self):
        self.assertIsNone(self.resolve("Beta"))
        self.assertIsNone(self.resolve(""))
        self.assertIsNone(self.resolve(None))


class WorkspaceAccess(unittest.TestCase):
    def check(self, user, workspace_id, meta=None):
        stub = MagicMock()
        with patch.object(ef, "get_workspace_metadata", return_value=meta), \
                Flask(__name__).test_request_context():
            return ef.VannaFlaskApp._user_can_access_workspace(stub, user, workspace_id)

    def test_admins_any_workspace(self):
        self.assertTrue(self.check({"role": "admin"}, "ws-1"))
        self.assertTrue(self.check({"role": "superadmin"}, "ws-1"))

    def test_user_only_their_own(self):
        user = {"role": "user", "workspace": "Alpha"}
        self.assertTrue(self.check(user, "Alpha"))
        self.assertTrue(self.check(user, "ws-1", meta={"name": "Alpha"}))
        self.assertFalse(self.check(user, "ws-2", meta={"name": "Beta"}))
        self.assertFalse(self.check({"role": "user", "workspace": ""}, "ws-1", meta={"name": ""}))


class TrainedQuestionLookup(unittest.TestCase):
    """A trained question must run its stored SQL — asked with different case or
    punctuation, and asked after an earlier answer (the chat sends the previous
    SQL with every question after the first)."""

    def test_exact_key_ignores_case_spacing_and_trailing_punctuation(self):
        from engine.chromadb.chromadb_vector import ChromaDB_VectorStore
        key = ChromaDB_VectorStore._exact_key
        self.assertEqual(key("What is the average value for AMZ002?"),
                         key("  what is the  average value for amz002 "))
        self.assertEqual(key("Count the unshipped orders."), key("count the unshipped orders"))
        # wording still has to match
        self.assertNotEqual(key("What is the average value for AMZ002?"),
                            key("What is the average value for AMZ003?"))

    def _generate(self, followup, trained):
        from engine.base.base import VannaBase
        stub = MagicMock()
        stub.find_trained_sql = MagicMock(side_effect=lambda q, ws: trained.get(q))
        stub.extract_sql = lambda text: text.split("```sql\n", 1)[-1].rsplit("\n```", 1)[0]
        stub.validate_openquery_literals.return_value = (True, None)
        stub.validate_db_scope.return_value = (True, None)
        stub.get_similar_question_sql.return_value = {"sql": [], "documentation": [], "context": {}}
        stub.submit_prompt.return_value = ("SELECT 'from the LLM'", 1, 1, 1, "gpt")
        return VannaBase.generate_sql(stub, question="SELECT 1 FROM t_prev", followup_sql=followup,
                                      workspace="test"), stub

    def test_followup_that_is_a_trained_question_runs_its_sql(self):
        (sql, *_rest, model), stub = self._generate(
            "What is the average value for AMZ002?",
            {"What is the average value for AMZ002?": "SELECT AVG(order_value) FROM t_erpnext_order_stage"})
        self.assertEqual((sql, model), ("SELECT AVG(order_value) FROM t_erpnext_order_stage", "exact_match"))
        stub.submit_prompt.assert_not_called()

    def test_short_reply_stays_a_followup(self):
        # "Warehouse ATH1" is (oddly) trained, but as a reply it means "the previous query, for ATH1"
        (_sql, *_rest, model), stub = self._generate("Warehouse ATH1", {"Warehouse ATH1": "SELECT * FROM t_whse"})
        self.assertNotEqual(model, "exact_match")
        stub.submit_prompt.assert_called_once()


class DatasetRoute(unittest.TestCase):
    """Dataset questions (and close rephrasings) must reach the query pipeline,
    not prediction/scheduling — unless they ask for something to be sent."""

    def route(self, question, trained=False, distance=None):
        stub = MagicMock()
        stub.find_trained_sql.return_value = "SELECT 1" if trained else None
        stub.nearest_trained_distance.return_value = distance
        with patch.object(ef, "vn", stub):
            return ef._dataset_route(question, "demo")

    def test_exact_trained_question(self):
        self.assertEqual(self.route("Show me orders at risk of missing delivery.", trained=True), "exact")

    def test_close_rephrasing_goes_to_the_dataset(self):
        self.assertEqual(self.route("orders at risk of missing delivery", distance=0.2), "near")

    def test_far_from_every_trained_question(self):
        self.assertIsNone(self.route("forecast next month's demand", distance=1.1))

    def test_delivery_requests_stay_with_scheduling(self):
        for q in ("send a mail to suriyan on orders at risk of missing delivery",
                  "email me daily the orders at risk of missing delivery",
                  "notify me when any order is at risk of missing delivery"):
            with self.subTest(q=q):
                self.assertIsNone(self.route(q, distance=0.1))

    def test_dataset_words_that_look_like_scheduling_still_match(self):
        # "watch" / "cancelled" are ordinary words in the trained questions
        self.assertEqual(self.route("which orders should we watch for delivery", distance=0.05), "near")
        self.assertEqual(self.route("cancelled orders still being picked", distance=0.1), "near")


class NewQuestionDuringSchedulePrompt(unittest.TestCase):
    """A fresh question typed while "What would you like me to send you?" is
    open is answered, not scheduled; real answers to the prompt still continue it."""

    def test_fresh_questions_leave_the_prompt(self):
        for q in ("how many warehpuse do we ahve", "what are the open orders",
                  "show me today's picks", "open orders by customer?"):
            with self.subTest(q=q):
                self.assertTrue(ef._is_new_question(q))

    def test_answers_to_the_prompt_continue_it(self):
        for q in ("suriyan", "the sales report", "send the open orders to suriyan",
                  "email what we discussed to akshaya", "every monday at 9am", "/list", ""):
            with self.subTest(q=q):
                self.assertFalse(ef._is_new_question(q))


if __name__ == "__main__":
    unittest.main()

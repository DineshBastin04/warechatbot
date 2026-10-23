"""Path classification, role normalisation, and the auth decorators' responses.

Uses a bare Flask app with access_control installed (and the real decorators
bound to a stub) rather than building VannaFlaskApp, which needs ChromaDB,
SQL Server and an LLM config."""
import os
import sys
import unittest
from unittest.mock import MagicMock

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from flask import Flask  # noqa: E402

import engine.flask as ef  # noqa: E402
from engine.flask.access_control import ADMIN_ROLES, classify_path, install_access_control, normalize_role  # noqa: E402


class ClassifyPath(unittest.TestCase):
    CASES = {
        "/": "public",
        "/assets/app.js": "public",
        "/api/messages": "public",
        "/superadmin": "superadmin",
        "/superadmin/settings": "superadmin",
        "/superadmins_report": "login",         # prefix alone must not match
        "/admin": "admin",
        "/workspace": "admin",
        "/api/v0/train": "admin",
        "/api/v0/remove_training_data": "admin",
        "/api/v0/remove_training_data_module": "admin",
        "/api/delete_user/42": "admin",
        "/api/v0/generate_sql": "login",
        "/user": "login",
    }

    def test_table(self):
        for path, expected in self.CASES.items():
            with self.subTest(path=path):
                self.assertEqual(classify_path(path), expected)


class NormalizeRole(unittest.TestCase):
    def test_values(self):
        self.assertEqual(normalize_role("Admin"), "admin")
        self.assertEqual(normalize_role(" SUPERADMIN "), "superadmin")
        self.assertEqual(normalize_role(None), "user")
        self.assertEqual(normalize_role(""), "user")
        self.assertEqual(normalize_role("   "), "user")


def _guarded_app():
    app = Flask(__name__)
    app.secret_key = "test"
    install_access_control(app)

    @app.route("/login")
    def login():
        return "login page"

    for path in ("/admin", "/superadmin", "/user", "/api/v0/generate_sql"):
        app.add_url_rule(path, path, lambda: "ok")
    return app


class GuardResponses(unittest.TestCase):
    def setUp(self):
        self.app = _guarded_app()

    def client_as(self, role):
        c = self.app.test_client()
        with c.session_transaction() as s:
            s["username"] = "someone"
            s["role"] = role
        return c

    def test_anonymous_api_gets_401_json(self):
        r = self.app.test_client().get("/api/v0/generate_sql")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.get_json()["error"], "Authentication required")

    def test_anonymous_page_navigation_redirects(self):
        r = self.app.test_client().get("/user", headers={"Sec-Fetch-Mode": "navigate"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.location.endswith("/login"))

    def test_anonymous_form_post_redirects_not_json(self):
        r = self.app.test_client().post("/user", headers={"Sec-Fetch-Mode": "navigate"})
        self.assertEqual(r.status_code, 302)

    def test_admin_paths(self):
        self.assertEqual(self.client_as("user").get("/admin").status_code, 403)
        self.assertEqual(self.client_as("admin").get("/admin").status_code, 200)
        self.assertEqual(self.client_as("Admin").get("/admin").status_code, 200)       # case-insensitive
        self.assertEqual(self.client_as("superadmin").get("/admin").status_code, 200)

    def test_superadmin_paths(self):
        self.assertEqual(self.client_as("admin").get("/superadmin").status_code, 403)
        self.assertEqual(self.client_as("SuperAdmin").get("/superadmin").status_code, 200)


class Decorators(unittest.TestCase):
    """requires_auth / requires_role, bound to a stub in place of the real app."""

    def setUp(self):
        self.stub = MagicMock()
        self.stub.auth.get_user.return_value = None
        requires_auth = ef.VannaFlaskAPI.requires_auth.__get__(self.stub)
        requires_role = ef.VannaFlaskAPI.requires_role.__get__(self.stub)

        app = Flask(__name__)
        app.secret_key = "test"
        app.add_url_rule("/login", "login", lambda: "login page")

        @app.route("/api/v0/thing")
        @requires_auth
        def api_thing(user=None):
            return "ok"

        @app.route("/page")
        @requires_auth
        def page(user=None):
            return "ok"

        @app.route("/api/v0/admin_thing")
        @requires_role(list(ADMIN_ROLES))
        @requires_auth
        def admin_thing(user=None):
            return "ok"

        self.client = app.test_client()

    def test_requires_auth_api_returns_401(self):
        r = self.client.get("/api/v0/thing")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.get_json()["type"], "error")

    def test_requires_auth_page_redirects(self):
        r = self.client.get("/page", headers={"Sec-Fetch-Mode": "navigate"})
        self.assertEqual(r.status_code, 302)

    def test_requires_role_anonymous_api_returns_401(self):
        self.assertEqual(self.client.get("/api/v0/admin_thing").status_code, 401)

    def test_requires_role_accepts_any_case_and_superadmin(self):
        for role, expected in (("admin", 200), ("ADMIN", 200), ("superadmin", 200), ("user", 403)):
            with self.subTest(role=role):
                self.stub.auth.get_user.return_value = {"username": "u", "role": role}
                self.assertEqual(self.client.get("/api/v0/admin_thing").status_code, expected)


if __name__ == "__main__":
    unittest.main()

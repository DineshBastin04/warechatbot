"""
Deny-by-default access control for every route.

Most routes predate any auth decorator, so the per-route ``requires_auth`` /
``requires_role`` decorators can't be the only line of defense: a route
missing one was reachable anonymously. This includes routes that return
database passwords or run arbitrary SQL. This guard runs before every request
and classifies the path as:

- public:     reachable without a session;
- login:      any logged-in user (the default for anything unlisted);
- admin:      admin or superadmin;
- superadmin: superadmin only.

Route decorators still apply on top of this; the guard only ever tightens access.
"""

from flask import jsonify, redirect, request, session, url_for

ADMIN_ROLES = ("admin", "superadmin")

PUBLIC_EXACT = {
    "/",
    "/vanna.svg",
    "/favicon.ico",
    "/auth/logout",
    "/api/messages",          # Teams bot: authenticated by its own Bot Framework JWT check
    "/teams/tab",             # Teams tab bootstrap page (runs SSO)
    "/teams/auth-start",      # Teams SSO one-time consent popup (opens Entra directly)
    "/teams/auth-end",        # Teams SSO consent popup redirect target
    "/auth/teams-sso",        # validates its own Entra token
}
PUBLIC_PREFIXES = ("/assets/", "/static/")

SUPERADMIN_PREFIXES = ("/superadmin",)

ADMIN_EXACT = {
    "/workspace", "/admin",
    "/get_workspaces", "/save_workspace", "/save-llm-config", "/save-ai-options",
    "/api/update_workspace_settings", "/save_connection", "/test_connection",
    "/get_connections", "/delete_connection", "/save_training_data", "/train-model",
    "/api/v0/train_documentation", "/api/v0/edit_training_data",
    "/api/v0/remove_training_data_module", "/get-saved-llms", "/get-ollama-models",
    "/validate-openai-api", "/initialize-vanna", "/api/v0/get_columns",
    "/api/v0/test_sql_query", "/api/v0/get_tables",
    "/save_prediction_config", "/save_anomaly_config", "/delete_prediction_config",
    "/delete_anomaly_config", "/api/v0/get_prediction_suggestions",
    "/api/v0/get_anomaly_suggestions", "/api/v0/get_agent_config",
    "/api/v0/save_agent_config", "/api/v0/test_agent_alert",
    "/api/v0/run_agent_query", "/api/v0/download_agent_data", "/api/v0/generate_insight",
    "/save_teams_config", "/get_teams_config",
    "/api/add_user", "/api/list_users", "/api/update_user", "/api/update_user_config",
    "/api/workspaces",
    "/api/get_feedback_config", "/api/save_feedback_config", "/api/test_feedback_email",
    "/api/v0/get_workspace_email_config", "/api/v0/save_workspace_email_config",
    "/api/sop/upload", "/api/sop/list",
    "/apidocs", "/apidocs/", "/apispec_1.json",
    # Legacy hardcoded prediction endpoints (no frontend caller)
    "/api/v0/deliverytimeprediction", "/api/v0/shipmentdelayprediction",
    "/api/v0/jobforecasting", "/api/v0/inventorydemandforecasting",
    "/api/v0/stockoutprediction", "/api/v0/pricetrendprediciton",
    "/api/v0/orderfulfillmenttimeprediction", "/api/v0/orderdelayprediction",
    "/api/v0/employeeperformanceprediction", "/api/v0/taskcompletionprediction",
    "/api/v0/anomalydetection",
}
ADMIN_PREFIXES = (
    "/update_workspace/", "/delete_workspace/", "/connect_workspace/",
    "/update-llm/", "/delete-llm/", "/api/delete_user/", "/api/sop/delete/",
    "/_debug/", "/_cache", "/api/v0/scheduled_agents",
    "/api/v0/reset_wizard/", "/api/v0/device_reset", "/api/v0/unpick_agent/",
    "/flasgger_static/", "/api/teams/",
)


def classify_path(path):
    if path in PUBLIC_EXACT or path.startswith(PUBLIC_PREFIXES):
        return "public"
    if path.startswith(SUPERADMIN_PREFIXES):
        return "superadmin"
    if path in ADMIN_EXACT or path.startswith(ADMIN_PREFIXES):
        return "admin"
    return "login"


def _wants_json(path):
    return (
        path.startswith(("/api/", "/_"))
        or request.method != "GET"
        or request.is_json
        or request.accept_mimetypes.best == "application/json"
    )


def install_access_control(flask_app):
    @flask_app.before_request
    def _enforce_access():
        path = request.path
        level = classify_path(path)
        if level == "public":
            return None

        if not session.get("username"):
            if _wants_json(path):
                return jsonify({"type": "error", "error": "Authentication required"}), 401
            return redirect(url_for("login"))

        role = str(session.get("role") or "user").lower()
        if level == "admin" and role not in ADMIN_ROLES:
            return jsonify({"type": "error", "error": "Permission denied"}), 403
        if level == "superadmin" and role != "superadmin":
            return jsonify({"type": "error", "error": "Permission denied"}), 403
        return None

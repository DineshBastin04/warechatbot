"""
Microsoft Teams integration: chat bot (/api/messages), personal tab with Teams
SSO (/teams/tab, /auth/teams-sso), admin status + app package download
(/api/teams/*), and proactive delivery of scheduled-agent results.

Everything is driven by .env (see TeamsSettings). With MICROSOFT_APP_* unset
the bot stays off and /api/messages answers 503; the rest of the app is unaffected.
"""

import logging

from flask import Response, jsonify, request, session

from . import cards, env_config
from .bridge import register_bridge
from .manifest import build_package
from .settings import TeamsSettings
from .tab import register_tab

logger = logging.getLogger(__name__)

# Where the Teams tab may be framed. Everything else can't frame the app
# (clickjacking protection) — only the app itself.
_TEAMS_FRAME_ANCESTORS = (
    "'self' https://teams.microsoft.com https://*.teams.microsoft.com https://*.cloud.microsoft "
    "https://*.microsoft365.com https://*.office.com https://outlook.office.com https://outlook.office365.com"
)


def register_teams(app):
    settings = TeamsSettings.from_env()
    flask_app = app.flask_app
    app.teams_settings = settings
    app.teams_runtime = None

    missing = settings.missing_for_bot()
    if settings.bot_enabled and not missing:
        try:
            from .handlers import register_handlers
            from .runtime import TeamsBotRuntime

            runtime = TeamsBotRuntime(app, settings)
            register_handlers(runtime)
            app.teams_runtime = runtime
            app.teams_proactive_sender = lambda aad_id, text, rows=None: runtime.send_proactive(
                aad_id, lambda: cards.scheduled_result_message(text, rows)
            )
            logger.info(f"Teams bot started (app id {settings.app_id}).", extra={"admin": True})
        except Exception as e:
            logger.error(f"Teams bot failed to start: {e}", exc_info=True, extra={"admin": True})
    elif settings.bot_enabled:
        logger.warning(f"Teams bot disabled — missing {', '.join(missing)} in .env", extra={"admin": True})

    register_bridge(flask_app, lambda: app.teams_runtime)
    register_tab(flask_app, app, settings)

    @flask_app.after_request
    def _frame_ancestors(response):
        if "Content-Security-Policy" not in response.headers:
            ancestors = _TEAMS_FRAME_ANCESTORS if settings.tab_enabled else "'self'"
            response.headers["Content-Security-Policy"] = f"frame-ancestors {ancestors}"
        return response

    @flask_app.route("/api/teams/status", methods=["GET"])
    def teams_status():
        base = settings.public_base_url
        return jsonify({
            "bot_enabled": settings.bot_enabled,
            "bot_running": app.teams_runtime is not None,
            "missing_for_bot": settings.missing_for_bot(),
            "tab_enabled": settings.tab_enabled,
            "missing_for_tab": settings.missing_for_tab(),
            "missing_for_package": _missing_for_package(settings),
            "bot_app_id": settings.app_id,
            "tenant_id": settings.tenant_id,
            "teams_app_id": settings.teams_app_id,
            "sso_resource": settings.sso_resource,
            "public_base_url": base,
            "messaging_endpoint": f"{base}/api/messages" if base else "",
            "tab_url": f"{base}/teams/tab" if base else "",
        })

    @flask_app.route("/api/teams/config", methods=["GET"])
    def teams_config_get():
        return jsonify(env_config.describe(settings))

    @flask_app.route("/api/teams/config", methods=["POST"])
    def teams_config_save():
        # With the Teams tab on, the session cookie is SameSite=None, so a
        # cross-site form post would carry it. Requiring a JSON body forces a
        # CORS preflight the server never grants, which blocks that.
        if not request.is_json:
            return jsonify({"error": "Expected a JSON body"}), 415
        try:
            result = env_config.save(request.get_json(silent=True), settings, changed_by=session.get("username"))
        except env_config.ConfigError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(result)

    @flask_app.route("/api/teams/manifest.zip", methods=["GET"])
    def teams_manifest_package():
        missing_pkg = _missing_for_package(settings)
        if missing_pkg:
            return jsonify({"error": f"Set {', '.join(missing_pkg)} in .env before building the Teams app package."}), 400
        return Response(
            build_package(settings),
            mimetype="application/zip",
            headers={"Content-Disposition": "attachment; filename=wai-teams-app.zip"},
        )


def _missing_for_package(settings):
    required = {
        "MICROSOFT_APP_ID": settings.app_id,
        "TEAMS_APP_ID": settings.teams_app_id,
        "PUBLIC_BASE_URL": settings.public_base_url,
    }
    return [name for name, value in required.items() if not value]

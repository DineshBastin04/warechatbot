"""
POST /api/messages — the Azure Bot messaging endpoint.

Every request is authenticated against the Bot Framework's signed JWT
(JwtTokenValidator: signature, audience = our app id, issuer/tenant) before
anything else happens. Message turns are then scheduled on the bot's event loop
and the request returns 202 immediately. The bot keeps "typing…" and replies
into the same conversation when the answer is ready, so a slow query never trips
Teams' ~15 s timeout and its automatic retry. Invoke activities need a
synchronous body, so the route waits for those.
"""

import logging

from flask import jsonify, request
from microsoft_agents.activity import Activity

logger = logging.getLogger(__name__)

_GENERIC_AUTH_ERROR = {"error": "Invalid token or authentication failed."}


def _bearer_token(header):
    parts = (header or "").split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def _log_turn_failure(future):
    exc = future.exception()
    if exc is not None:
        logger.error(f"Teams: turn processing failed: {exc}", exc_info=exc, extra={"admin": True})


def register_bridge(flask_app, get_runtime):
    @flask_app.route("/api/messages", methods=["POST"])
    def teams_messages():
        runtime = get_runtime()
        if runtime is None:
            return jsonify({"error": "The Teams bot is not configured on this server."}), 503

        token = _bearer_token(request.headers.get("Authorization"))
        if not token:
            return jsonify(_GENERIC_AUTH_ERROR), 401
        try:
            claims = runtime.submit(runtime.validator.validate_token(token)).result(timeout=20)
        except Exception as e:
            logger.warning(f"Teams: rejected request with invalid token ({type(e).__name__})", extra={"admin": True})
            return jsonify(_GENERIC_AUTH_ERROR), 401

        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify({"error": "Invalid JSON"}), 400
        try:
            activity = Activity.model_validate(body)
        except Exception:
            return jsonify({"error": "Invalid activity"}), 400
        if not activity.type or not activity.conversation or not activity.conversation.id:
            return jsonify({"error": "Activity must have type and conversation.id"}), 400
        if not runtime.adapter._validate_service_url(claims, activity):
            return jsonify({"error": "Service URL is not allowed."}), 401

        future = runtime.submit(runtime.adapter.process_activity(claims, activity, runtime.agent.on_turn))

        if activity.type == "invoke":
            try:
                invoke_response = future.result(timeout=10)
            except Exception as e:
                logger.error(f"Teams: invoke failed: {e}", exc_info=True, extra={"admin": True})
                return jsonify({"error": "Invoke failed"}), 500
            if invoke_response is None:
                return jsonify(None), 501
            return jsonify(invoke_response.body), invoke_response.status or 200

        future.add_done_callback(_log_turn_failure)
        return "", 202

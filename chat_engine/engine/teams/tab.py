"""
Teams personal tab: GET /teams/tab bootstraps Teams single sign-on, then
POST /auth/teams-sso turns the Entra token into a normal WAI session and sends
the user to the existing chat UI (/home) — the same chat, voice included,
inside Teams.
"""

import logging
import threading

import jwt
from flask import Response, jsonify, request, session
from jwt import PyJWKClient

from .identity import IdentityError, build_chat_context, find_app_user

logger = logging.getLogger(__name__)

TEAMS_JS_URL = "https://res.cdn.office.net/teams-js/2.57.0/js/MicrosoftTeams.min.js"

_jwk_clients = {}
_jwk_lock = threading.Lock()


def _jwk_client(path_segment):
    with _jwk_lock:
        if path_segment not in _jwk_clients:
            _jwk_clients[path_segment] = PyJWKClient(
                f"https://login.microsoftonline.com/{path_segment}/discovery/v2.0/keys", cache_keys=True
            )
        return _jwk_clients[path_segment]


def validate_sso_token(token, settings):
    """Validate a Teams SSO (Entra v2) access token issued to our tab.
    Returns its claims; raises jwt.PyJWTError / ValueError on anything off.

    The app registration is multi-tenant (its home tenant, MICROSOFT_APP_TENANT_ID,
    can differ from the tenant Teams users actually sign in from), so signing keys
    are fetched from the shared "common" endpoint and the issuer is checked against
    the token's own tid rather than against a single fixed tenant."""
    signing_key = _jwk_client("common").get_signing_key_from_jwt(token)
    audiences = [a for a in (settings.app_id, settings.sso_resource) if a]
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=audiences,
        leeway=60,
        options={"require": ["exp", "iat", "aud", "tid", "oid"], "verify_iss": False},
    )
    tid = str(claims.get("tid", ""))
    if claims.get("iss") != f"https://login.microsoftonline.com/{tid}/v2.0":
        raise ValueError("Unexpected token issuer")
    if settings.enforce_tenant and tid.lower() != settings.tenant_id.lower():
        raise ValueError("Token is from another tenant")
    if "access_as_user" not in str(claims.get("scp", "")).split():
        raise ValueError("Token lacks the access_as_user scope")
    return claims


_TAB_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>WAI</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="__TEAMS_JS__"></script>
<style>
  :root { --bg:#f5f7fb; --fg:#1f2937; --muted:#6b7280; --accent:#4f46e5; }
  @media (prefers-color-scheme: dark) { :root { --bg:#1f1f1f; --fg:#f3f4f6; --muted:#9ca3af; --accent:#818cf8; } }
  body { margin:0; font-family:"Segoe UI",system-ui,sans-serif; background:var(--bg); color:var(--fg);
         display:flex; align-items:center; justify-content:center; min-height:100vh; }
  .box { max-width:420px; padding:24px; text-align:center; }
  .muted { color:var(--muted); font-size:14px; }
  a { color:var(--accent); }
</style></head>
<body><div class="box">
  <h2>Warehouse Intelligence</h2>
  <p id="status" class="muted">Signing you in…</p>
  <p id="fallback" class="muted" style="display:none">
    <a href="/" id="login-link">Sign in with your WAI username and password</a></p>
</div>
<script>
(async function () {
  const status = document.getElementById("status");
  const fail = (msg) => { status.textContent = msg; document.getElementById("fallback").style.display = "block"; };

  const finishSignIn = async (token) => {
    const res = await fetch("/auth/teams-sso", {
      method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: token })
    });
    const data = await res.json().catch(() => ({}));
    if (res.ok && data.redirect) { window.location.replace(data.redirect); return; }
    fail(data.error || "Sign-in failed.");
  };

  try {
    await microsoftTeams.app.initialize();
    let token;
    try {
      token = await microsoftTeams.authentication.getAuthToken();
    } catch (silentErr) {
      // First time this app is used from this tenant: nobody has consented yet,
      // so the silent token request fails. Open a one-time consent popup, then
      // retry the silent request — it succeeds from then on.
      status.textContent = "One-time sign-in — a popup will ask you to approve access…";
      await microsoftTeams.authentication.authenticate({
        url: window.location.origin + "/teams/auth-start",
        width: 600, height: 535,
      });
      status.textContent = "Signing you in…";
      token = await microsoftTeams.authentication.getAuthToken();
    }
    await finishSignIn(token);
  } catch (e) {
    fail("Teams sign-in isn't available here (" + (e && e.message ? e.message : e) + ").");
  }
})();
</script></body></html>
"""

_AUTH_START_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Sign in</title>
<script src="__TEAMS_JS__"></script></head>
<body>
<script>
function randomString(len) {
  const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  let out = "";
  for (let i = 0; i < len; i++) out += chars[Math.floor(Math.random() * chars.length)];
  return out;
}

microsoftTeams.app.initialize().then(() => {
  return microsoftTeams.app.getContext();
}).then((context) => {
  const tenantId = (context.user && context.user.tenant && context.user.tenant.id) || "organizations";
  const loginHint = (context.user && context.user.loginHint) || "";
  const params = new URLSearchParams({
    client_id: "__APP_ID__",
    response_type: "id_token",
    response_mode: "fragment",
    scope: "__SSO_RESOURCE__/access_as_user openid profile",
    redirect_uri: window.location.origin + "/teams/auth-end",
    nonce: randomString(16),
    login_hint: loginHint,
  });
  window.location.assign(`https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/authorize?${params.toString()}`);
}).catch((e) => {
  document.body.textContent = "Couldn't start sign-in: " + (e && e.message ? e.message : e);
});
</script></body></html>
"""

_AUTH_END_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Signing in…</title>
<script src="__TEAMS_JS__"></script></head>
<body>
<script>
function parseFragment(hash) {
  const out = {};
  new URLSearchParams((hash || "").replace(/^#/, "")).forEach((v, k) => { out[k] = v; });
  return out;
}

microsoftTeams.app.initialize().then(() => {
  const result = parseFragment(window.location.hash);
  if (result.id_token) {
    microsoftTeams.authentication.notifySuccess(result.id_token);
  } else {
    microsoftTeams.authentication.notifyFailure(result.error_description || result.error || "consent_failed");
  }
}).catch((e) => {
  document.body.textContent = "Sign-in failed: " + (e && e.message ? e.message : e);
});
</script></body></html>
"""


def register_tab(flask_app, app, settings):
    @flask_app.route("/teams/tab")
    def teams_tab():
        return Response(_TAB_HTML.replace("__TEAMS_JS__", TEAMS_JS_URL), mimetype="text/html")

    @flask_app.route("/teams/auth-start")
    def teams_auth_start():
        html = (_AUTH_START_HTML
                .replace("__TEAMS_JS__", TEAMS_JS_URL)
                .replace("__APP_ID__", settings.app_id)
                .replace("__SSO_RESOURCE__", settings.sso_resource))
        return Response(html, mimetype="text/html")

    @flask_app.route("/teams/auth-end")
    def teams_auth_end():
        return Response(_AUTH_END_HTML.replace("__TEAMS_JS__", TEAMS_JS_URL), mimetype="text/html")

    @flask_app.route("/auth/teams-sso", methods=["POST"])
    def teams_sso():
        missing = settings.missing_for_tab()
        if missing:
            return jsonify({"error": f"Teams sign-in isn't configured on the server (missing {', '.join(missing)})."}), 503

        token = (request.get_json(silent=True) or {}).get("token")
        if not token:
            return jsonify({"error": "Missing token"}), 400
        try:
            claims = validate_sso_token(token, settings)
        except Exception as e:
            logger.warning(f"Teams SSO: rejected token ({type(e).__name__}: {e})", extra={"admin": True})
            return jsonify({"error": "Your Teams sign-in couldn't be verified."}), 401

        aad_id = claims.get("oid")
        email = (claims.get("email") or claims.get("preferred_username") or claims.get("upn") or "").strip().lower()
        user_id, meta = find_app_user(app, aad_id, email)
        if not user_id:
            return jsonify({"error": f"{email or 'Your account'} isn't registered in WAI. Ask your admin to add it as your user's email."}), 403

        try:
            ctx = build_chat_context(app, user_id, meta, aad_id, email)
        except IdentityError as e:
            return jsonify({"error": str(e)}), 403

        instance, err = app.vanna_registry.get_or_build(ctx.workspace_id)
        if instance is None:
            return jsonify({"error": f"Your workspace isn't ready: {err}"}), 400

        app.auth.establish_session(meta.get("username"), ctx.role, user_id=user_id)
        session["workspace_id"] = ctx.workspace_id
        session["teams_tab"] = True
        app.cache.refresh_cache_for_user(user_id, ctx.workspace_id)
        logger.info(f"Teams SSO: {meta.get('username')} signed in to workspace {ctx.workspace_name}", extra={"admin": True})
        return jsonify({"redirect": f"/home?workspace_id={ctx.workspace_id}&inTeams=1"})

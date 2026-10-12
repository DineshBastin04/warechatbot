"""
Server-side workspace authorization for every agent route, chat command and
job action. The client-supplied workspace_id is only a *request*; access is
decided here from the authenticated user record (BasicAuth.get_user ->
{"username", "role", "workspace"}).

- superadmin: every workspace.
- admin: every workspace if their user record has no workspace pinned (the
  app's existing meaning of an admin), otherwise only that workspace.
- user: read-only access (reports, chat commands that don't send or
  schedule) to their own pinned workspace only.
A workspace that doesn't exist and one the caller may not access produce the
same response for non-superadmins, so IDs can't be probed.
"""
ADMIN_ROLES = ("admin", "superadmin")


def _norm(v):
    return str(v or "").strip().casefold()


def _matches(user_workspace, ctx):
    want = _norm(user_workspace)
    if not want:
        return False
    candidates = {_norm(ctx.workspace_id), _norm(ctx.name), _norm(ctx.display_name),
                  _norm(str(ctx.name).replace("_", " ")), _norm(str(ctx.display_name).replace(" ", "_"))}
    return want in candidates


def role_of(user):
    return (user or {}).get("role") if isinstance(user, dict) else getattr(user, "role", None)


def username_of(user):
    return (user or {}).get("username") if isinstance(user, dict) else getattr(user, "username", None)


def authorize(user, ctx, need_admin=False):
    """Returns (ok, http_status, message)."""
    if not user or not username_of(user):
        return False, 401, "authentication required"
    role = role_of(user)
    if role == "superadmin":
        return (True, 200, None) if ctx is not None else (False, 404, "workspace not found")
    denied = (False, 403, "workspace not found or you are not authorized for it")
    if ctx is None:
        return denied
    pinned = (user.get("workspace") if isinstance(user, dict) else getattr(user, "workspace", None)) or ""
    if role == "admin":
        return (True, 200, None) if (not str(pinned).strip() or _matches(pinned, ctx)) else denied
    if need_admin:
        return False, 403, "this action requires an admin"
    return (True, 200, None) if _matches(pinned, ctx) else denied


def is_admin(user):
    return role_of(user) in ADMIN_ROLES

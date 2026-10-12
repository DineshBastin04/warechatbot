"""
Map a Microsoft Teams user to a WAI user and workspace.

A Teams user is matched to an app user by the `email` an admin set on the
account (User Management). The first match stores the user's Entra object id
on the account (`aad_object_id`), so later messages resolve without another
lookup and a renamed mailbox can't take over someone else's account.

Workspace: a plain user always gets their own assigned workspace. Admins
(who have no fixed workspace) get the one chosen with `workspace <name>`,
defaulting to the first Teams-enabled workspace. Either way the workspace must
have Teams enabled in the admin panel.
"""

import json
import logging

from ..flask.chat_context import ChatContext

logger = logging.getLogger(__name__)

ADMIN_ROLES = ("admin", "superadmin")


class IdentityError(Exception):
    """A user-facing reason this Teams user can't be served."""


def teams_enabled_workspaces(app):
    """[(workspace_id, metadata)] for every workspace with Teams enabled."""
    result = []
    records = app.workspace_collection.get()
    for wid, meta in zip(records.get("ids") or [], records.get("metadatas") or []):
        try:
            if json.loads((meta or {}).get("teams_config") or "{}").get("enabled"):
                result.append((wid, meta))
        except (ValueError, TypeError):
            continue
    return result


def _workspace_by_name(app, name):
    records = app.workspace_collection.get()
    for wid, meta in zip(records.get("ids") or [], records.get("metadatas") or []):
        if name and (name == wid or name in ((meta or {}).get("name"), (meta or {}).get("display_name"))):
            return wid, meta
    return None, None


def _is_teams_enabled(meta):
    try:
        return bool(json.loads((meta or {}).get("teams_config") or "{}").get("enabled"))
    except (ValueError, TypeError):
        return False


def find_app_user(app, aad_object_id, email):
    """(user_id, metadata) for this Teams identity, linking the Entra object id on
    first match by email. Returns (None, None) when the user isn't registered."""
    user_id, meta = app.find_user_by_aad_id(aad_object_id)
    if user_id:
        return user_id, meta
    user_id, meta = app.find_user_by_email(email)
    if not user_id:
        return None, None
    linked = (meta or {}).get("aad_object_id")
    if linked and aad_object_id and linked != aad_object_id:
        # Email matches but the account is already bound to a different Entra
        # user — refuse rather than let a reassigned mailbox take it over.
        logger.warning(f"Teams: {email} matches user {user_id}, already linked to another Entra id", extra={"admin": True})
        return None, None
    if aad_object_id and not linked:
        updated = dict(meta)
        updated["aad_object_id"] = aad_object_id
        app.users_collection.update(ids=[user_id], metadatas=[updated])
        meta = updated
        logger.info(f"Teams: linked Entra user {aad_object_id} to app user {meta.get('username')}", extra={"admin": True})
    return user_id, meta


def build_chat_context(app, user_id, meta, aad_object_id, email, preferred_workspace_id=None):
    """ChatContext for a resolved app user, or IdentityError with the reason."""
    role = str(meta.get("role") or "user").lower()
    username = meta.get("username")

    if role in ADMIN_ROLES:
        enabled = teams_enabled_workspaces(app)
        chosen = next(((wid, m) for wid, m in enabled if wid == preferred_workspace_id), None)
        if not chosen:
            if not enabled:
                raise IdentityError("No workspace has Teams enabled yet — enable it under Workspace Admin → Teams Configuration.")
            chosen = enabled[0]
        workspace_id, ws_meta = chosen
    else:
        assigned = meta.get("workspace") or ""
        if not assigned or not meta.get("workspace_valid", False):
            raise IdentityError("Your WAI account isn't assigned to an active workspace. Please contact your admin.")
        workspace_id, ws_meta = _workspace_by_name(app, assigned)
        if not workspace_id:
            raise IdentityError("Your assigned workspace no longer exists. Please contact your admin.")
        if not _is_teams_enabled(ws_meta):
            raise IdentityError("Teams isn't enabled for your workspace yet. Ask your admin to enable it.")

    return ChatContext(
        workspace_id=str(workspace_id),
        workspace_name=ws_meta.get("name") or str(workspace_id),
        user_id=user_id,
        username=username,
        role=role,
        channel="teams",
        teams_aad_id=aad_object_id,
        email=(email or meta.get("email") or None),
    )

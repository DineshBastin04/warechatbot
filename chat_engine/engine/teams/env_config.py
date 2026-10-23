"""
Read and write the Teams credentials in chat_engine/.env from the admin panel.

Changes go to the file only. The running bot keeps the credentials it started
with (they're baked into its MSAL connection, JWT validator and route closures),
so a saved change applies on the next server restart; describe() reports when
the file and the running server disagree.
"""

import logging
import os
import re
import threading

from dotenv import dotenv_values, set_key

from .settings import TeamsSettings, default_sso_resource

logger = logging.getLogger(__name__)

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")

_GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_BASE_URL = re.compile(r"^https://[A-Za-z0-9.-]+(:\d{1,5})?$")
_SSO_RESOURCE = re.compile(r"^api://[A-Za-z0-9._~:/-]+$")
# The characters Entra uses in generated client secrets. Values are written
# unquoted, so anything that dotenv would treat specially ($, #, quotes,
# whitespace) must never get in.
_SECRET = re.compile(r"^[A-Za-z0-9._~-]{8,256}$")

_COMPARED_FIELDS = ("app_id", "app_password", "tenant_id", "public_base_url", "sso_resource")

_write_lock = threading.Lock()


class ConfigError(ValueError):
    """A user-facing reason the submitted credentials were rejected."""


def _saved_values():
    return {k: (v or "") for k, v in dotenv_values(ENV_PATH).items()} if os.path.exists(ENV_PATH) else {}


def _restart_required(saved, running):
    return any(getattr(saved, f) != getattr(running, f) for f in _COMPARED_FIELDS)


def describe(running):
    """What the admin form shows: the values saved in .env (never the secret
    itself), and whether they differ from what the server is running with."""
    values = _saved_values()
    saved = TeamsSettings.from_mapping(values)
    return {
        "app_id": saved.app_id,
        "tenant_id": saved.tenant_id,
        "public_base_url": saved.public_base_url,
        "sso_resource": values.get("TEAMS_SSO_RESOURCE", "").strip(),
        "sso_resource_default": default_sso_resource(saved.public_base_url, saved.app_id),
        "app_password_set": bool(saved.app_password),
        "restart_required": _restart_required(saved, running),
    }


def save(payload, running, changed_by=None):
    """Validate the submitted credentials and write them to .env. A blank
    client secret keeps the saved one."""
    payload = payload if isinstance(payload, dict) else {}
    app_id = str(payload.get("app_id") or "").strip()
    tenant_id = str(payload.get("tenant_id") or "").strip()
    public_base_url = str(payload.get("public_base_url") or "").strip().rstrip("/")
    sso_resource = str(payload.get("sso_resource") or "").strip()
    app_password = str(payload.get("app_password") or "").strip()

    if not _GUID.match(app_id):
        raise ConfigError("Bot (Entra app) ID must be a GUID, e.g. 00000000-0000-0000-0000-000000000000.")
    if not _GUID.match(tenant_id):
        raise ConfigError("Tenant ID must be a GUID, e.g. 00000000-0000-0000-0000-000000000000.")
    if not _BASE_URL.match(public_base_url):
        raise ConfigError("Public base URL must be https://<host> with no path, e.g. https://abc-8084.inc1.devtunnels.ms.")
    if sso_resource and not _SSO_RESOURCE.match(sso_resource):
        raise ConfigError("SSO Application ID URI must start with api:// and contain no spaces.")
    if app_password and not _SECRET.match(app_password):
        raise ConfigError("Client secret contains unexpected characters — paste the secret's Value exactly as Entra showed it.")

    updates = {
        "MICROSOFT_APP_ID": app_id,
        "MICROSOFT_APP_TENANT_ID": tenant_id,
        "PUBLIC_BASE_URL": public_base_url,
        "TEAMS_SSO_RESOURCE": sso_resource,
    }
    with _write_lock:
        values = _saved_values()
        if app_password:
            updates["MICROSOFT_APP_PASSWORD"] = app_password
        elif not values.get("MICROSOFT_APP_PASSWORD", "").strip():
            raise ConfigError("Client secret is required — the bot can't sign in without it.")

        changed = [key for key, value in updates.items() if values.get(key, "").strip() != value]
        for key in changed:
            set_key(ENV_PATH, key, updates[key], quote_mode="never")

    if changed:
        logger.info(f"Teams credentials updated in .env by {changed_by or 'unknown'}: {', '.join(changed)}", extra={"admin": True})
    return {"ok": True, "changed": changed, **describe(running)}

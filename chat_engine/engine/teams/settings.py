import os
from dataclasses import dataclass


def _get(source, name, default=""):
    return (source.get(name) or default).strip()


def _flag(source, name, default=False):
    value = source.get(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def default_sso_resource(public_base_url, app_id):
    host = public_base_url.split("://", 1)[-1].split("/", 1)[0].lower()
    return f"api://{host}/botid-{app_id}" if host and app_id else ""


@dataclass(frozen=True)
class TeamsSettings:
    """Everything the Teams bot + tab need, read from the environment (.env).

    app_id / app_password / tenant_id come from the Entra app registration that
    backs the Azure Bot resource (single-tenant). public_base_url is the HTTPS
    address Teams reaches this server on (a dev tunnel while testing)."""
    app_id: str
    app_password: str
    tenant_id: str
    public_base_url: str
    teams_app_id: str
    sso_resource: str
    bot_enabled: bool
    tab_enabled: bool
    enforce_tenant: bool
    max_workers: int
    conversation_store_path: str

    @classmethod
    def from_env(cls):
        return cls.from_mapping(os.environ)

    @classmethod
    def from_mapping(cls, source):
        app_id = _get(source, "MICROSOFT_APP_ID")
        public_base_url = _get(source, "PUBLIC_BASE_URL").rstrip("/")
        return cls(
            app_id=app_id,
            app_password=_get(source, "MICROSOFT_APP_PASSWORD"),
            tenant_id=_get(source, "MICROSOFT_APP_TENANT_ID"),
            public_base_url=public_base_url,
            teams_app_id=_get(source, "TEAMS_APP_ID"),
            sso_resource=_get(source, "TEAMS_SSO_RESOURCE") or default_sso_resource(public_base_url, app_id),
            bot_enabled=_flag(source, "TEAMS_ENABLED", default=bool(app_id)),
            tab_enabled=_flag(source, "TEAMS_TAB_ENABLED"),
            # Off = only users in MICROSOFT_APP_TENANT_ID can use the bot. Default on
            # (safe) — turn off only while the Azure resources and your real Teams
            # tenant don't match yet (e.g. Azure was set up under a personal "Default
            # Directory" instead of your actual work tenant). Re-enable before real use.
            enforce_tenant=_flag(source, "TEAMS_ENFORCE_TENANT", default=True),
            max_workers=int(_get(source, "TEAMS_BOT_MAX_WORKERS", "4") or 4),
            conversation_store_path=_get(source, "TEAMS_CONVERSATION_STORE", os.path.join("admin_store", "teams_conversations.json")),
        )

    @property
    def public_host(self):
        return self.public_base_url.split("://", 1)[-1].split("/", 1)[0].lower()

    def missing_for_bot(self):
        """Names of the settings the bot can't run without."""
        required = {
            "MICROSOFT_APP_ID": self.app_id,
            "MICROSOFT_APP_PASSWORD": self.app_password,
            "MICROSOFT_APP_TENANT_ID": self.tenant_id,
        }
        return [name for name, value in required.items() if not value]

    def missing_for_tab(self):
        required = {
            "MICROSOFT_APP_ID": self.app_id,
            "MICROSOFT_APP_TENANT_ID": self.tenant_id,
            "PUBLIC_BASE_URL": self.public_base_url,
        }
        return [name for name, value in required.items() if not value]

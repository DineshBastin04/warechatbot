"""
Explicit, per-run workspace resolution.

The rest of the app runs background agents through the module-level global
`vn` (self.ensure_vanna_initialized re-points it), so two workspaces' jobs —
or a job and a user switching workspaces in the UI — share one mutable object.
This agent never touches `vn`: every run reads the target workspace's metadata
fresh from the Workspaces collection by its explicit workspace_id and builds
its own DB connection and LLM client from that, used only for that run.
"""
import json
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_SECRET_KEY_RE = re.compile(r"(pass(word)?|pwd|secret|token|api[_-]?key|client[_-]?secret|credential)", re.IGNORECASE)
_SECRET_IN_TEXT_RE = re.compile(
    r"((?:api[_-]?key|key|token|secret|password|pwd|client_secret|access_token)\s*[=:]\s*)([^\s&;,'\"]+)",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def redact(value):
    """Deep copy with every secret-looking key's value replaced. Used on
    anything that could reach a log line, an API response or a report."""
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if _SECRET_KEY_RE.search(str(k)):
                out[k] = "***" if v else ""
            else:
                out[k] = redact(v)
        return out
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def scrub_text(text):
    """Removes credentials and full email addresses from free text (exception
    messages, provider errors) before it is stored or shown."""
    if text is None:
        return None
    text = _SECRET_IN_TEXT_RE.sub(lambda m: m.group(1) + "***", str(text))
    return _EMAIL_RE.sub(lambda m: f"{m.group(1)}***@{m.group(2)}", text)


def mask_email(address):
    if not address or "@" not in address:
        return None
    local, _, domain = address.partition("@")
    return f"{local[:1]}***@{domain}"


def _loads(raw):
    if isinstance(raw, dict):
        return raw
    try:
        value = json.loads(raw or "{}")
        return value if isinstance(value, (dict, list)) else {}
    except (TypeError, ValueError):
        return {}


@dataclass
class WorkspaceContext:
    workspace_id: str
    name: str
    display_name: str
    db_config: dict = field(repr=False)
    db_config_b: dict = field(repr=False)
    llm_config: dict = field(repr=False)
    email_recipients: list = field(repr=False)

    def scope(self):
        """The same four attributes VannaBase.validate_db_scope reads."""
        primary = self.db_config.get("databaseName") or None
        secondary = self.db_config_b.get("databaseName") or None
        same_instance = bool(secondary) and (
            str(self.db_config_b.get("serverName") or "").strip().lower()
            == str(self.db_config.get("serverName") or "").strip().lower()
            and str(self.db_config_b.get("port") or "").strip() == str(self.db_config.get("port") or "").strip()
        )
        return {
            "primary_db_name": primary,
            "secondary_db_name": secondary,
            "same_instance": same_instance,
            "secondary_db_alias": (self.db_config_b.get("db_alias") or "SECONDARY") if secondary else None,
        }

    def db_configured(self):
        return bool(self.db_config.get("serverName") and self.db_config.get("databaseName"))

    def public(self):
        """Safe to return to a browser: names and DB topology only."""
        scope = self.scope()
        return {
            "workspace_id": self.workspace_id,
            "name": self.name,
            "display_name": self.display_name,
            "db_configured": self.db_configured(),
            "primary_database": scope["primary_db_name"],
            "secondary_database": scope["secondary_db_name"],
            "llm_type": self.llm_config.get("model_type") or None,
            "llm_model": self.llm_config.get("model_name") or None,
        }


class WorkspaceResolver:
    """Reads workspaces straight from the ChromaDB `Workspaces` collection
    (the same collection VannaFlaskApp uses). Every call is a fresh read — no
    caching — so a DB/LLM/recipient change is picked up by the next run."""

    def __init__(self, workspace_collection):
        self._collection = workspace_collection

    def list_workspaces(self):
        """Returns None (not []) when the collection can't be read, so callers
        never mistake a read failure for "every workspace was deleted"."""
        try:
            data = self._collection.get()
        except Exception as exc:
            logger.error("warehouse_perf: could not list workspaces: %s", scrub_text(exc))
            return None
        out = []
        for ws_id, meta in zip(data.get("ids") or [], data.get("metadatas") or []):
            meta = meta or {}
            out.append({
                "workspace_id": str(ws_id),
                "name": meta.get("name") or "",
                "display_name": meta.get("display_name") or meta.get("name") or str(ws_id),
            })
        return out

    def get(self, workspace_id):
        if not workspace_id:
            return None
        try:
            data = self._collection.get(ids=[str(workspace_id)])
        except Exception as exc:
            logger.error("warehouse_perf: could not read workspace %s: %s", workspace_id, scrub_text(exc))
            return None
        metas = data.get("metadatas") or []
        ids = data.get("ids") or []
        if not metas or not ids or metas[0] is None:
            return None
        meta = metas[0]
        recipients = _loads(meta.get("email_recipients") or "[]")
        return WorkspaceContext(
            workspace_id=str(ids[0]),
            name=meta.get("name") or "",
            display_name=meta.get("display_name") or meta.get("name") or str(ids[0]),
            db_config=_loads(meta.get("db_config")) if isinstance(_loads(meta.get("db_config")), dict) else {},
            db_config_b=_loads(meta.get("db_config_b")) if isinstance(_loads(meta.get("db_config_b")), dict) else {},
            llm_config=_loads(meta.get("llm_config")) if isinstance(_loads(meta.get("llm_config")), dict) else {},
            email_recipients=recipients if isinstance(recipients, list) else [],
        )

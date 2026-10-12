"""
Warehouse Performance Intelligence Agent (V1: internal warehouse data only).

Automatic and zero-configuration: every workspace gets the agent. It discovers
usable operational data in the workspace's own SQL Server database (read-only),
builds historical baselines, detects significant deviations, drills down to
where and when performance changed, writes an executive report and — when a
significant deterioration is found — emails it to the workspace's existing
saved email recipients.

Integration surface (everything else in the app is untouched):
  create_warehouse_perf(app, send_email, load_email_config, scheduler=...)
      called once from VannaFlaskApp.__init__ with the app's existing
      scheduled-agents APScheduler instance; registers the dashboard/report
      routes and the per-workspace jobs on that scheduler.
  module.is_warehouse_command(text) / module.handle_chat(user, ws, text)
      optional "/warehouse ..." chat commands onto the same engine.

WPA_ENABLED=0 switches the whole feature off (no routes, no jobs).
"""
import logging
import os

logger = logging.getLogger(__name__)


class WarehousePerfModule:
    def __init__(self, service, jobs, chat):
        self.service = service
        self.jobs = jobs
        self.chat = chat

    @staticmethod
    def is_warehouse_command(text):
        from .chat import is_warehouse_command
        return is_warehouse_command(text)

    def handle_chat(self, user, workspace_id, text):
        try:
            return self.chat.handle(user, workspace_id, text)
        except Exception as exc:  # noqa: BLE001
            from .workspace_context import scrub_text
            logger.exception("warehouse_perf: chat command failed")
            return {"type": "text", "text": f"The warehouse agent hit an error: {scrub_text(type(exc).__name__)}"}, 500


def create_warehouse_perf(app, send_email, load_email_config, scheduler=None, store_dir=None, start_jobs=True):
    """Returns a WarehousePerfModule, or None if disabled. Never raises — a
    failure here is logged and the rest of the app starts normally."""
    if os.environ.get("WPA_ENABLED", "1").strip().lower() in ("0", "false", "no", "off"):
        logger.info("warehouse_perf: disabled via WPA_ENABLED")
        return None
    try:
        from .chat import WarehouseChat
        from .db import ReadOnlyExecutor
        from .delivery import EmailDelivery
        from .jobs import WarehousePerfJobs
        from .recipients import label_filter_from_env
        from .routes import register_routes
        from .service import ServiceSettings, WarehousePerfService
        from .store import WarehousePerfStore
        from .workspace_context import WorkspaceResolver

        root = store_dir or os.environ.get("WPA_STORE_DIR") or os.path.join("admin_store", "warehouse_perf")
        store = WarehousePerfStore(root)
        settings = ServiceSettings()
        service = WarehousePerfService(
            store=store,
            resolver=WorkspaceResolver(app.workspace_collection),
            executor=ReadOnlyExecutor(),
            delivery=EmailDelivery(store, send_email, load_email_config, label_filter=label_filter_from_env()),
            settings=settings,
        )
        jobs = WarehousePerfJobs(scheduler, service, settings.interval_minutes)
        service.jobs = jobs
        chat = WarehouseChat(service)
        register_routes(app.flask_app, app.requires_auth, app.requires_role, service, chat)
        if start_jobs:
            jobs.start()
        logger.info("warehouse_perf: initialised (store %s)", root)
        return WarehousePerfModule(service, jobs, chat)
    except Exception:  # noqa: BLE001
        logger.exception("warehouse_perf: initialisation failed — feature disabled for this process")
        return None

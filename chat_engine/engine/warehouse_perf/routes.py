"""
Flask routes for the Warehouse Performance Agent — dashboard and reports
only; there is deliberately no configuration API.

Registered on the existing VannaFlaskApp.flask_app with the app's own
requires_auth / requires_role decorators, and every handler additionally runs
authz.authorize() against the explicitly resolved workspace (the client's
workspace_id is a request, not a grant). Responses follow the app's
{"type": "success"|"error", ...} convention and never include DB credentials,
API keys, email secrets or full email addresses.

  GET  /warehouse-performance                         dashboard page
  GET  /api/v0/warehouse_perf/dashboard.js            dashboard script
  GET  /api/v0/warehouse_perf/dashboard?workspace_id= latest analysis + status
  POST /api/v0/warehouse_perf/run                     run a fresh analysis now
  GET  /api/v0/warehouse_perf/reports?workspace_id=   report history
  GET  /api/v0/warehouse_perf/report?workspace_id=&report_id=&format=json|docx|html|csv|text
  POST /api/v0/warehouse_perf/report/send             (admin) email to saved recipients
  POST /api/v0/warehouse_perf/rediscover              (admin) re-scan the schema, then run
  POST /api/v0/warehouse_perf/email_settings          (admin) which saved recipients get the report, and when
"""
import csv
import io
import os

from flask import Response, jsonify, request

from .authz import authorize, is_admin, username_of
from .reporting import csv_rows, render_html, render_text
from .word_report import WORD_MIME, build_docx
from .service import ServiceError
from .workspace_context import scrub_text

ADMIN = ["admin", "superadmin"]
BASE = "/api/v0/warehouse_perf"
_JS_PATH = os.path.join(os.path.dirname(__file__), "dashboard.js")

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Warehouse Performance Agent</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>body{margin:0;background:#f5f7fb;font-family:Segoe UI,Arial,sans-serif}#wpa-root{max-width:1200px;margin:0 auto;padding:16px}</style>
</head><body><div id="wpa-root"></div>
<script src="/api/v0/warehouse_perf/dashboard.js"></script>
<script>
  (function () {
    var ws = new URLSearchParams(window.location.search).get("workspace_id") || "";
    window.renderWarehousePerfDashboard(document.getElementById("wpa-root"), ws, {standalone: true});
  })();
</script></body></html>"""


def _err(message, status=400):
    return jsonify({"type": "error", "error": message}), status


def _ok(**payload):
    return jsonify({"type": "success", **payload})


def register_routes(flask_app, requires_auth, requires_role, service, chat=None):
    def ctx_for(user, workspace_id, need_admin=False):
        ctx = service.resolver.get(str(workspace_id)) if workspace_id else None
        ok, status, msg = authorize(user, ctx, need_admin=need_admin)
        if not ok:
            raise ServiceError(msg, status)
        return ctx

    def body():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ServiceError("a JSON object body is required")
        return data

    def guarded(fn):
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except ServiceError as exc:
                return _err(str(exc), exc.status)
            except Exception as exc:  # noqa: BLE001
                flask_app.logger.exception("warehouse_perf route failed")
                return _err(f"internal error: {scrub_text(type(exc).__name__)}", 500)
        wrapper.__name__ = fn.__name__
        return wrapper

    @flask_app.route("/warehouse-performance", methods=["GET"])
    @requires_auth
    def wpa_page(user=None):
        return Response(PAGE, mimetype="text/html")

    @flask_app.route(f"{BASE}/dashboard.js", methods=["GET"])
    @requires_auth
    def wpa_dashboard_js(user=None):
        with open(_JS_PATH, encoding="utf-8") as fh:
            return Response(fh.read(), mimetype="application/javascript",
                            headers={"Cache-Control": "no-cache"})

    @flask_app.route(f"{BASE}/dashboard", methods=["GET"])
    @requires_auth
    @guarded
    def wpa_dashboard(user=None):
        ctx = ctx_for(user, request.args.get("workspace_id"))
        view = service.dashboard(ctx.workspace_id, include_admin=is_admin(user))
        view["viewer"] = {"is_admin": is_admin(user)}
        view["monitoring"]["run_queued"] = bool(service.jobs and service.jobs.is_queued(ctx.workspace_id))
        return _ok(dashboard=view)

    @flask_app.route(f"{BASE}/run", methods=["POST"])
    @requires_auth
    @guarded
    def wpa_run(user=None):
        ctx = ctx_for(user, body().get("workspace_id"))
        if service.recently_ran(ctx.workspace_id):
            return _ok(queued=False, message="An analysis finished a few seconds ago — showing that result. Click again in 15 seconds for a new run.")
        if service.jobs is not None and service.jobs.queue_now(ctx.workspace_id, "manual", username_of(user)):
            return _ok(queued=True, message="Analysis started.")
        rec = service.run_analysis(ctx.workspace_id, trigger="manual", actor=username_of(user))
        return _ok(queued=False, run={k: rec.get(k) for k in ("status", "report_id", "failure_reason")})

    @flask_app.route(f"{BASE}/reports", methods=["GET"])
    @requires_auth
    @guarded
    def wpa_reports(user=None):
        ctx = ctx_for(user, request.args.get("workspace_id"))
        return _ok(reports=service.list_reports(ctx.workspace_id))

    @flask_app.route(f"{BASE}/report", methods=["GET"])
    @requires_auth
    @guarded
    def wpa_report(user=None):
        ctx = ctx_for(user, request.args.get("workspace_id"))
        rep = service.get_report(ctx.workspace_id, request.args.get("report_id") or None)
        fmt = (request.args.get("format") or "json").lower()
        name = f"warehouse_performance_{rep['report_id']}"
        if fmt in ("docx", "word"):
            return Response(build_docx(rep), mimetype=WORD_MIME,
                            headers={"Content-Disposition": f'attachment; filename="{name}.docx"'})
        if fmt == "text":
            return Response(render_text(rep), mimetype="text/plain; charset=utf-8",
                            headers={"Content-Disposition": f'attachment; filename="{name}.txt"'})
        if fmt == "html":
            return Response(render_html(rep), mimetype="text/html",
                            headers={"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src data:",
                                     "Content-Disposition": f'inline; filename="{name}.html"'})
        if fmt == "csv":
            out = io.StringIO()
            csv.writer(out).writerows(csv_rows(rep))
            return Response(out.getvalue(), mimetype="text/csv",
                            headers={"Content-Disposition": f'attachment; filename="{name}.csv"'})
        rep = dict(rep)
        rep["result"] = {k: v for k, v in rep["result"].items() if k != "query_log"}
        return _ok(report=rep)

    @flask_app.route(f"{BASE}/report/send", methods=["POST"])
    @requires_auth
    @requires_role(ADMIN)
    @guarded
    def wpa_report_send(user=None):
        data = body()
        ctx = ctx_for(user, data.get("workspace_id"), need_admin=True)
        return _ok(delivery=service.send_report(ctx.workspace_id, data.get("report_id") or None, username_of(user)))

    @flask_app.route(f"{BASE}/email_settings", methods=["POST"])
    @requires_auth
    @requires_role(ADMIN)
    @guarded
    def wpa_email_settings(user=None):
        data = body()
        ctx = ctx_for(user, data.get("workspace_id"), need_admin=True)
        return _ok(email_settings=service.save_email_settings(ctx.workspace_id, data, username_of(user)))

    @flask_app.route(f"{BASE}/rediscover", methods=["POST"])
    @requires_auth
    @requires_role(ADMIN)
    @guarded
    def wpa_rediscover(user=None):
        ctx = ctx_for(user, body().get("workspace_id"), need_admin=True)
        service.rediscover(ctx.workspace_id)
        queued = bool(service.jobs and service.jobs.queue_now(ctx.workspace_id, "rediscover", username_of(user)))
        if not queued:
            service.run_analysis(ctx.workspace_id, trigger="rediscover", actor=username_of(user))
        return _ok(queued=queued)

"""
The agent's single entry point for every interface (scheduler, dashboard,
chat): WarehousePerfService.run_analysis(workspace_id, ...).

Isolation contract for every run:
  workspace_id (explicit argument)
    → WorkspaceResolver.get(workspace_id)   fresh read of THAT workspace's metadata
    → WorkspaceData(ctx, ReadOnlyExecutor)   per-query read-only connections to its DB
    → discovery (cached per workspace)
    → Monitor → Investigator → Advisor agents (agents.py) → report → store/<workspace_id>/
    → delivery to THAT workspace's saved recipients only
No global `vn`, browser session or "active workspace" is consulted, nothing
is shared between workspaces, and all run state is local to the call.

There is no admin configuration. Operating values are application defaults
(ServiceSettings, overridable only by environment variables at deployment).
"""
import hashlib
import logging
import os
import threading
import time
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import recipients as recip
from .agents import run_agents
from .analyzer import Settings as AnalysisSettings
from .delivery import STATUS_NO_RECIPIENTS
from .discovery import MODEL_VERSION, db_fingerprint, discover
from .llm import build_narrator
from .queries import QuerySpec, WorkspaceData
from .exec_report import build_executive
from .word_report import WORD_MIME, build_docx
from .reporting import (alert_signature, build_report, csv_dicts, generate_narrative, render_html, render_text)
from .workspace_context import scrub_text

logger = logging.getLogger(__name__)


MODE_SIGNIFICANT = "significant"      # email only when a significant deterioration is found
MODE_EVERY_RUN = "every_run"          # email the report after every completed analysis
PERSON_TRIGGERS = ("manual", "chat")  # a person asked for this run ("Run analysis now", /warehouse run)
EMAIL_MODES = (MODE_SIGNIFICANT, MODE_EVERY_RUN)


class ServiceError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def _env_int(name, default, lo=None, hi=None):
    try:
        v = int(os.environ.get(name, default))
    except (TypeError, ValueError):
        v = default
    if lo is not None:
        v = max(lo, v)
    if hi is not None:
        v = min(hi, v)
    return v


class ServiceSettings:
    """Application defaults — not admin configuration."""

    def __init__(self, **over):
        self.timezone = over.get("timezone") or os.environ.get("WPA_TIMEZONE") or \
            os.environ.get("SCHEDULE_DEFAULT_TIMEZONE", "Asia/Kolkata")
        self.interval_minutes = over.get("interval_minutes", _env_int("WPA_INTERVAL_MINUTES", 60, 15, 1440))
        self.catalog_ttl_hours = over.get("catalog_ttl_hours", _env_int("WPA_CATALOG_TTL_HOURS", 24, 1, 720))
        self.query_timeout = over.get("query_timeout", _env_int("WPA_QUERY_TIMEOUT_SECONDS", 30, 5, 300))
        self.row_limit = over.get("row_limit", _env_int("WPA_ROW_LIMIT", 50000, 1000, 500000))
        self.max_auto_emails_per_day = over.get("max_auto_emails_per_day",
                                                _env_int("WPA_MAX_AUTO_EMAILS_PER_DAY", 3, 0, 24))
        self.auto_email = over.get("auto_email", os.environ.get("WPA_AUTO_EMAIL", "1").strip().lower()
                                   not in ("0", "false", "no", "off"))
        self.manual_cooldown_seconds = over.get("manual_cooldown_seconds", 15)
        # Testing aid for database snapshots: analyse as if the local time were this
        # ISO datetime (e.g. 2026-06-05T12:00). Unset in production.
        self.as_of = over.get("as_of", os.environ.get("WPA_ANALYSIS_AS_OF", "").strip() or None)
        self.analysis = over.get("analysis") or AnalysisSettings(
            lookback_days=_env_int("WPA_LOOKBACK_DAYS", 35, 22, 120))

    def tz(self):
        try:
            return ZoneInfo(self.timezone)
        except Exception:  # noqa: BLE001
            return ZoneInfo("UTC")


class WarehousePerfService:
    def __init__(self, store, resolver, executor, delivery, settings=None, clock=None,
                 narrator_factory=build_narrator, data_factory=None):
        self.store = store
        self.resolver = resolver
        self.executor = executor
        self.delivery = delivery
        self.settings = settings or ServiceSettings()
        self._clock = clock
        self._narrator_factory = narrator_factory
        self._data_factory = data_factory or (lambda ctx: WorkspaceData(
            ctx, executor, self.settings.query_timeout, self.settings.row_limit))
        self._local = {}
        self._local_guard = threading.Lock()
        self.jobs = None          # set by create_warehouse_perf (next-run times for the dashboard)

    # ------------------------------------------------------------- basics
    def now(self):
        if self._clock is not None:
            return self._clock()
        pinned = self.pinned_clock()
        return pinned or datetime.now(self.settings.tz())

    def pinned_clock(self):
        if not self.settings.as_of:
            return None
        try:
            return datetime.fromisoformat(self.settings.as_of).replace(tzinfo=self.settings.tz())
        except ValueError:
            logger.error("warehouse_perf: ignoring invalid WPA_ANALYSIS_AS_OF %r", self.settings.as_of)
            return None

    def _thread_lock(self, workspace_id):
        with self._local_guard:
            return self._local.setdefault(workspace_id, threading.Lock())

    def _public(self, ctx):
        pub = ctx.public()
        pub["timezone"] = self.settings.timezone
        return pub

    # ---------------------------------------------------------- discovery
    def _model(self, ctx, data, now, force=False):
        fp = db_fingerprint(ctx)
        cached = None if force else self.store.get_catalog(ctx.workspace_id)
        # A cached scan that found nothing usable (e.g. tables with no recent rows) is never
        # trusted: data may have arrived since, so every run scans again until metrics exist.
        if cached and cached.get("db_fingerprint") == fp and cached.get("metrics") \
                and cached.get("model_version") == MODEL_VERSION:
            try:
                age = now - datetime.fromisoformat(cached["discovered_at"])
            except (KeyError, ValueError, TypeError):
                age = timedelta(days=999)
            if timedelta(0) <= age < timedelta(hours=self.settings.catalog_ttl_hours):
                return cached, "cached"
        rows = data.catalog()
        start = datetime.combine(now.date() - timedelta(days=self.settings.analysis.lookback_days), datetime.min.time())
        end = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())

        def probe(candidate, ts, wide=False):
            spec = QuerySpec("probe", candidate["schema"], candidate["table"], ts,
                             label=f"probe {candidate['schema']}.{candidate['table']}{' (all time)' if wide else ''}")
            return data.probe(spec, start - timedelta(days=3650) if wide else start, end)

        def process_labels(candidate):
            spec = QuerySpec("labels", candidate["schema"], candidate["table"], candidate["ts"],
                             group_process=candidate["process"], description_column=candidate["process_description"],
                             label=f"activity types {candidate['schema']}.{candidate['table']}")
            frame = data.fetch(spec, start, end).frame
            frame.columns = [str(c).lower() for c in frame.columns]
            return frame.to_dict("records")

        model = discover(rows, probe=probe, now=now, db_fingerprint=fp, process_labels=process_labels)
        self.store.save_catalog(ctx.workspace_id, model)
        return model, "discovered"

    def rediscover(self, workspace_id):
        self.store.clear_catalog(workspace_id)

    # --------------------------------------------------------------- runs
    def run_analysis(self, workspace_id, trigger="scheduled", actor=None, force_discovery=False):
        """Runs one full analysis cycle for one workspace. Never raises; returns the run record."""
        started = time.time()
        now = self.now()
        rec = {"run_id": uuid.uuid4().hex[:12], "workspace_id": str(workspace_id), "trigger": trigger,
               "actor": actor, "started_at": now.isoformat(timespec="seconds"), "status": "failed",
               "db_status": "not_queried", "metrics_discovered": [], "metrics_calculated": [],
               "metrics_unavailable": [], "anomalies": [], "report_id": None, "report_generated": False,
               "recipients_resolved": 0, "email_status": "not_attempted", "failure_reason": None}
        ctx = self.resolver.get(workspace_id)
        if ctx is None:
            rec["failure_reason"] = "workspace not found"
            self._log(rec, started)
            return rec
        tlock = self._thread_lock(ctx.workspace_id)
        if not tlock.acquire(blocking=False):
            rec.update(status="skipped", failure_reason="an analysis is already running for this workspace")
            self._log(rec, started)
            return rec
        release = None
        data = None
        try:
            release = self.store.try_run_lock(ctx.workspace_id)
            if release is None:
                rec.update(status="skipped", failure_reason="an analysis is already running for this workspace")
                return rec
            if not ctx.db_configured():
                rec.update(status="not_configured", failure_reason="the workspace has no database connection configured")
                return rec
            data = self._data_factory(ctx)
            try:
                model, how = self._model(ctx, data, now, force=force_discovery)
            except Exception as exc:  # noqa: BLE001
                rec.update(db_status="failed", failure_reason=f"schema discovery failed: {scrub_text(str(exc))}")
                return rec
            rec["discovery"] = how
            rec["metrics_discovered"] = [m["metric_id"] for m in model.get("metrics") or []]
            rec["metrics_unavailable"] = [u["metric_id"] for u in model.get("unavailable") or []]

            result = run_agents(self._public(ctx), model, data, now, self.settings.analysis)
            qlog = result.get("query_log") or []
            rec["db_status"] = ("failed" if qlog and all(q["status"] == "failed" for q in qlog) else
                                "partial" if any(q["status"] == "failed" for q in qlog) else "ok")
            rec["queries"] = len(qlog)
            rec["metrics_calculated"] = [m["metric_id"] for m in result.get("metrics") or [] if m.get("status") == "ok"]
            rec["anomalies"] = [c["metric_id"] for c in result.get("changes") or []
                                if c["classification"] in ("deterioration", "significant_deterioration")]
            diag = result.get("diagnosis") or {}
            rec["investigation"] = (result.get("investigation") or {}).get("status")
            rec["likely_causes"] = [c["title"] for c in diag.get("likely_causes") or []]

            narrative, source, rejected = None, "deterministic", []
            try:
                narrator = self._narrator_factory(ctx.llm_config)
            except Exception as exc:  # noqa: BLE001
                narrator, rejected = None, [f"LLM unavailable: {type(exc).__name__}"]
            if narrator is not None:
                narrative, source, rejected = generate_narrative(narrator, result)

            report_id = f"{now:%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
            report = build_report(report_id, result, narrative, source, rejected)
            report["text"] = render_text(report)
            report["trigger"] = trigger
            rec["report_id"] = report_id
            rec["report_generated"] = True

            # Any run (scheduled, Run analysis now, Re-scan, chat) emails the recipients chosen in
            # the agent's Email settings:
            #   * "After every analysis": every completed report, problems included (no daily limit);
            #   * a run a person asked for that finds a significant problem: always (they asked for it);
            #   * the automatic runs on a significant problem: once per problem, max N a day.
            email = self.email_settings(ctx.workspace_id)
            every_run = email["mode"] == MODE_EVERY_RUN and result.get("status") == "ok"
            asked = trigger in PERSON_TRIGGERS and report["alert_worthy"]
            if (report["alert_worthy"] or every_run) and self.settings.auto_email:
                report["delivery"] = self._auto_deliver(
                    ctx, report, every_run=every_run or asked,
                    purpose="every_run" if every_run else "manual_run" if asked else "auto")
            elif report["alert_worthy"] or every_run:
                report["delivery"] = {"status": "not_sent_auto_email_off",
                                      "reason": "automatic email is switched off for this deployment (WPA_AUTO_EMAIL)"}
            else:
                report["delivery"] = {"status": "not_required",
                                      "reason": "no significant deterioration was detected, so no email was sent"}
            rec["email_status"] = report["delivery"]["status"]
            rec["recipients_resolved"] = report["delivery"].get("recipients_resolved", 0)
            self.store.save_report(ctx.workspace_id, report)
            rec["status"] = "ok" if result.get("status") == "ok" else result.get("status")
            if result.get("status") != "ok":
                rec["failure_reason"] = result.get("message")
            return rec
        except Exception as exc:  # noqa: BLE001 — a run never propagates; the next run (and other workspaces) continue
            logger.exception("warehouse_perf: analysis failed for workspace %s", workspace_id)
            rec["failure_reason"] = scrub_text(f"{type(exc).__name__}: {exc}")
            return rec
        finally:
            if data is not None:
                try:
                    data.close()
                except Exception:  # noqa: BLE001
                    pass
            if release is not None:
                release()
            tlock.release()
            try:
                self.store.append_run(ctx.workspace_id, {**rec, "finished_at": self.now().isoformat(
                    timespec="seconds"), "duration_seconds": round(time.time() - started, 2)})
            except Exception:  # noqa: BLE001
                logger.exception("warehouse_perf: could not record run for %s", workspace_id)
            self._log(rec, started)

    def _log(self, rec, started):
        logger.info(
            "warehouse_perf run workspace=%s trigger=%s status=%s duration=%.2fs db=%s discovered=%s calculated=%s "
            "unavailable=%s anomalies=%s report=%s recipients=%s email=%s failure=%s",
            rec["workspace_id"], rec["trigger"], rec["status"], time.time() - started, rec["db_status"],
            len(rec["metrics_discovered"]), len(rec["metrics_calculated"]), len(rec["metrics_unavailable"]),
            ",".join(rec["anomalies"]) or "-", rec["report_id"] or "-", rec["recipients_resolved"],
            rec["email_status"], scrub_text(rec["failure_reason"]) or "-")

    # ----------------------------------------------------------- delivery
    def _email_parts(self, report, ctx):
        """(subject, text, csv rows, csv filename, extras). The body is the management version
        (plain English, status, KPI tiles, charts); the full technical report is attached."""
        try:
            ex = build_executive(report, inline=True)
        except Exception:  # noqa: BLE001 — never let the pretty version block the alert
            logger.exception("warehouse_perf: executive email could not be built; sending plain text")
            ex = None
        name = f"warehouse_performance_{report['report_id']}"
        if ex is None:
            ov = report.get("overall") or {}
            cls = (ov.get("classification") or "").replace("_", " ")
            subject = f"[Warehouse Performance] {ctx.display_name}: {cls or 'report'} — " \
                      f"{(report.get('period') or {}).get('label') or ''}".strip(" —")
            return subject, report["text"], csv_dicts(report), f"{name}.csv", None
        attachments = []
        try:
            attachments.append((f"{name}_report.docx", WORD_MIME, build_docx(report)))
        except Exception:  # noqa: BLE001 — the email still goes out with the CSV
            logger.exception("warehouse_perf: Word report could not be built")
        extras = {"html": ex["html"],
                  "inline_images": [(cid, png) for cid, png, _alt in ex["images"]],
                  "extra_attachments": attachments}
        return ex["subject"], ex["text"], csv_dicts(report), f"{name}_data.csv", extras

    def _auto_deliver(self, ctx, report, every_run=False, purpose="every_run"):
        subject, body, rows, filename, extras = self._email_parts(report, ctx)
        flt, use_default = self.recipient_filter(ctx.workspace_id)
        day = (report.get("period") or {}).get("date")
        sig = hashlib.sha256(alert_signature(report["result"]).encode()).hexdigest()[:12]
        if every_run:
            # "After every analysis", or a run a person asked for: each report is sent once and
            # never blocked by the daily limit (and not counted towards it). The problem's
            # signature is kept in the key, so the automatic runs know it was already emailed.
            out = self.delivery.deliver(ctx, ctx.workspace_id, report["report_id"], purpose,
                                        f"run:{day}:{sig}:{report['report_id']}", subject, body, rows, filename,
                                        label_filter=flt, use_default_filter=use_default, extras=extras)
            return self._delivery_summary(out)
        if report.get("alert_worthy") and any(
                d.get("status") == "sent" and str(d.get("dedupe_key") or "").startswith(f"run:{day}:{sig}:")
                for d in self.store.list_deliveries(ctx.workspace_id, limit=500)):
            return {"status": "duplicate_skipped",
                    "reason": "this problem was already emailed today (from Run analysis now or After every analysis)"}
        if self.store.auto_sends_on(ctx.workspace_id, day) >= self.settings.max_auto_emails_per_day:
            return {"status": "not_sent_daily_cap",
                    "reason": f"the automatic email limit of {self.settings.max_auto_emails_per_day} per day was reached"}
        out = self.delivery.deliver(ctx, ctx.workspace_id, report["report_id"], "auto", f"auto:{day}:{sig}",
                                    subject, body, rows, filename, label_filter=flt, use_default_filter=use_default,
                                    extras=extras)
        return self._delivery_summary(out)

    # ------------------------------------------------------- email settings
    def email_settings(self, workspace_id):
        raw = self.store.get_settings(workspace_id).get("email") or {}
        mode = raw.get("mode") if raw.get("mode") in EMAIL_MODES else MODE_SIGNIFICANT
        recipients = raw.get("recipients")
        return {"mode": mode, "recipients": list(recipients) if isinstance(recipients, list) else None,
                "updated_by": raw.get("updated_by"), "updated_at": raw.get("updated_at")}

    def recipient_filter(self, workspace_id):
        """(filter, use_deployment_default). A saved selection wins; otherwise every saved
        recipient (or the WPA_RECIPIENT_LABELS deployment default) is used."""
        sel = self.email_settings(workspace_id)["recipients"]
        return (sel, False) if sel is not None else (None, True)

    def save_email_settings(self, workspace_id, payload, actor):
        ctx = self.resolver.get(workspace_id)
        if ctx is None:
            raise ServiceError("workspace not found", 404)
        mode = payload.get("mode", MODE_SIGNIFICANT)
        if mode not in EMAIL_MODES:
            raise ServiceError("mode must be one of: " + ", ".join(EMAIL_MODES))
        labels = payload.get("recipients")
        if labels is not None:
            if not isinstance(labels, list) or not all(isinstance(x, str) for x in labels):
                raise ServiceError("recipients must be a list of saved recipient names")
            saved = {r["key"] for r in recip.saved_list(ctx)}
            keys = []
            for label in labels:
                key = recip.normalize_label(label)
                if key not in saved:
                    raise ServiceError(f"'{label}' is not a saved recipient of this workspace (add it first)")
                if key not in keys:
                    keys.append(key)
            labels = keys
        settings = self.store.get_settings(ctx.workspace_id)
        settings["email"] = {"mode": mode, "recipients": labels, "updated_by": actor,
                             "updated_at": self.now().isoformat(timespec="seconds")}
        self.store.save_settings(ctx.workspace_id, settings)
        logger.info("warehouse_perf email settings workspace=%s by=%s mode=%s recipients=%s",
                    ctx.workspace_id, actor, mode, "all" if labels is None else len(labels))
        return self.email_settings(ctx.workspace_id)

    def _delivery_summary(self, out):
        sent = [o for o in out["outcomes"] if o["status"] == "sent"]
        summary = {"status": out["status"], "at": self.now().isoformat(timespec="seconds"),
                   "recipients_resolved": len([o for o in out["outcomes"] if o["status"] != "rejected"]),
                   "sent_to": [{"label": o["label"], "address_masked": o.get("address_masked")} for o in sent],
                   "outcomes": out["outcomes"], "problems": out.get("problems") or []}
        if out["status"] == STATUS_NO_RECIPIENTS:
            summary["reason"] = ("the report was generated but not sent: " + (out.get("reason") or "no recipients"))
        return summary

    def send_report(self, workspace_id, report_id, actor):
        ctx = self.resolver.get(workspace_id)
        if ctx is None:
            raise ServiceError("workspace not found", 404)
        report = self.store.get_report(ctx.workspace_id, report_id) if report_id else \
            self.store.latest_report(ctx.workspace_id)
        if not report:
            raise ServiceError("no report has been generated for this workspace yet", 404)
        subject, body, rows, filename, extras = self._email_parts(report, ctx)
        flt, use_default = self.recipient_filter(ctx.workspace_id)
        out = self.delivery.deliver(ctx, ctx.workspace_id, report["report_id"], "manual",
                                    f"manual:{report['report_id']}", subject, body, rows, filename,
                                    label_filter=flt, use_default_filter=use_default, extras=extras)
        summary = self._delivery_summary(out)
        summary["actor"] = actor
        report.setdefault("manual_deliveries", []).append(summary)
        self.store.save_report(ctx.workspace_id, report)
        logger.info("warehouse_perf manual send workspace=%s report=%s by=%s status=%s sent=%d",
                    ctx.workspace_id, report["report_id"], actor, summary["status"], len(summary["sent_to"]))
        return summary

    # ---------------------------------------------------------- dashboard
    def dashboard(self, workspace_id, include_admin=False):
        ctx = self.resolver.get(workspace_id)
        if ctx is None:
            raise ServiceError("workspace not found", 404)
        report = self.store.latest_report(ctx.workspace_id)
        last = self.store.last_run(ctx.workspace_id)
        next_run = self.jobs.next_run(ctx.workspace_id) if self.jobs else None
        catalog = self.store.get_catalog(ctx.workspace_id)
        view = {
            "workspace": self._public(ctx),
            "monitoring": {
                "status": ("not_configured" if not ctx.db_configured() else
                           "active" if (self.jobs and self.jobs.active) else "manual_only"),
                "interval_minutes": self.settings.interval_minutes,
                "last_analysis_at": (report or {}).get("generated_at"),
                "last_run": _public_run(last),
                "next_analysis_at": next_run,
                "clock_pinned_to": self.settings.as_of if self.pinned_clock() else None,
            },
            "report": _dashboard_report(report),
            "discovery": _public_catalog(catalog),
            "email": {"auto_email": self.settings.auto_email,
                      "provider": self.delivery.provider_status() if include_admin else None},
        }
        view["last_email"] = self._last_email(ctx.workspace_id)
        if include_admin:
            flt, use_default = self.recipient_filter(ctx.workspace_id)
            effective = self.delivery.label_filter if use_default else flt
            view["recipients"] = recip.public_summary(ctx, ctx.workspace_id, effective)
            es = self.email_settings(ctx.workspace_id)
            chosen = set(effective) if effective is not None else None
            view["email_settings"] = {
                "mode": es["mode"], "all_selected": es["recipients"] is None,
                "updated_by": es["updated_by"], "updated_at": es["updated_at"],
                "saved": [{"label": r["label"], "address_masked": r["address_masked"],
                           "selected": chosen is None or r["key"] in chosen} for r in recip.saved_list(ctx)],
            }
            view["recent_runs"] = [_public_run(r) for r in self.store.list_runs(ctx.workspace_id, 10)]
        return view

    def _last_email(self, workspace_id):
        """The most recent email that was actually sent (any report), for the dashboard."""
        sent = [d for d in self.store.list_deliveries(workspace_id, limit=500) if d.get("status") == "sent"]
        if not sent:
            return None
        latest = sent[0]
        same = [d for d in sent if d.get("report_id") == latest.get("report_id")]
        try:
            at = datetime.fromtimestamp(float(latest.get("updated_at")), self.settings.tz()).isoformat(timespec="seconds")
        except (TypeError, ValueError):
            at = None
        return {"at": at, "report_id": latest.get("report_id"),
                "automatic": latest.get("purpose") in ("auto", "every_run"),
                "sent_to": sorted({d.get("label") for d in same if d.get("label")})}

    def get_report(self, workspace_id, report_id=None):
        rep = self.store.get_report(workspace_id, report_id) if report_id else self.store.latest_report(workspace_id)
        if not rep:
            raise ServiceError("report not found", 404)
        return rep

    def list_reports(self, workspace_id, limit=30):
        return self.store.list_reports(workspace_id, limit)

    def recently_ran(self, workspace_id):
        last = self.store.last_run(workspace_id)
        if not last or not last.get("finished_at"):
            return False
        try:
            age = self.now() - datetime.fromisoformat(last["finished_at"])
        except (TypeError, ValueError):
            return False
        return 0 <= age.total_seconds() < self.settings.manual_cooldown_seconds   # "future" runs (clock re-pinned) never block


def _public_run(r):
    if not r:
        return None
    return {k: r.get(k) for k in ("run_id", "trigger", "status", "started_at", "finished_at", "duration_seconds",
                                  "db_status", "report_id", "email_status", "failure_reason")}


def _public_catalog(c):
    if not c:
        return None
    return {"discovered_at": c.get("discovered_at"), "tables_scanned": c.get("tables_scanned"),
            "metrics": [{"metric_id": m["metric_id"], "label": m["label"]} for m in c.get("metrics") or []],
            "unavailable": c.get("unavailable") or [], "notes": c.get("notes") or [],
            "sources": {k: (f"{v['schema']}.{v['table']}" if v else None) for k, v in (c.get("sources") or {}).items()},
            "evidence_sources": {k: (f"{v['schema']}.{v['table']}" if v else None)
                                 for k, v in (c.get("evidence_sources") or {}).items()}}


HOURLY_FALLBACK = ("orders_dispatched", "orders_completed", "units_moved", "transactions")


def _hourly_chart(r, dd):
    """Today vs normal per hour: the headline metric in the problem warehouse, or (no problem)
    the main throughput metric for all warehouses."""
    tw = dd.get("time_window") or {}
    h = dd.get("headline_metric") or {}
    if tw.get("hourly"):
        scope = f" in warehouse {tw['scope']}" if tw.get("scope") else ""
        return {"title": f"{h.get('label')}{scope} per hour: today vs a normal day", "start": tw.get("start"),
                "y_title": _per_hour_title(h.get("label"), h.get("unit")), "unit": h.get("unit"),
                "points": tw["hourly"]}
    metrics = {m["metric_id"]: m for m in r.get("metrics") or []}
    for mid in ([h["metric_id"]] if h.get("metric_id") else []) + list(HOURLY_FALLBACK):
        m = metrics.get(mid) or {}
        if m.get("hourly"):
            return {"title": f"{m['label']} per hour, all warehouses: today vs a normal day", "start": None,
                    "y_title": _per_hour_title(m["label"], m.get("unit")), "unit": m.get("unit"),
                    "points": m["hourly"]}
    return None


def _per_hour_title(label, unit):
    """Y-axis title: a count is "X per hour"; a duration is an average, so "X (minutes)"."""
    return f"{label} (minutes)" if unit == "minutes" else f"{label} per hour"


def _check_label(c):
    s = c.get("subject") or ""
    if c["id"] == "staffing:all":
        return "People working (all activities)"
    return {"staffing": f"People on {s}", "productivity": f"{s} per person", "demand": "Orders received",
            "order_size": "Units per order"}.get(c["hypothesis"], s)


def _public_check(c):
    return {**{k: c.get(k) for k in ("id", "hypothesis", "hypothesis_title", "status", "subject", "unit", "actual",
                                     "baseline", "pct_diff", "statement")},
            "label": _check_label(c)}


def _dashboard_report(report):
    if not report:
        return None
    r = report["result"]
    dd = r.get("drilldown") or {}
    return {
        "report_id": report["report_id"], "generated_at": report["generated_at"], "status": r.get("status"),
        "message": r.get("message"), "period": r.get("period"), "overall": r.get("overall"), "kpis": r.get("kpis"),
        "changes": (r.get("changes") or [])[:8],
        "where": {"headline": dd.get("headline_metric"), "warehouse": dd.get("warehouse"),
                  "process": dd.get("process"), "time_window": {k: v for k, v in (dd.get("time_window") or {}).items()
                                                                  if k != "hourly"} or None,
                  "dimensions": dd.get("dimensions"), "conclusion": dd.get("conclusion")},
        "executive_summary": report.get("executive_summary"), "summary_source": report.get("summary_source"),
        "recommendations": dd.get("recommendations") or [],
        "freshness_warnings": r.get("freshness_warnings") or [],
        "unavailable": r.get("unavailable") or [],
        "diagnosis": r.get("diagnosis"),
        "investigation": {**{k: (r.get("investigation") or {}).get(k) for k in ("status", "scope", "summary", "notes",
                                                                               "sources")},
                          "checks": [_public_check(c) for c in (r.get("investigation") or {}).get("checks") or []]},
        "charts": {"hourly": _hourly_chart(r, dd)},
        "agents": r.get("agents") or [],
        "alert_worthy": report.get("alert_worthy"),
        "delivery": {k: v for k, v in (report.get("delivery") or {}).items() if k != "outcomes"},
        "manual_deliveries": [{k: v for k, v in d.items() if k != "outcomes"}
                              for d in report.get("manual_deliveries") or []],
    }

"""
Email delivery through the app's EXISTING provider layer.

send_email / load_email_config are injected — they are the module-level
_send_email(recipients, subject, body, rows, filename) and load_email_config()
from engine/flask/__init__.py, so SMTP vs Microsoft Graph selection, sender
credentials and the CSV attachment format are exactly what every other agent
uses. This module adds, per recipient:
  - the global kill switch check (send_email_enabled), recorded explicitly;
  - one message per recipient, so each has its own audit row and retry;
  - dedupe: a (purpose, report, recipient) key already sent is never re-sent;
  - bounded retries with backoff; errors scrubbed of secrets before storage.
Recipients come only from recipients.resolve_workspace_recipients().
"""
import logging
import time

from . import recipients as recip
from .workspace_context import scrub_text

logger = logging.getLogger(__name__)

STATUS_SENT = "sent"
STATUS_FAILED = "failed"
STATUS_REJECTED = "rejected"
STATUS_SUPPRESSED = "suppressed_kill_switch"
STATUS_DUPLICATE = "duplicate_skipped"
STATUS_NO_RECIPIENTS = "not_sent_no_recipients"
KILL_SWITCH_TEXT = "global email kill switch is on (send_email_enabled = false)"


class EmailDelivery:
    def __init__(self, store, send_email, load_email_config, max_attempts=3, backoff_seconds=(2, 5), sleep=time.sleep,
                 label_filter=None):
        self.store = store
        self._send = send_email
        self._load_cfg = load_email_config
        self.max_attempts = max(1, int(max_attempts))
        self.backoff = tuple(backoff_seconds)
        self._sleep = sleep
        self.label_filter = label_filter

    def kill_switch_engaged(self):
        try:
            return not bool((self._load_cfg() or {}).get("send_email_enabled", True))
        except Exception as exc:  # noqa: BLE001 — can't read the switch => don't send
            logger.error("warehouse_perf: email config unreadable, treating as disabled: %s", scrub_text(exc))
            return True

    def provider_status(self):
        try:
            cfg = self._load_cfg() or {}
        except Exception:  # noqa: BLE001
            return {"provider": None, "enabled": False, "configured": False}
        provider = cfg.get("email_provider", "gmail")
        if provider == "outlook":
            o = cfg.get("outlook") or {}
            configured = bool(o.get("tenant_id") and o.get("client_id") and o.get("client_secret") and o.get("sender_email"))
        else:
            configured = bool(cfg.get("sender_email") and cfg.get("sender_password"))
        return {"provider": provider, "enabled": bool(cfg.get("send_email_enabled", True)), "configured": configured}

    def _send_one(self, address, subject, body, rows, filename, extras):
        if not extras:
            return self._send([address], subject, body, rows, filename)
        try:
            return self._send([address], subject, body, rows, filename, **extras)
        except TypeError:
            # an older _send_email without html/inline_images/extra_attachments: send plain text
            return self._send([address], subject, body, rows, filename)

    def deliver(self, ctx, workspace_id, report_id, purpose, dedupe_scope, subject, body, rows, filename,
                label_filter=None, use_default_filter=True, extras=None):
        """Sends to the workspace's resolved saved recipients (all of them, or those in
        label_filter). Returns {"status", "outcomes", "problems"}; never raises for a
        delivery problem."""
        flt = label_filter if (label_filter is not None or not use_default_filter) else self.label_filter
        resolved, problems = recip.resolve_workspace_recipients(ctx, workspace_id, flt)
        outcomes = []
        for p in problems:
            if p["reason"] in (recip.REASON_NONE, recip.REASON_NONE_SELECTED, recip.REASON_WRONG_WORKSPACE):
                continue
            self.store.record_delivery(workspace_id, report_id, purpose, p["label"], STATUS_REJECTED, p["reason"])
            outcomes.append({"label": p["label"], "status": STATUS_REJECTED, "reason": p["reason"]})
        if not resolved:
            reason = problems[0]["reason"] if problems else recip.REASON_NONE
            self.store.record_delivery(workspace_id, report_id, purpose, None, STATUS_NO_RECIPIENTS, reason)
            return {"status": STATUS_NO_RECIPIENTS, "reason": reason, "outcomes": outcomes, "problems": problems}

        suppressed = self.kill_switch_engaged()
        for r in resolved:
            key = f"{dedupe_scope}:{r['recipient_key']}"
            delivery_id, already = self.store.begin_delivery(workspace_id, key, r["label"], r["address_masked"],
                                                             report_id, purpose)
            if already:
                outcomes.append({"label": r["label"], "address_masked": r["address_masked"], "status": STATUS_DUPLICATE})
                continue
            if suppressed:
                self.store.update_delivery(workspace_id, delivery_id, STATUS_SUPPRESSED, 0, KILL_SWITCH_TEXT)
                outcomes.append({"label": r["label"], "address_masked": r["address_masked"],
                                 "status": STATUS_SUPPRESSED})
                continue
            status, attempts, error = STATUS_FAILED, 0, None
            for attempt in range(1, self.max_attempts + 1):
                attempts = attempt
                try:
                    if self._send_one(r["address"], subject, body, rows, filename, extras):
                        status, error = STATUS_SENT, None
                        break
                    if self.kill_switch_engaged():
                        status, error = STATUS_SUPPRESSED, KILL_SWITCH_TEXT
                        break
                    error = "the email provider reported the message was not sent"
                except Exception as exc:  # noqa: BLE001
                    error = scrub_text(f"{type(exc).__name__}: {exc}")
                if attempt < self.max_attempts:
                    self._sleep(self.backoff[min(attempt - 1, len(self.backoff) - 1)] if self.backoff else 0)
            self.store.update_delivery(workspace_id, delivery_id, status, attempts, error)
            if status != STATUS_SENT:
                logger.warning("warehouse_perf: delivery to %s for report %s in workspace %s: %s (%s)",
                               r["address_masked"], report_id, workspace_id, status, error)
            outcomes.append({"label": r["label"], "address_masked": r["address_masked"], "status": status,
                             "attempts": attempts, "error": error})
        statuses = {o["status"] for o in outcomes if o["status"] != STATUS_REJECTED}
        overall = (STATUS_SENT if STATUS_SENT in statuses else
                   STATUS_SUPPRESSED if statuses == {STATUS_SUPPRESSED} else
                   STATUS_DUPLICATE if statuses == {STATUS_DUPLICATE} else STATUS_FAILED)
        return {"status": overall, "outcomes": outcomes, "problems": problems}

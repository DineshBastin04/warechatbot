"""
Optional chat interface — "/warehouse ..." — onto the SAME engine the
scheduler uses. The agent does not need chat to work; this only reads the
latest automatic analysis (or queues a fresh one) for the chat's workspace.

  /warehouse                 help
  /warehouse report|status   latest executive finding + top changes + dashboard link
  /warehouse run             queue a fresh analysis now
  /warehouse send            (admin) preview who the latest report would go to
  /warehouse send confirm <report id>   (admin) email it to the saved recipients

Replies use the app's existing {"type": "text", "text": ...} shape.
"""
import re

from . import recipients as recip
from .authz import authorize, is_admin, username_of
from .drilldown import fmt_num, fmt_pct
from .reporting import cls_text

COMMAND_RE = re.compile(r"^\s*/warehouse\b", re.IGNORECASE)

HELP = (
    "Warehouse Performance Agent — runs automatically for this workspace.\n"
    "  /warehouse report — latest analysis (what changed, where, when)\n"
    "  /warehouse run — run a fresh analysis now\n"
    "  /warehouse send — (admin) email the latest report to this workspace's saved recipients\n"
    "Full dashboard: /warehouse-performance"
)


def is_warehouse_command(text):
    return bool(COMMAND_RE.match(text or ""))


def _reply(text, status=200):
    return {"type": "text", "text": text}, status


def dashboard_link(workspace_id):
    return f"/warehouse-performance?workspace_id={workspace_id}"


class WarehouseChat:
    def __init__(self, service):
        self.service = service

    def handle(self, user, workspace_id, text):
        rest = COMMAND_RE.sub("", text or "", count=1).strip()
        low = rest.lower()
        if low in ("", "help", "?"):
            return _reply(HELP)
        ctx = self.service.resolver.get(workspace_id) if workspace_id else None
        ok, status, msg = authorize(user, ctx, need_admin=False)
        if not ok:
            return _reply(f"Sorry — {msg}.", status)
        if low in ("report", "status", "performance", "latest"):
            return self._report(ctx)
        if low == "run":
            return self._run(ctx, user)
        if low.startswith("send"):
            return self._send(ctx, user, low)
        return _reply(HELP)

    def _report(self, ctx):
        rep = self.service.store.latest_report(ctx.workspace_id)
        if not rep:
            return _reply("No analysis has completed for this workspace yet — it runs automatically; you can also "
                          f"type /warehouse run. Dashboard: {dashboard_link(ctx.workspace_id)}")
        r = rep["result"]
        lines = [f"Warehouse performance — {(r.get('period') or {}).get('label') or 'latest'} "
                 f"(analysed {rep['generated_at']})", "", rep["executive_summary"], ""]
        changes = [c for c in r.get("changes") or [] if c["classification"] != "normal_variation"][:5]
        if changes:
            lines.append("What changed:")
            lines += [f"  • {c['label']}: {fmt_num(c['actual'], c['unit'])} vs {fmt_num(c['baseline'], c['unit'])} "
                      f"({fmt_pct(c['pct_diff'])}) — {cls_text(c['classification'])}" for c in changes]
        lines.append(f"Dashboard: {dashboard_link(ctx.workspace_id)}   Report ID: {rep['report_id']}")
        return _reply("\n".join(lines))

    def _run(self, ctx, user):
        if self.service.recently_ran(ctx.workspace_id):
            return _reply("An analysis finished a few seconds ago — type /warehouse report to see it, or try again in 15 seconds.")
        jobs = self.service.jobs
        if jobs is not None and jobs.queue_now(ctx.workspace_id, trigger="chat", actor=username_of(user)):
            return _reply("Analysis started. Type /warehouse report in a minute to see the result.")
        rec = self.service.run_analysis(ctx.workspace_id, trigger="chat", actor=username_of(user))
        if rec.get("report_id"):
            return self._report(ctx)
        return _reply(f"The analysis did not complete: {rec.get('failure_reason') or rec.get('status')}.")

    def _send(self, ctx, user, low):
        if not is_admin(user):
            return _reply("Only an admin can email the report.", 403)
        rep = self.service.store.latest_report(ctx.workspace_id)
        if not rep:
            return _reply("There is no report to send yet.")
        m = re.match(r"^send\s+confirm\s+([a-z0-9-]+)$", low)
        if not m:
            flt, use_default = self.service.recipient_filter(ctx.workspace_id)
            summary = recip.public_summary(ctx, ctx.workspace_id,
                                           self.service.delivery.label_filter if use_default else flt)
            if not summary["recipients"]:
                reason = summary["problems"][0]["reason"] if summary["problems"] else recip.REASON_NONE
                return _reply(f"The report can't be emailed: {reason}. Add recipients under Email Config.")
            names = ", ".join(f"{r['label']} ({r['address_masked']})" for r in summary["recipients"])
            return _reply(f"This will email report {rep['report_id']} to: {names}.\n"
                          f"Type /warehouse send confirm {rep['report_id']} to send it.")
        if m.group(1) != rep["report_id"].lower():
            return _reply("That report ID is not the latest report — type /warehouse send again to get a fresh "
                          "confirmation.")
        out = self.service.send_report(ctx.workspace_id, rep["report_id"], username_of(user))
        if out["status"] == "sent":
            return _reply("Sent to " + ", ".join(s["label"] for s in out["sent_to"]) + ".")
        return _reply(f"Not sent: {out.get('reason') or out['status'].replace('_', ' ')}.")

"""
Recipient resolution from the workspace's EXISTING saved email configuration.

The app already stores named recipients per workspace (Email Config panel →
/api/v0/save_workspace_email_config → workspace metadata "email_recipients" =
[{"label", "address"}], labels unique, "all" reserved). This agent stores no
addresses of its own: the report goes to recipients saved there, resolved
label → address from a FRESH read of that workspace at send time, and nothing
falls back to any other address.

Which of the saved recipients receive this agent's report is chosen per
workspace on the dashboard (Email settings, stored by label in the agent's own
store). Until an admin chooses, every saved recipient receives it. The optional
WPA_RECIPIENT_LABELS environment default (comma-separated labels) applies only
to workspaces with no selection.
"""
import os
import re

from .workspace_context import mask_email

_ADDRESS_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

REASON_AMBIGUOUS = "more than one saved recipient has this name"
REASON_INVALID = "the saved address is not a valid email address"
REASON_MISSING = "no saved recipient has this name in the workspace"
REASON_NONE = "the workspace has no saved email recipients (Email Config)"
REASON_WRONG_WORKSPACE = "recipient list belongs to a different workspace"
REASON_NONE_SELECTED = "no recipients are selected in the agent's Email settings"


def normalize_label(label):
    return re.sub(r"\s+", " ", str(label or "")).strip().casefold()


def label_filter_from_env():
    raw = os.environ.get("WPA_RECIPIENT_LABELS", "")
    labels = [normalize_label(x) for x in raw.split(",") if normalize_label(x)]
    return labels or None


def resolve_workspace_recipients(ctx, workspace_id, label_filter=None):
    """
    Returns (resolved, problems):
      resolved: [{"label", "address", "address_masked", "recipient_key"}]
      problems: [{"label", "reason"}]
    `ctx` must be the freshly resolved context for `workspace_id`.
    """
    if ctx is None or str(ctx.workspace_id) != str(workspace_id):
        return [], [{"label": None, "reason": REASON_WRONG_WORKSPACE}]
    index = {}
    for entry in ctx.email_recipients or []:
        if not isinstance(entry, dict):
            continue
        label = str(entry.get("label") or "").strip()
        key = normalize_label(label)
        if key:
            index.setdefault(key, []).append((label, str(entry.get("address") or "").strip()))
    if not index:
        return [], [{"label": None, "reason": REASON_NONE}]
    if label_filter is not None and not label_filter:
        return [], [{"label": None, "reason": REASON_NONE_SELECTED}]
    keys = label_filter if label_filter is not None else sorted(index)
    resolved, problems = [], []
    for key in keys:
        matches = index.get(key)
        if not matches:
            problems.append({"label": key, "reason": REASON_MISSING})
        elif len(matches) > 1:
            problems.append({"label": matches[0][0], "reason": REASON_AMBIGUOUS})
        elif not _ADDRESS_RE.match(matches[0][1]):
            problems.append({"label": matches[0][0], "reason": REASON_INVALID})
        else:
            label, address = matches[0]
            resolved.append({"label": label, "address": address, "address_masked": mask_email(address),
                             "recipient_key": key})
    return resolved, problems


def saved_list(ctx):
    """Every saved Email Config recipient of the workspace: label, masked address, key."""
    out, seen = [], set()
    for entry in (ctx.email_recipients if ctx else None) or []:
        if not isinstance(entry, dict):
            continue
        label = str(entry.get("label") or "").strip()
        key = normalize_label(label)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append({"label": label, "key": key,
                    "address_masked": mask_email(str(entry.get("address") or "").strip())})
    return out


def public_summary(ctx, workspace_id, label_filter=None):
    resolved, problems = resolve_workspace_recipients(ctx, workspace_id, label_filter)
    return {"recipients": [{"label": r["label"], "address_masked": r["address_masked"]} for r in resolved],
            "problems": problems, "filtered_by_deployment_default": bool(label_filter)}

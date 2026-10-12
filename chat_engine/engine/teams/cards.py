"""
Adaptive Cards for Teams replies.

Teams does not render markdown tables in bot messages, so query results go
out as an Adaptive Card Table (v1.5). Cards are kept well under Teams' ~100 KB
message limit: at most 10 rows x 8 columns, with cell text truncated.
"""

import json

from microsoft_agents.hosting.core import CardFactory, MessageFactory

MAX_ROWS = 10
MAX_COLUMNS = 8
MAX_CELL_CHARS = 60
MAX_CARD_BYTES = 80_000

_SCHEMA = "http://adaptivecards.io/schemas/adaptive-card.json"


def _card(body, actions=None):
    card = {"type": "AdaptiveCard", "$schema": _SCHEMA, "version": "1.5", "body": body}
    if actions:
        card["actions"] = actions
    return card


def _cell(value, bold=False):
    text = "" if value is None else str(value)
    if len(text) > MAX_CELL_CHARS:
        text = text[: MAX_CELL_CHARS - 1] + "…"
    block = {"type": "TextBlock", "text": text, "wrap": True, "size": "Small"}
    if bold:
        block["weight"] = "Bolder"
    return {"type": "TableCell", "items": [block]}


def _table(columns, rows):
    shown_columns = columns[:MAX_COLUMNS]
    table_rows = [{"type": "TableRow", "cells": [_cell(c, bold=True) for c in shown_columns]}]
    for row in rows[:MAX_ROWS]:
        table_rows.append({"type": "TableRow", "cells": [_cell(row.get(c)) for c in shown_columns]})
    return {
        "type": "Table",
        "columns": [{"width": 1} for _ in shown_columns],
        "rows": table_rows,
        "firstRowAsHeader": True,
        "showGridLines": True,
    }


def _sql_action(sql):
    return {
        "type": "Action.ShowCard",
        "title": "Show SQL",
        "card": _card([{"type": "TextBlock", "text": sql, "wrap": True, "fontType": "Monospace", "size": "Small"}]),
    }


def answer_message(result):
    """Reply for a run_chat_turn "answer": summary + result table + SQL."""
    summary = result.get("text") or ""
    columns = result.get("columns") or []
    rows = result.get("rows") or []
    total = result.get("total_rows", len(rows))

    body = []
    if summary:
        body.append({"type": "TextBlock", "text": summary, "wrap": True})
    if columns and rows:
        body.append(_table(columns, rows))
        notes = []
        if total > MAX_ROWS:
            notes.append(f"Showing {min(MAX_ROWS, len(rows))} of {total} rows")
        if len(columns) > MAX_COLUMNS:
            notes.append(f"{MAX_COLUMNS} of {len(columns)} columns")
        if notes:
            body.append({
                "type": "TextBlock", "isSubtle": True, "size": "Small", "wrap": True,
                "text": " · ".join(notes) + " — open the WAI tab for the full result.",
            })
    if not body:
        body.append({"type": "TextBlock", "text": "No data available for your request.", "wrap": True})

    actions = [_sql_action(result["sql"])] if result.get("sql") else None
    card = _card(body, actions)
    if len(json.dumps(card)) > MAX_CARD_BYTES:
        # Pathologically wide values: fall back to summary + SQL only.
        card = _card([b for b in body if b.get("type") != "Table"], actions)
    return MessageFactory.attachment(CardFactory.adaptive_card(card), text=None)


def write_confirmation_message(result, workspace_id):
    preview = result.get("preview") or {}
    facts = [
        {"title": "Operation", "value": str(preview.get("operation") or "?")},
        {"title": "Table", "value": str(preview.get("table") or "?")},
    ]
    estimate = preview.get("affected_rows_estimate")
    facts.append({"title": "Rows affected (approx.)", "value": "unknown" if estimate is None else str(estimate)})
    body = [
        {"type": "TextBlock", "text": "Confirm data change", "weight": "Bolder", "size": "Medium"},
        {"type": "TextBlock", "text": result.get("question") or "", "wrap": True, "isSubtle": True},
        {"type": "FactSet", "facts": facts},
        {"type": "TextBlock", "text": result.get("text") or "", "wrap": True, "fontType": "Monospace", "size": "Small"},
        {"type": "TextBlock", "text": "Only an admin can confirm. The request expires in 10 minutes.", "wrap": True, "size": "Small", "isSubtle": True},
    ]
    payload = {"write_id": result.get("write_id"), "workspace_id": workspace_id}
    actions = [
        {"type": "Action.Submit", "title": "Confirm & execute", "style": "destructive", "data": {"wai_action": "confirm_write", **payload}},
        {"type": "Action.Submit", "title": "Cancel", "data": {"wai_action": "cancel_write", **payload}},
    ]
    return MessageFactory.attachment(CardFactory.adaptive_card(_card(body, actions)))


def help_message(tab_available=True):
    lines = [
        "**Ask about your warehouse data** — e.g. *How many orders shipped today?* "
        "Follow-up questions build on the previous answer; say **reset** to start over.",
        "**Schedule reports and alerts** — e.g. *Email open orders to my manager every Monday at 9am* "
        "or *Notify me when stock of item X drops below 50*. Use **/list** to see your agents, "
        "**/stop <id>** to cancel one, **/email list** for registered recipients.",
        "**Voice** — attach an audio file (paperclip) with your question and I'll transcribe it.",
    ]
    if tab_available:
        lines.append("**Talk and listen** — open the **WAI** tab above this chat to ask by voice and hear the answers.")
    body = [{"type": "TextBlock", "text": "Warehouse Intelligence (WAI)", "weight": "Bolder", "size": "Medium"}]
    body += [{"type": "TextBlock", "text": line, "wrap": True} for line in lines]
    return MessageFactory.attachment(CardFactory.adaptive_card(_card(body)))


def text_message(text):
    # Teams renders bot text as markdown, where a single newline doesn't break
    # the line — keep multi-line answers (e.g. /list output) readable.
    return MessageFactory.text((text or "").replace("\r\n", "\n").replace("\n", "\n\n"))


def scheduled_result_message(text, rows=None):
    """Proactive delivery of a scheduled agent's result."""
    if rows:
        columns = list(rows[0].keys())
        return answer_message({"text": text, "columns": columns, "rows": rows, "total_rows": len(rows)})
    return text_message(text)

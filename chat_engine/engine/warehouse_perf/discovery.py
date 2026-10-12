"""
Phase 1 — automatic, read-only discovery of usable operational data.

Nothing here assumes a particular table or column exists. The workspace's own
catalog (INFORMATION_SCHEMA, read through the read-only executor) is
classified by column name tokens and SQL types into roles:

  warehouse identifier, order identifier, quantity, process/activity type,
  status, category, zone, shift, and event timestamps — generic ("tran date")
  or process-stage specific (created / picked / packed / loaded / dispatched /
  completed). A "<x>_date" column paired with a "<x>_time" column (the
  HighJump-style split date/time layout) becomes one combined timestamp.

Tables are then ranked as candidate *sources*:
  activity — a transaction/activity log (timestamp + quantity or process type)
  orders   — an order table (order id + one or more stage timestamps)
Up to PROBE_CANDIDATES of each are probed with a bounded COUNT/MIN/MAX query
over the look-back window and the one with the most recent rows wins. A
timestamp whose rows are ~all at midnight is downgraded to daily granularity.

The result (the "schema model") lists which metrics can be derived, the exact
table/columns each uses (shown in reports as evidence), and — for every metric
that can NOT be derived — why. Nothing is ever defaulted or fabricated.

For the Investigator agent the model also records cause evidence, found the same
way: the activity log's person column (employee/user/operator) and item column,
and an exception/error log table (timestamp + exception type and/or description).
"""
import hashlib
import re
from datetime import datetime, timezone

DT_TYPES = {"datetime", "datetime2", "smalldatetime", "datetimeoffset"}
DATE_TYPES = {"date"}
TIME_TYPES = {"time"}
NUM_TYPES = {"int", "bigint", "smallint", "tinyint", "decimal", "numeric", "float", "real"}
GROUPABLE_TYPES = {"char", "varchar", "nchar", "nvarchar", "int", "bigint", "smallint", "tinyint"}
MAX_DIM_LENGTH = 100
EXCLUDED_SCHEMAS = {"sys", "information_schema", "guest", "cdc", "db_owner", "db_accessadmin"}
PROBE_CANDIDATES = 3
MIDNIGHT_SHARE_FOR_DAILY = 0.95
MODEL_VERSION = 2          # 2: adds the Investigator's evidence sources (older cached models are re-scanned)

HIGHER, LOWER, NEUTRAL = "higher_is_better", "lower_is_better", "neutral"

WAREHOUSE_WORDS = {"wh", "whse", "warehouse", "site", "facility", "dc", "depot", "branch", "plant"}
KEY_WORDS = {"number", "num", "no", "nbr", "id", "key", "ref", "code"}
ORDER_WORDS = {"order", "orders"}
QTY_WORDS = {"qty", "quantity", "units", "pieces", "pcs", "eaches", "cases", "cartons"}
QTY_GOOD = {"picked", "shipped", "moved", "tran", "actual", "act", "confirmed", "dispatched", "despatched",
            "loaded", "packed", "processed", "move"}
QTY_BAD = {"planned", "plan", "ordered", "requested", "req", "allocated", "alloc", "min", "max", "reorder",
           "capacity", "cap", "conversion", "conv", "std", "standard", "default", "threshold", "limit", "safety",
           "backorder", "expected", "exp", "open", "remaining", "avail", "available", "onhand"}
QTY_EXCLUDE = {"weight", "wt", "volume", "vol", "price", "cost", "amount", "amt", "value", "val", "rate", "pct",
               "percent", "factor", "length", "width", "height", "cube", "days", "hours", "minutes", "seconds",
               "sequence", "seq", "priority", "level", "status", "uom", "per"}
STAGE_WORDS = {
    "picked": {"pick", "picked", "picking"},
    "packed": {"pack", "packed", "packing"},
    "loaded": {"load", "loaded", "loading"},
    "dispatched": {"ship", "shipped", "shipping", "dispatch", "dispatched", "despatch", "despatched", "depart",
                   "departed", "departure"},
    "completed": {"complete", "completed", "completion", "closed", "close", "finished", "finish"},
    "created": {"created", "create", "creation", "entered", "entry", "added", "inserted", "placed", "booked"},
}
STAGE_ORDER = ["created", "picked", "packed", "loaded", "dispatched", "completed"]
TS_EXCLUDE = {"due", "required", "req", "promise", "promised", "expected", "expiry", "expire", "expiration", "plan",
              "planned", "scheduled", "sched", "requested", "target", "eta", "etd", "manufactured", "mfg",
              "manufacture", "best", "birth", "dob", "hire", "effective", "valid", "modified", "modify", "updated",
              "update", "changed", "sync", "synced", "export", "exported", "import", "imported", "archived",
              "archive", "printed", "print", "deleted", "cancel", "cancelled", "canceled", "lock", "locked",
              "earliest", "latest", "window", "cutoff", "deadline", "appointment", "appt", "forecast", "estimated",
              "est"}
EVENT_WORDS = {"tran", "transaction", "trans", "txn", "event", "activity", "scan", "scanned", "logged", "performed"}
DATE_WORDS = {"date", "datetime", "timestamp", "ts", "dt", "time"}
PROCESS_SUBJECT = {"tran", "transaction", "trans", "txn", "activity", "task", "work", "process", "operation", "event",
                   "move", "movement"}
PROCESS_KIND = {"type", "code", "kind"}
CATEGORY_WORDS = {"category", "class", "family", "commodity", "dept", "department"}
ZONE_WORDS = {"zone", "area"}
SHIFT_WORDS = {"shift"}
DESCRIPTIVE = {"name", "desc", "description", "address", "addr", "phone", "email", "city", "state", "country", "zip",
               "postal", "comment", "comments", "note", "notes", "text", "msg", "message"}

ACTIVITY_TABLE_WORDS = {"tran", "transaction", "transactions", "trans", "txn", "activity", "activities", "movement",
                        "movements", "move", "moves", "history", "hist", "log", "task", "tasks", "work", "scan",
                        "scans", "event", "events", "pick", "picks", "picking", "productivity"}
ORDER_TABLE_WORDS = {"order", "orders", "shipment", "shipments", "outbound", "so", "despatch", "dispatch"}
DETAIL_TABLE_WORDS = {"detail", "details", "line", "lines", "item", "items", "dtl"}
EXCLUDED_TABLE_WORDS = {"archive", "arch", "backup", "bak", "bkp", "tmp", "temp", "staging", "stg", "test", "copy",
                        "old", "audit", "error", "errors", "exception", "exceptions", "config", "setting",
                        "settings", "lookup", "control", "message", "messages", "host", "interface", "snapshot",
                        "comment", "comments", "image", "images", "label", "labels", "sysdiagrams", "report",
                        "reports", "import", "export", "hold", "holds"}

ACTOR_WORDS = {"employee", "emp", "user", "operator", "worker", "picker", "staff", "associate"}
ITEM_WORDS = {"item", "sku", "product", "material", "article"}
EXCEPTION_TABLE_WORDS = {"exception", "exceptions", "error", "errors", "alert", "alerts", "alarm", "alarms",
                         "incident", "incidents", "fault", "faults"}
REASON_WORDS = {"type", "code", "kind", "reason"}

VOCAB = (WAREHOUSE_WORDS | KEY_WORDS | ORDER_WORDS | QTY_WORDS | QTY_GOOD | QTY_BAD | TS_EXCLUDE | EVENT_WORDS
         | DATE_WORDS | PROCESS_SUBJECT | PROCESS_KIND | CATEGORY_WORDS | ZONE_WORDS | SHIFT_WORDS | DESCRIPTIVE
         | set().union(*STAGE_WORDS.values())
         | {"status", "item", "line", "detail", "master", "header", "hdr", "user", "emp", "employee", "location",
            "loc", "lot", "start", "end", "from", "to", "last", "first", "sales", "customer", "cust", "carrier",
            "load", "wave", "sku", "product", "prod", "unit", "total", "count", "stamp", "tm"})

# canonical metrics: id -> (label, unit, direction)
METRICS = {
    "units_moved": ("Units moved", "units", HIGHER),
    "transactions": ("Warehouse transactions", "transactions", HIGHER),
    "orders_received": ("Orders received", "orders", NEUTRAL),
    "orders_picked": ("Orders picked", "orders", HIGHER),
    "orders_packed": ("Orders packed", "orders", HIGHER),
    "orders_loaded": ("Orders loaded", "orders", HIGHER),
    "orders_dispatched": ("Orders dispatched", "orders", HIGHER),
    "orders_completed": ("Orders completed", "orders", HIGHER),
    "pending_orders": ("Pending orders (backlog)", "orders", LOWER),
    "processing_time": ("Order processing time", "minutes", LOWER),
}
STAGE_METRIC = {"created": "orders_received", "picked": "orders_picked", "packed": "orders_packed",
                "loaded": "orders_loaded", "dispatched": "orders_dispatched", "completed": "orders_completed"}
STAGE_PROCESS_LABEL = {"picked": "picking", "packed": "packing", "loaded": "loading", "dispatched": "dispatch",
                       "completed": "completion"}
STAGE_NOUN = {"created": "order-created", "picked": "picking", "packed": "packing", "loaded": "loading",
              "dispatched": "dispatch", "completed": "completion"}


# ------------------------------------------------------------------ tokens
def _compound(tok):
    if tok in VOCAB or len(tok) <= 3:
        return [tok]
    best = {0: []}
    for i in range(1, len(tok) + 1):
        for j in range(max(0, i - 14), i - 1):
            if j in best and tok[j:i] in VOCAB:
                cand = best[j] + [tok[j:i]]
                if i not in best or len(cand) < len(best[i]):
                    best[i] = cand
    return best.get(len(tok)) or [tok]


def split_tokens(name):
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(name or ""))
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    out = []
    for raw in re.split(r"[^A-Za-z0-9]+", s.lower()):
        for piece in re.split(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", raw):
            if piece and not piece.isdigit():
                out.extend(_compound(piece))
    return out


# ------------------------------------------------------------ column roles
class Column:
    __slots__ = ("name", "type", "length", "tokens")

    def __init__(self, name, data_type, length=None):
        self.name = str(name)
        self.type = str(data_type or "").strip().lower()
        try:
            self.length = int(length) if length is not None else None
        except (TypeError, ValueError):
            self.length = None
        self.tokens = split_tokens(self.name)

    @property
    def tset(self):
        return set(self.tokens)

    def is_temporal(self):
        return self.type in DT_TYPES or self.type in DATE_TYPES

    def groupable(self):
        return self.type in GROUPABLE_TYPES and (self.length is None or 0 < self.length <= MAX_DIM_LENGTH)


def stage_of(col):
    t = col.tset
    for stage in ("dispatched", "completed", "loaded", "packed", "picked", "created"):
        if t & STAGE_WORDS[stage]:
            return stage
    if "order" in t and t & {"date", "datetime", "dt", "time"} and len(t) <= 3:
        return "created"
    return None


def _ts_ok(col):
    return col.is_temporal() and not (col.tset & TS_EXCLUDE)


def event_ts_score(col):
    if not _ts_ok(col):
        return 0
    t = col.tset
    s = 0.0
    if t & EVENT_WORDS:
        s += 3
    if "start" in t:
        s += 1
    if "end" in t:
        s += 0.5
    if t & DATE_WORDS:
        s += 1
    if stage_of(col) == "created":
        s += 0.5
    return s


def warehouse_score(col):
    if not col.groupable() or col.is_temporal():
        return 0
    t = col.tset
    if not t & WAREHOUSE_WORDS or t & DESCRIPTIVE or t & {"type", "status", "group"}:
        return 0
    s = 2.0
    if t & KEY_WORDS:
        s += 1
    if col.tokens and col.tokens[0] in WAREHOUSE_WORDS:
        s += 0.5
    if t & {"wh", "whse", "warehouse"}:
        s += 0.5
    return s


def order_key_score(col):
    if not col.groupable() or col.is_temporal():
        return 0
    t = col.tset
    if t & ORDER_WORDS:
        others = t - ORDER_WORDS
        if others and others <= KEY_WORDS:
            return 3
        if not others:
            return 1.5
    if t & {"so", "salesorder"} and (t - {"so", "salesorder", "sales", "order"}) <= KEY_WORDS and len(t) >= 2:
        return 2
    return 0


def quantity_score(col):
    if col.type not in NUM_TYPES:
        return 0
    t = col.tset
    if not t & QTY_WORDS or t & QTY_EXCLUDE:
        return 0
    return max(0.1, 2 + len(t & QTY_GOOD) - 1.5 * len(t & QTY_BAD) - (1 if t & ORDER_WORDS else 0))


def process_score(col):
    if not col.groupable() or col.is_temporal():
        return 0
    t = col.tset
    if t & DESCRIPTIVE:
        return 0
    if t & PROCESS_SUBJECT and t & PROCESS_KIND:
        return 3 if t & {"tran", "transaction", "trans", "txn", "activity", "task", "process", "work"} else 2
    if t in ({"process"}, {"operation"}, {"stage"}, {"activity"}, {"step"}):
        return 2
    return 0


def dim_score(col, words):
    if not col.groupable() or col.is_temporal():
        return 0
    t = col.tset
    if not t & words or t & DESCRIPTIVE or t & WAREHOUSE_WORDS:
        return 0
    return 2 + (1 if t & KEY_WORDS or len(t) == 1 else 0)


def status_score(col):
    if not col.groupable() or col.is_temporal():
        return 0
    t = col.tset
    if "status" not in t or t & DESCRIPTIVE or t & DATE_WORDS:
        return 0
    return 3 if col.tokens == ["status"] else 2 - 0.1 * len(t)


TEXT_TYPES = {"char", "varchar", "nchar", "nvarchar", "text", "ntext"}
DESC_WORDS = {"description", "desc", "descr"}
PICK_WORDS = {"pick", "picked", "picking"}
SHIP_WORDS = {"ship", "shipped", "shipping", "shipment", "dispatch", "dispatched", "despatch", "despatched"}
# Never outbound throughput: reversals/voids, and - in HighJump-style logs - internal moves that are
# also labelled "(Pick)", the "put" half of a pick/put pair, replenishment and loading.
NOT_OUTBOUND_WORDS = {"unpick", "unship", "cancel", "cancelled", "canceled", "reverse", "reversal", "reversed", "undo",
                      "void", "voided", "return", "returned", "adjust", "adjustment", "delete", "deleted", "short",
                      "correction", "correct", "reject", "rejected", "error", "denial", "move", "moves",
                      "movement", "replenishment", "replen", "slot", "transfer", "relocate", "relocation", "put",
                      "putaway", "load", "loading", "loaded", "unload", "request"}


def description_for(proc_col, columns):
    """The human-readable label column for an activity-type code column, e.g.
    t_tran_log.description for t_tran_log.tran_type. Prefers a description that
    shares the code column's subject (tran_description); plain "description" is fine."""
    subject = proc_col.tset - PROCESS_KIND
    best, best_score = None, 0
    for c in columns:
        if c is proc_col or c.type not in TEXT_TYPES or not (c.tset & DESC_WORDS):
            continue
        score = 2 + (1 if c.tset & subject else 0) - 0.1 * len(c.tset - DESC_WORDS - subject)
        if score > best_score:
            best, best_score = c, score
    return best


def outbound_stage(label):
    """"pick" / "ship" for an order-picking or shipping transaction type, else None."""
    t = set(split_tokens(label))
    if t & NOT_OUTBOUND_WORDS:
        return None
    if t & PICK_WORDS:
        return "pick"
    if t & SHIP_WORDS:
        return "ship"
    return None


def classify_process_labels(rows):
    """rows: [{"code", "label", "rows"}] -> labels plus the codes units moved should count.
    Units moved counts ONE outbound stage so a unit is not counted twice: picking types
    when any exist, otherwise shipping types."""
    labels, pick, ship = {}, [], []
    for r in rows or []:
        code = str(r.get("code") if r.get("code") is not None else "").strip()
        if not code:
            continue
        label = str(r.get("label") or "").strip()
        labels[code] = label
        stage = outbound_stage(label) if label else None
        if stage == "pick":
            pick.append(code)
        elif stage == "ship":
            ship.append(code)
    pick, ship = sorted(pick), sorted(ship)
    return {"labels": labels, "pick_codes": pick, "ship_codes": ship, "outbound_codes": pick or ship,
            "outbound_stage": "pick" if pick else ("ship" if ship else None)}


def actor_score(col):
    """The person who recorded the work (employee_id, user_id, operator)."""
    if not col.groupable() or col.is_temporal():
        return 0
    t = col.tset
    if not t & ACTOR_WORDS or t & DESCRIPTIVE or t & {"type", "status", "group", "count", "qty", "class"}:
        return 0
    if not (t & KEY_WORDS or len(t) == 1):
        return 0
    return 2 + (0.5 if col.tokens and col.tokens[0] in ACTOR_WORDS else 0) - 0.1 * len(t)


def item_score(col):
    if not col.groupable() or col.is_temporal():
        return 0
    t = col.tset
    if not t & ITEM_WORDS or t & DESCRIPTIVE or t & {"type", "status", "group", "class", "category", "qty", "uom",
                                                       "count", "weight"}:
        return 0
    if not (t & KEY_WORDS or len(t) == 1):
        return 0
    return 2 - 0.1 * len(t)


def reason_score(col):
    """Exception/error type column of an exception log."""
    if not col.groupable() or col.is_temporal():
        return 0
    t = col.tset
    if t & DESCRIPTIVE or not t & REASON_WORDS:
        return 0
    return 1 + (2 if process_score(col) else 0) + (1 if t & (EXCEPTION_TABLE_WORDS | {"reason"}) else 0)


def _best(columns, score_fn):
    scored = [(score_fn(c), -i, c) for i, c in enumerate(columns)]
    scored = [s for s in scored if s[0] > 0]
    if not scored:
        return None
    scored.sort(key=lambda s: (s[0], s[1]), reverse=True)
    return scored[0][2]


def timestamp_for(col, columns):
    """-> {"column", "time_column", "granularity"} for a temporal column,
    pairing <x>_date with <x>_time where present."""
    toks = col.tokens
    if "date" in toks or "dt" in toks:
        want = [("time" if t == "date" else "tm" if t == "dt" else t) for t in toks]
        for other in columns:
            if other is col or other.type not in (DT_TYPES | TIME_TYPES):
                continue
            if other.tokens == want or (other.tokens == [("time" if t in ("date", "dt") else t) for t in toks]):
                return {"column": col.name, "time_column": other.name, "granularity": "hour"}
    return {"column": col.name, "time_column": None,
            "granularity": "day" if col.type in DATE_TYPES else "hour"}


# ----------------------------------------------------------------- tables
def _table_excluded(tokens):
    return bool(set(tokens) & EXCLUDED_TABLE_WORDS)


def analyse_table(schema, table, table_type, columns):
    """Returns (activity_candidate | None, orders_candidate | None)."""
    ttoks = split_tokens(table)
    if _table_excluded(ttoks):
        return None, None
    is_view = str(table_type or "").upper() == "VIEW"
    wh = _best(columns, warehouse_score)
    dims = {}
    for key, words in (("category", CATEGORY_WORDS), ("zone", ZONE_WORDS), ("shift", SHIFT_WORDS)):
        c = _best(columns, lambda col, w=words: dim_score(col, w))
        if c is not None:
            dims[key] = c.name
    status = _best(columns, status_score)
    ref = {"schema": schema, "table": table, "is_view": is_view}

    activity = None
    ts_col = _best(columns, event_ts_score)
    qty = _best(columns, quantity_score)
    proc = _best(columns, process_score)
    name_match = bool(set(ttoks) & ACTIVITY_TABLE_WORDS)
    if ts_col is not None and (qty is not None or proc is not None) and (name_match or (qty and proc)):
        score = (3 if name_match else 0) + (1 if qty else 0) + (1 if proc else 0) + (0.5 if wh else 0) \
            + 0.2 * event_ts_score(ts_col) - (1 if is_view else 0)
        desc = description_for(proc, columns) if proc is not None else None
        actor = _best(columns, actor_score)
        item = _best(columns, item_score)
        activity = {**ref, "score": round(score, 2), "ts": timestamp_for(ts_col, columns),
                    "warehouse": wh.name if wh else None, "quantity": qty.name if qty else None,
                    "process": proc.name if proc else None, "process_description": desc.name if desc else None,
                    "actor": actor.name if actor else None, "item": item.name if item else None,
                    "dims": dims}

    orders = None
    key = _best(columns, order_key_score)
    if key is not None:
        stages = {}
        for stage in STAGE_ORDER:
            cands = [c for c in columns if _ts_ok(c) and stage_of(c) == stage]
            if cands:
                cands.sort(key=lambda c: (c.type in DT_TYPES, "date" in c.tokens or "time" in c.tokens, -len(c.tokens)),
                           reverse=True)
                stages[stage] = timestamp_for(cands[0], columns)
        order_name = bool(set(ttoks) & ORDER_TABLE_WORDS)
        if stages and (order_name or len(stages) >= 2):
            score = (3 if order_name else 0) + len(stages) + (1 if "dispatched" in stages else 0) \
                + (1 if "created" in stages else 0) + (0.5 if wh else 0) \
                - (2 if set(ttoks) & DETAIL_TABLE_WORDS else 0) - (1 if is_view else 0)
            orders = {**ref, "score": round(score, 2), "order_key": key.name, "warehouse": wh.name if wh else None,
                      "stages": stages, "status": status.name if status else None, "dims": dims}
    return activity, orders


def analyse_exception_table(schema, table, table_type, columns):
    """An exception/error log: a table named like one, with an event timestamp and an
    exception type and/or description. Returns a candidate or None."""
    ttoks = set(split_tokens(table))
    if not ttoks & EXCEPTION_TABLE_WORDS or ttoks & (EXCLUDED_TABLE_WORDS - EXCEPTION_TABLE_WORDS):
        return None
    subject = ttoks - {"t", "tbl", "log", "logs", "history", "hist"}

    def ts_score(col):
        if not _ts_ok(col):
            return 0
        t = col.tset
        return (1 + (1 if t & subject else 0) + (0.5 if t & {"date", "datetime", "timestamp", "dt"} else 0)
                + (0.5 if t & EVENT_WORDS else 0) + (0.25 if t & {"created", "logged"} else 0))

    ts_col = _best(columns, ts_score)
    if ts_col is None:
        return None
    kind = _best(columns, reason_score)
    desc = description_for(kind, columns) if kind is not None else next(
        (c for c in columns if c.type in TEXT_TYPES and c.tset & DESC_WORDS), None)
    if kind is None and desc is None:
        return None
    wh = _best(columns, warehouse_score)
    is_view = str(table_type or "").upper() == "VIEW"
    score = 2 + (1 if kind else 0) + (1 if desc else 0) + (0.5 if wh else 0) - (1 if is_view else 0)
    return {"schema": schema, "table": table, "is_view": is_view, "score": round(score, 2),
            "ts": timestamp_for(ts_col, columns), "type": kind.name if kind else None,
            "description": desc.name if desc else None, "warehouse": wh.name if wh else None}


def group_catalog(rows):
    """rows: [{"schema","table","column","data_type","max_length"?,"table_type"?}] ->
    {(schema, table): {"table_type", "columns": [Column]}}"""
    tables = {}
    for r in rows or []:
        schema = str(r.get("schema") or "dbo")
        if schema.lower() in EXCLUDED_SCHEMAS:
            continue
        key = (schema, str(r.get("table")))
        entry = tables.setdefault(key, {"table_type": r.get("table_type") or "BASE TABLE", "columns": []})
        entry["columns"].append(Column(r.get("column"), r.get("data_type"), r.get("max_length")))
    return tables


def _probe_ts(candidate, kind):
    if kind == "activity":
        return candidate["ts"]
    st = candidate["stages"]
    return st.get("dispatched") or st.get("completed") or st.get("created") or next(iter(st.values()))


def discover(catalog_rows, probe=None, now=None, db_fingerprint=None, process_labels=None):
    """
    catalog_rows: the workspace catalog (see group_catalog).
    probe(candidate, ts, wide=False) -> {"rows": int, "first_ts", "last_ts", "midnight_rows"} for
        the look-back window (wide=True: the last ten years, used only to report how old the
        newest record is); may raise (a failing candidate is skipped and noted).
    process_labels(candidate) -> [{"code", "label", "rows"}] for the chosen activity table's
        activity-type codes and their descriptions in the look-back window; may raise.
    Returns the JSON-serialisable schema model.
    """
    tables = group_catalog(catalog_rows)
    cands = {"activity": [], "orders": []}
    exc_cands = []
    for (schema, table), info in tables.items():
        a, o = analyse_table(schema, table, info["table_type"], info["columns"])
        if a:
            cands["activity"].append(a)
        if o:
            cands["orders"].append(o)
        e = analyse_exception_table(schema, table, info["table_type"], info["columns"])
        if e:
            exc_cands.append(e)
    notes = []
    chosen = {}
    for kind in ("activity", "orders"):
        ranked = sorted(cands[kind], key=lambda c: c["score"], reverse=True)[:PROBE_CANDIDATES]
        best = None
        for c in ranked:
            ts = _probe_ts(c, kind)
            if probe is not None:
                try:
                    p = probe(c, ts) or {}
                except Exception as exc:  # noqa: BLE001 — a candidate that can't be read is skipped, not fatal
                    c["probe"] = {"error": str(exc)[:200]}
                    notes.append(f"Candidate {kind} table {c['schema']}.{c['table']} could not be read and was skipped.")
                    continue
                c["probe"] = {"rows": int(p.get("rows") or 0), "first_ts": _iso(p.get("first_ts")),
                              "last_ts": _iso(p.get("last_ts"))}
                rows = c["probe"]["rows"]
                if rows and (p.get("midnight_rows") or 0) / rows >= MIDNIGHT_SHARE_FOR_DAILY and not ts.get("time_column"):
                    ts["granularity"] = "day"
                    notes.append(f"{c['schema']}.{c['table']}.{ts['column']} holds dates without times, so it is "
                                 f"analysed per day, not per hour.")
            else:
                c["probe"] = {"rows": None}
            if best is None or (c["probe"].get("rows") or 0) > (best["probe"].get("rows") or 0):
                best = c
        if best is not None and probe is not None and not best["probe"].get("rows"):
            latest = None
            try:
                wide = probe(best, _probe_ts(best, kind), True) or {}
                latest = _iso(wide.get("last_ts"))
                best["probe"]["latest_record"] = latest
                best["probe"]["rows_all_time"] = int(wide.get("rows") or 0)
            except Exception:  # noqa: BLE001 — diagnostic only
                pass
            notes.append(f"The best {kind} table found ({best['schema']}.{best['table']}) has no rows in the "
                         f"look-back window" + (f"; its latest record is from {latest[:10]}." if latest else "."))
        chosen[kind] = best

    act = chosen.get("activity")
    if act and act.get("process") and act.get("process_description") and process_labels is not None             and (act.get("probe") or {}).get("rows"):
        try:
            act.update(classify_process_labels(process_labels(act)))
        except Exception as exc:  # noqa: BLE001 — labels are an enhancement; codes still work without them
            notes.append(f"Activity-type descriptions could not be read ({str(exc)[:120]}); raw codes are shown.")

    metrics, unavailable = derive_metrics(chosen.get("activity"), chosen.get("orders"))
    exceptions = _choose_exception_log(exc_cands, probe, notes)
    fp = db_fingerprint
    return {
        "model_version": MODEL_VERSION,
        "discovered_at": (now or datetime.now(timezone.utc)).isoformat(),
        "db_fingerprint": fp,
        "tables_scanned": len(tables),
        "columns_scanned": sum(len(v["columns"]) for v in tables.values()),
        "sources": chosen,
        "candidates": {k: [{"table": f"{c['schema']}.{c['table']}", "score": c["score"],
                            "rows": (c.get("probe") or {}).get("rows")} for c in
                           sorted(v, key=lambda c: c["score"], reverse=True)[:5]] for k, v in cands.items()},
        "metrics": metrics,
        "unavailable": unavailable,
        "evidence_sources": {"exceptions": exceptions},
        "notes": notes,
    }


def _choose_exception_log(cands, probe, notes):
    """The exception log with the most rows in the look-back window (probed like the
    activity/order candidates); None when the database has none."""
    best = None
    for c in sorted(cands, key=lambda c: c["score"], reverse=True)[:PROBE_CANDIDATES]:
        if probe is not None:
            try:
                p = probe(c, c["ts"]) or {}
            except Exception:  # noqa: BLE001 — an unreadable candidate is skipped
                continue
            c["probe"] = {"rows": int(p.get("rows") or 0), "first_ts": _iso(p.get("first_ts")),
                          "last_ts": _iso(p.get("last_ts"))}
            rows = c["probe"]["rows"]
            if rows and (p.get("midnight_rows") or 0) / rows >= MIDNIGHT_SHARE_FOR_DAILY \
                    and not c["ts"].get("time_column"):
                c["ts"]["granularity"] = "day"
        else:
            c["probe"] = {"rows": None}
        if best is None or (c["probe"].get("rows") or 0) > (best["probe"].get("rows") or 0):
            best = c
    if best is not None and probe is not None and not best["probe"].get("rows"):
        try:
            wide = probe(best, best["ts"], True) or {}
            best["probe"]["latest_record"] = _iso(wide.get("last_ts"))
        except Exception:  # noqa: BLE001 — diagnostic only
            pass
    if best is not None:
        notes.append(f"Exception log for root-cause checks: {best['schema']}.{best['table']}.")
    return best


def _iso(v):
    if v is None:
        return None
    return v.isoformat() if hasattr(v, "isoformat") else str(v)


def _metric(mid, source, **extra):
    label, unit, direction = METRICS[mid]
    return {"metric_id": mid, "label": label, "unit": unit, "direction": direction, "source": source, **extra}


def derive_metrics(activity, orders):
    metrics, unavailable = [], []

    def missing(mid, reason):
        unavailable.append({"metric_id": mid, "label": METRICS[mid][0], "reason": reason})

    if activity and (activity.get("probe") or {}).get("rows") != 0:
        metrics.append(_metric("transactions", "activity", measure="count"))
        if activity.get("quantity"):
            codes = activity.get("outbound_codes") or []
            labels = activity.get("labels") or {}
            if codes:
                stage = "picking" if activity.get("outbound_stage") == "pick" else "shipping"
                scope = (f"Units moved counts {activity['quantity']} for {stage} transaction types only ("
                         + ", ".join(f"{labels.get(c) or c} ({c})" for c in codes)
                         + "), so each unit is counted once. Moves, replenishment, put-away, loading, "
                           "reversals and adjustments are excluded.")
                if stage == "picking" and activity.get("ship_codes"):
                    scope += " Shipping types are not added, to avoid counting picked units a second time."
            else:
                scope = ("No pick/ship transaction types could be identified from the transaction descriptions, so "
                         "units moved sums " + activity["quantity"] + " over all transaction types and may count "
                         "the same unit more than once as it moves through the warehouse.")
            metrics.append(_metric("units_moved", "activity", measure="sum", column=activity["quantity"],
                                   outbound_codes=codes, scope_note=scope))
        else:
            missing("units_moved", "Units moved cannot be analysed because no quantity column was found in the "
                                   "warehouse transaction/activity table.")
    else:
        reason = ("no transaction/activity table with a usable timestamp and a quantity or activity-type column "
                  "was found") if not activity else "the transaction/activity table has no rows in the look-back window"
        if activity and (activity.get("probe") or {}).get("latest_record"):
            reason += f" (latest record {activity['probe']['latest_record'][:10]})"
        missing("transactions", f"Warehouse activity cannot be analysed because {reason}.")
        missing("units_moved", f"Units moved cannot be analysed because {reason}.")

    order_ids = ["orders_received", "orders_picked", "orders_packed", "orders_loaded", "orders_dispatched",
                 "orders_completed", "pending_orders", "processing_time"]
    if not orders or (orders.get("probe") or {}).get("rows") == 0:
        reason = ("no order table with an order identifier and order timestamps was found") if not orders else \
            "the order table has no rows in the look-back window"
        if orders and (orders.get("probe") or {}).get("latest_record"):
            reason += f" (latest record {orders['probe']['latest_record'][:10]})"
        for mid in order_ids:
            missing(mid, f"{METRICS[mid][0]} cannot be analysed because {reason}.")
        return metrics, unavailable

    stages = orders["stages"]
    for stage in STAGE_ORDER:
        mid = STAGE_METRIC[stage]
        if stage in stages:
            metrics.append(_metric(mid, "orders", measure="count_distinct", column=orders["order_key"], stage=stage,
                                   process=STAGE_PROCESS_LABEL.get(stage)))
        elif stage not in ("completed",) or "dispatched" not in stages:
            noun = STAGE_NOUN[stage]
            missing(mid, f"{noun[0].upper() + noun[1:]} performance cannot be analysed because {noun} timestamps "
                         f"are unavailable." if stage != "created" else
                    "Orders received cannot be analysed because order-created timestamps are unavailable.")
    done = "dispatched" if "dispatched" in stages else ("completed" if "completed" in stages else None)
    if "created" in stages and done:
        metrics.append(_metric("pending_orders", "orders", measure="backlog", column=orders["order_key"],
                               done_stage=done))
        metrics.append(_metric("processing_time", "orders", measure="duration", done_stage=done))
    else:
        why = ("the order table does not have both an order-created timestamp and a dispatch/completion timestamp")
        missing("pending_orders", f"Pending orders/backlog cannot be analysed because {why}.")
        missing("processing_time", f"Processing time cannot be analysed because {why}.")
    return metrics, unavailable


def db_fingerprint(ctx):
    cfg = ctx.db_config or {}
    raw = "|".join(str(cfg.get(k) or "").strip().lower() for k in ("serverName", "port", "databaseName"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

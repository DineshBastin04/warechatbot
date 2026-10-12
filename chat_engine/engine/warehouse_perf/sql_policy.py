"""
Read-only SQL policy for admin-approved metric queries.

Why this exists rather than reusing VannaBase.is_sql_valid alone: is_sql_valid
returns True if ANY parsed statement is a SELECT, so "SELECT 1; DELETE FROM t"
passes it — and VannaBase.run_sql executes inside engine.begin(), which commits.
This policy is layered: a lexer separates code from string literals, comments
and bracketed/quoted identifiers (so a keyword hidden in a comment can't slip
through, and a status value like 'UPDATE PENDING' inside a literal doesn't
false-positive), then:

  1. exactly one statement (a leading ";" as in ";WITH ..." and a trailing ";"
     are tolerated — the repo's own trained examples start with ";WITH");
  2. must start with SELECT or WITH;
  3. no data-modifying, DDL, dynamic-SQL, session-changing or bulk keywords;
  4. no system databases/objects, no 4-part (linked-server) names;
  5. every table read must be on the metric's allowlist (CTE names excluded);
  6. OPENQUERY payloads are un-escaped and validated recursively by the same
     rules, since they execute on the linked server;
  7. the workspace DB-scope and OPENQUERY-literal checks from VannaBase are
     reused unchanged (validate_db_scope / validate_openquery_literals);
  8. :window_start / :window_end tokens must be present so every query is
     time-bounded; they are bound as parameters, never string-interpolated.

Column-level restrictions are enforced on the RESULT (only mapped columns are
kept) — parsing T-SQL column references reliably is out of scope; use a
read-only DB login with column GRANTs if column-level control is required.
"""
import re
from dataclasses import dataclass, field
from types import SimpleNamespace

WINDOW_START_TOKEN = ":window_start"
WINDOW_END_TOKEN = ":window_end"
MAX_SQL_LENGTH = 20000

FORBIDDEN_KEYWORDS = (
    "INSERT", "UPDATE", "DELETE", "MERGE", "DROP", "ALTER", "CREATE", "TRUNCATE",
    "EXEC", "EXECUTE", "GRANT", "REVOKE", "DENY", "BACKUP", "RESTORE", "DBCC",
    "SHUTDOWN", "KILL", "RECONFIGURE", "BULK", "OPENROWSET", "OPENDATASOURCE",
    "OPENXML", "WAITFOR", "USE", "DECLARE", "SET", "INTO", "GO", "CHECKPOINT",
    "READTEXT", "WRITETEXT", "UPDATETEXT", "REVERT", "SETUSER", "COMMIT",
    "ROLLBACK", "SAVE", "BEGIN", "TRANSACTION", "TRAN",
)
_FORBIDDEN_RE = re.compile(r"\b(" + "|".join(FORBIDDEN_KEYWORDS) + r")\b", re.IGNORECASE)
_PROC_PREFIX_RE = re.compile(r"\b(sp|xp)_\w+", re.IGNORECASE)
_VARIABLE_RE = re.compile(r"@@?\w+")
_SYSTEM_DB_RE = re.compile(r"\b(master|msdb|model|tempdb|mssqlsystemresource)\b", re.IGNORECASE)
_SYSTEM_SCHEMA_RE = re.compile(r"\b(sys|information_schema)\s*\.", re.IGNORECASE)

_CLAUSE_END = {
    "WHERE", "GROUP", "ORDER", "HAVING", "UNION", "EXCEPT", "INTERSECT", "ON", "JOIN", "INNER", "LEFT",
    "RIGHT", "FULL", "CROSS", "OUTER", "OPTION", "FOR", "WINDOW", "SELECT", "APPLY", "PIVOT", "UNPIVOT",
}
_NOT_ALIAS = _CLAUSE_END | {"AS", "WITH", "FROM"}


class SqlPolicyError(ValueError):
    pass


@dataclass
class PolicyResult:
    ok: bool
    errors: list = field(default_factory=list)
    tables: list = field(default_factory=list)
    cte_names: list = field(default_factory=list)

    def raise_if_invalid(self):
        if not self.ok:
            raise SqlPolicyError("; ".join(self.errors))


# ----------------------------------------------------------------- lexing
def _lex(sql):
    """Splits T-SQL into segments: ('code', text), ('literal', unescaped_text),
    ('ident', name) for [bracketed] / "quoted" identifiers, and drops comments.
    T-SQL block comments nest, so depth is tracked. Raises SqlPolicyError on an
    unterminated literal, identifier or comment."""
    segments = []
    buf = []
    i, n = 0, len(sql)

    def flush():
        if buf:
            segments.append(("code", "".join(buf)))
            buf.clear()

    while i < n:
        if sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j == -1 else j
            buf.append(" ")
            continue
        if sql.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if sql.startswith("/*", j):
                    depth += 1
                    j += 2
                elif sql.startswith("*/", j):
                    depth -= 1
                    j += 2
                else:
                    j += 1
            if depth:
                raise SqlPolicyError("unterminated block comment")
            i = j
            buf.append(" ")
            continue
        ch = sql[i]
        if ch == "'":
            j, parts = i + 1, []
            while True:
                if j >= n:
                    raise SqlPolicyError("unterminated string literal")
                if sql[j] == "'":
                    if j + 1 < n and sql[j + 1] == "'":
                        parts.append("'")
                        j += 2
                        continue
                    break
                parts.append(sql[j])
                j += 1
            flush()
            segments.append(("literal", "".join(parts)))
            i = j + 1
            continue
        if ch in "[\"":
            close = "]" if ch == "[" else "\""
            j, parts = i + 1, []
            while True:
                if j >= n:
                    raise SqlPolicyError("unterminated quoted identifier")
                if sql[j] == close:
                    if j + 1 < n and sql[j + 1] == close:
                        parts.append(close)
                        j += 2
                        continue
                    break
                parts.append(sql[j])
                j += 1
            flush()
            segments.append(("ident", "".join(parts)))
            i = j + 1
            continue
        buf.append(ch)
        i += 1
    flush()
    return segments


def _render(segments, literal_placeholder=True, ident_placeholder=False):
    out = []
    for idx, (kind, text) in enumerate(segments):
        if kind == "code":
            out.append(text)
        elif kind == "literal":
            out.append(f" __LIT{idx}__ " if literal_placeholder else text)
        else:
            out.append(" __ID__ " if ident_placeholder else f"[{text}]")
    return "".join(out)


def _tokens(code_with_idents):
    """Word / [ident] / punctuation tokens from code whose literals are
    already placeholders. Brackets are preserved so identifiers stay intact."""
    return re.findall(r"\[[^\]]*\]|__LIT\d+__|[A-Za-z_#@][\w#@$]*|\d+(?:\.\d+)?|\.|,|\(|\)|;|\S", code_with_idents)


def _unbracket(tok):
    return tok[1:-1] if tok.startswith("[") and tok.endswith("]") else tok


def _is_ident(tok):
    return bool(tok) and (tok.startswith("[") or re.match(r"^[A-Za-z_#][\w#$]*$", tok) is not None)


# ------------------------------------------------------- table extraction
def _cte_names(code):
    names = set()
    for m in re.finditer(r"(?:\bWITH\b|,)\s*(\[[^\]]+\]|[A-Za-z_]\w*)\s*(?:\([^()]*\))?\s*\bAS\s*\(",
                         code, re.IGNORECASE):
        names.add(_unbracket(m.group(1)).lower())
    return names


def _read_object_name(tokens, i):
    """Reads ident(.ident)* starting at tokens[i]; empty parts allowed (db..table).
    Returns (parts, next_index) or (None, i) if tokens[i] isn't an identifier."""
    if i >= len(tokens) or not _is_ident(tokens[i]) or tokens[i].upper() in _CLAUSE_END:
        return None, i
    parts = [_unbracket(tokens[i])]
    i += 1
    while i < len(tokens) and tokens[i] == ".":
        i += 1
        if i < len(tokens) and _is_ident(tokens[i]):
            parts.append(_unbracket(tokens[i]))
            i += 1
        else:
            parts.append("")
    return parts, i


def _skip_alias_and_hints(tokens, i):
    if i < len(tokens) and tokens[i].upper() == "AS":
        i += 1
        if i < len(tokens) and _is_ident(tokens[i]):
            i += 1
    elif i < len(tokens) and _is_ident(tokens[i]) and tokens[i].upper() not in _NOT_ALIAS:
        i += 1
    if i + 1 < len(tokens) and tokens[i].upper() == "WITH" and tokens[i + 1] == "(":
        depth, i = 0, i + 1
        while i < len(tokens):
            if tokens[i] == "(":
                depth += 1
            elif tokens[i] == ")":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            i += 1
    return i


def extract_table_references(code_with_idents):
    """[(parts, raw)] for every object read via FROM / JOIN / APPLY, including
    comma-separated FROM lists. Subqueries/derived tables and OPENQUERY are
    skipped here (OPENQUERY is validated separately)."""
    tokens = _tokens(code_with_idents)
    refs = []
    i = 0
    while i < len(tokens):
        up = tokens[i].upper()
        if up in ("FROM", "JOIN", "APPLY"):
            i += 1
            while True:
                if i < len(tokens) and tokens[i] == "(":
                    break  # derived table / function call — contents are scanned on their own
                if i < len(tokens) and tokens[i].upper() == "OPENQUERY":
                    break
                parts, j = _read_object_name(tokens, i)
                if parts is None:
                    break
                if j < len(tokens) and tokens[j] == "(":
                    break  # table-valued function call, e.g. FROM dbo.fn(...)
                refs.append(parts)
                i = _skip_alias_and_hints(tokens, j)
                if up == "FROM" and i < len(tokens) and tokens[i] == ",":
                    i += 1
                    continue
                break
            continue
        i += 1
    return refs


def normalize_table(parts, default_db):
    """-> (db, schema, table) lowercase. Missing schema => dbo; missing db =>
    the workspace's primary database."""
    parts = [p.strip().lower() for p in parts]
    if len(parts) == 1:
        return (default_db, "dbo", parts[0])
    if len(parts) == 2:
        return (default_db, parts[0] or "dbo", parts[1])
    if len(parts) == 3:
        return (parts[0] or default_db, parts[1] or "dbo", parts[2])
    raise SqlPolicyError(
        f"4-part name {'.'.join(parts)!r} is not allowed — reach a linked server only through OPENQUERY"
    )


def normalize_allowlist(entries, default_db):
    out = set()
    for entry in entries or []:
        text = str(entry or "").strip()
        if not text:
            continue
        pieces = [p.strip().strip("[]") for p in text.split(".")]
        out.add(normalize_table(pieces, default_db))
    return out


# -------------------------------------------------------------- the policy
def validate_select_sql(sql, allowed_tables, scope=None, require_window_tokens=True, _depth=0):
    """
    Validates `sql` against the read-only policy.

    allowed_tables: iterable of "table", "schema.table" or "db.schema.table".
    scope: object/dict with primary_db_name, secondary_db_name, same_instance,
           secondary_db_alias (the workspace's configured databases).
    Returns PolicyResult. Never raises for a policy violation.
    """
    errors = []
    if not isinstance(sql, str) or not sql.strip():
        return PolicyResult(False, ["SQL is empty"])
    if len(sql) > MAX_SQL_LENGTH:
        return PolicyResult(False, [f"SQL is longer than {MAX_SQL_LENGTH} characters"])

    scope_ns = _scope_namespace(scope)
    default_db = (scope_ns.primary_db_name or "").lower()

    try:
        segments = _lex(sql)
    except SqlPolicyError as exc:
        return PolicyResult(False, [str(exc)])

    code = _render(segments, literal_placeholder=True, ident_placeholder=False)
    code_kw = _render(segments, literal_placeholder=True, ident_placeholder=True)

    # 1. single statement
    body = code_kw.strip().lstrip(";").strip().rstrip(";").strip()
    if ";" in body:
        errors.append("only a single statement is allowed")

    # 2. must start with SELECT / WITH
    first = re.match(r"^\(*\s*([A-Za-z]+)", body)
    if not first or first.group(1).upper() not in ("SELECT", "WITH"):
        errors.append("the query must start with SELECT or WITH")

    # 3. forbidden keywords / procedures / variables
    bad = sorted({m.group(1).upper() for m in _FORBIDDEN_RE.finditer(code_kw)})
    if bad:
        errors.append(f"forbidden keyword(s): {', '.join(bad)}")
    procs = sorted({m.group(0) for m in _PROC_PREFIX_RE.finditer(code_kw)})
    if procs:
        errors.append(f"system/extended procedure reference(s) not allowed: {', '.join(procs)}")
    variables = sorted({m.group(0) for m in _VARIABLE_RE.finditer(code_kw)})
    if variables:
        errors.append(f"variables are not allowed: {', '.join(variables)}")

    # 4. system objects
    if _SYSTEM_DB_RE.search(code) or _SYSTEM_SCHEMA_RE.search(code):
        errors.append("system databases and system objects (master/msdb/tempdb/sys/INFORMATION_SCHEMA) are not allowed")

    # 5. tables vs allowlist
    ctes = _cte_names(code)
    tables = []
    try:
        allow = normalize_allowlist(allowed_tables, default_db)
    except SqlPolicyError as exc:
        allow = set()
        errors.append(f"allowed_tables: {exc}")
    if not allow:
        errors.append("allowed_tables must list every table this query may read")
    for parts in extract_table_references(code):
        if len(parts) == 1 and parts[0].lower() in ctes:
            continue
        if parts[0].startswith("#"):
            errors.append(f"temporary table {parts[0]!r} is not allowed")
            continue
        try:
            norm = normalize_table(parts, default_db)
        except SqlPolicyError as exc:
            errors.append(str(exc))
            continue
        tables.append(".".join(norm))
        if allow and norm not in allow:
            errors.append(f"table {'.'.join(p for p in parts if p)!r} is not on this metric's allowed_tables list")

    # 6. OPENQUERY payloads, recursively
    oq_calls = list(re.finditer(r"\bOPENQUERY\s*\(", code, re.IGNORECASE))
    if oq_calls:
        literal_by_index = {idx: text for idx, (kind, text) in enumerate(segments) if kind == "literal"}
        matched = list(re.finditer(r"\bOPENQUERY\s*\(\s*(\[[^\]]+\]|[A-Za-z_]\w*)\s*,\s*__LIT(\d+)__\s*\)",
                                   code, re.IGNORECASE))
        if len(matched) != len(oq_calls):
            errors.append("every OPENQUERY call must be OPENQUERY(linked_server, 'literal query')")
        if _depth > 0:
            errors.append("nested OPENQUERY is not allowed")
        for m in matched:
            inner = literal_by_index.get(int(m.group(2)), "")
            inner_scope = SimpleNamespace(
                primary_db_name=scope_ns.secondary_db_name, secondary_db_name=None,
                same_instance=False, secondary_db_alias=None,
            )
            sub = validate_select_sql(inner, allowed_tables, inner_scope, require_window_tokens=False, _depth=_depth + 1)
            errors.extend(f"inside OPENQUERY: {e}" for e in sub.errors)
            tables.extend(sub.tables)

    # 7. reuse the existing workspace scope guards unchanged
    if _depth == 0:
        from ..base.base import VannaBase  # local import keeps this module light for callers
        ok_lit, why_lit = VannaBase.validate_openquery_literals(scope_ns, sql)
        if not ok_lit:
            errors.append(why_lit)
        ok_scope, why_scope = VannaBase.validate_db_scope(scope_ns, sql)
        if not ok_scope:
            errors.append(why_scope)

    # 8. time window tokens
    if require_window_tokens:
        for token in (WINDOW_START_TOKEN, WINDOW_END_TOKEN):
            if token not in code:
                errors.append(f"the query must filter on {token} (outside any string literal) so it is time-bounded")

    # de-duplicate errors, keep order
    seen, unique = set(), []
    for e in errors:
        if e not in seen:
            seen.add(e)
            unique.append(e)
    return PolicyResult(not unique, unique, sorted(set(tables)), sorted(ctes))


def bind_window_parameters(sql):
    """Replaces :window_start / :window_end (outside literals) with pyodbc '?'
    placeholders. Returns (sql_with_placeholders, ["window_start", ...]) — the
    order in which the caller must pass parameter values. Comments are dropped."""
    segments = _lex(sql)
    out, order = [], []
    token_re = re.compile(r":window_(start|end)\b")
    for kind, text in segments:
        if kind == "code":
            def _sub(m):
                order.append("window_" + m.group(1))
                return "?"
            out.append(token_re.sub(_sub, text))
        elif kind == "literal":
            out.append("'" + text.replace("'", "''") + "'")
        else:
            out.append("[" + text.replace("]", "]]") + "]")
    return "".join(out), order


def _scope_namespace(scope):
    if scope is None:
        scope = {}
    get = scope.get if isinstance(scope, dict) else (lambda k, d=None: getattr(scope, k, d))
    return SimpleNamespace(
        primary_db_name=get("primary_db_name") or None,
        secondary_db_name=get("secondary_db_name") or None,
        same_instance=bool(get("same_instance", False)),
        secondary_db_alias=get("secondary_db_alias") or None,
    )

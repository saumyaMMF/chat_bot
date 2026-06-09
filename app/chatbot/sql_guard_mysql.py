"""Gate C — SQL guard for the chatbot, MySQL dialect.

Mirrors app.chatbot.sql_guard but for the 10 tenant-scoped rhize_* MySQL
tables. The model is told NEVER to write a tenantid filter; this guard
AST-injects ``AND tenantid = <validated literal>`` at every leaf table
reference of an allow-listed rhize_* table.

The tenant id is validated against ``settings.valid_tenant_ids`` BEFORE
injection, so the integer can be safely inlined into the rewritten SQL.

Defense-in-depth: layered on top of (a) the read-only ``chatbot_ro`` MySQL
user (SELECT grants on the 10 tables only) and (b) per-query READ ONLY
transaction in readonly_db_mysql.run_readonly_mysql.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.config import get_settings


ALLOWED_MYSQL_TABLES: frozenset[str] = frozenset({
    "rhize_dataset_main",
    "rhize_dataset_store",
    "rhize_brands",
    "rhize_partner_stores",
    "rhize_orders",
    "rhize_live_inventory",
    "rhize_product_lots",
    "rhize_stores",
    "rhize_strain_info",
    "rhize_sales_actions",
})

DEFAULT_ROW_LIMIT = 500

_DANGEROUS_FN = re.compile(
    r"\b("
    + "|".join([
        "load_file", "sleep", "benchmark", "get_lock", "release_lock",
        "sys_exec", "sys_eval", "uuid_short", "version", "user",
        "current_user", "session_user", "database", "schema", "connection_id",
        "found_rows", "last_insert_id", "row_count",
    ])
    + r")\s*\(",
    re.IGNORECASE,
)

# REPLACE is overloaded in MySQL: REPLACE INTO ... is DML (forbidden);
# REPLACE(str, from, to) is a string function (allowed). Same shape for
# any keyword that could also be a built-in function. The negative
# lookahead `(?!\s*\()` keeps the function form passing while still
# blocking the statement form. Other DML keywords (insert/update/delete)
# are NEVER functions, so they stay unconditional.
_FORBIDDEN_KEYWORD = re.compile(
    r"\b("
    + "|".join([
        "insert", "update", "delete", "drop", "alter", "truncate",
        "create", "grant", "revoke", "merge", "do", "reset",
        "use", "load", "lock", "unlock", "handler", "rename", "optimize",
        "repair", "check", "flush", "kill", "shutdown", "prepare",
        "deallocate",
    ])
    + r")\b"
    + r"|\b(replace|call|set|analyze|execute)\b(?!\s*\()",
    re.IGNORECASE,
)

# MySQL exfil / data-export constructs. Reject anywhere in the (string-stripped)
# SQL. UNION is rejected — cross-tenant exfil vector since the guard only
# injects tenantid per-SELECT, not across UNION arms.
_MYSQL_EXFIL = re.compile(
    "|".join([
        r"\binto\s+outfile\b",
        r"\binto\s+dumpfile\b",
        r"\binto\s+@",
        r"\bload_file\s*\(",
        r"\bunion\b",
        r"\binformation_schema\b",
        r"\bperformance_schema\b",
        r"\bmysql\.\w+",
        r"\bsys\.\w+",
    ]),
    re.IGNORECASE,
)

_COMMENT_RX = re.compile(r"--|/\*|\*/|(?:^|\s)#")
_READONLY_PREFIX = re.compile(r"^\s*\(*\s*(select|with)\b", re.IGNORECASE)
_LIMIT_RX = re.compile(r"\blimit\b\s+\d+", re.IGNORECASE)
# MySQL string literals may use '' OR \' to escape an inner quote.
_STRING_LITERAL_RX = re.compile(r"'(?:\\.|''|[^'\\])*'")
_BACKTICK_IDENT_RX = re.compile(r"`[^`]*`")


@dataclass(frozen=True)
class GuardResult:
    ok: bool
    sql: str = ""
    reason: str = ""


def _strip_string_literals(sql: str) -> str:
    return _STRING_LITERAL_RX.sub("''", sql)


def _strip_backtick_idents(sql: str) -> str:
    return _BACKTICK_IDENT_RX.sub("``", sql)


def _cte_names(tree: exp.Expression) -> set[str]:
    names: set[str] = set()
    for cte in tree.find_all(exp.CTE):
        alias = cte.alias_or_name
        if alias:
            names.add(alias.lower())
    return names


def _iter_table_refs(tree: exp.Expression) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for tbl in tree.find_all(exp.Table):
        name = (tbl.name or "").lower()
        schema = (tbl.db or "").lower()
        if name:
            out.append((schema, name))
    return out


def _tenant_predicate(alias_or_table: str, tenant_id: int) -> exp.Expression:
    """Build ``<alias>.tenantid = <literal>`` AST node."""
    col = exp.Column(
        this=exp.to_identifier("tenantid"),
        table=exp.to_identifier(alias_or_table) if alias_or_table else None,
    )
    return exp.EQ(this=col, expression=exp.Literal.number(tenant_id))


def _inject_tenant_predicates(tree: exp.Expression, tenant_id: int) -> None:
    """For each SELECT in the tree, AND ``<alias>.tenantid = <tenant_id>`` onto
    its WHERE for every allow-listed rhize_* table in its FROM/JOIN list.

    CTE names are treated as aliases and skipped (their bodies are visited
    independently when sqlglot walks into them).
    """
    cte_names = _cte_names(tree)

    for select in tree.find_all(exp.Select):
        additions: list[exp.Expression] = []

        # Gather every Table whose NEAREST enclosing Select is THIS one. Tables
        # inside subqueries belong to their own Select and will be visited when
        # the outer loop reaches them.
        for tbl in select.find_all(exp.Table):
            if _nearest_select(tbl) is not select:
                continue
            name = (tbl.name or "").lower()
            if not name or name in cte_names:
                continue
            if name not in ALLOWED_MYSQL_TABLES:
                continue
            alias = tbl.alias_or_name  # alias if present, else table name
            additions.append(_tenant_predicate(alias, tenant_id))

        if not additions:
            continue

        existing_where = select.args.get("where")
        new_where = existing_where.this if existing_where is not None else None
        for pred in additions:
            new_where = pred if new_where is None else exp.And(this=new_where, expression=pred)
        select.set("where", exp.Where(this=new_where))


def _nearest_select(node: exp.Expression) -> exp.Select | None:
    """Walk parents until we hit a Select; that's the scope this node belongs
    to. Returns None if there is no enclosing Select."""
    cur = node.parent
    while cur is not None:
        if isinstance(cur, exp.Select):
            return cur
        cur = cur.parent
    return None


def validate_mysql_sql(raw_sql: str, tenant_id: int) -> GuardResult:
    """Validate + rewrite a single model-generated MySQL SELECT.

    Returns ``GuardResult(ok=True, sql=<rewritten>)`` on success — the
    rewritten SQL has tenantid predicates injected and is what should be sent
    to the read-only MySQL pool.
    """
    if not isinstance(raw_sql, str) or raw_sql.strip() == "":
        return GuardResult(ok=False, reason="Empty SQL.")

    settings = get_settings()
    if not isinstance(tenant_id, int) or tenant_id not in settings.valid_tenant_ids:
        return GuardResult(ok=False, reason="Invalid tenant context.")

    sql = raw_sql.strip()
    if sql.endswith(";"):
        sql = sql[:-1].strip()

    if _COMMENT_RX.search(sql):
        return GuardResult(ok=False, reason="SQL comments are not allowed.")

    no_strings = _strip_string_literals(sql)
    if ";" in no_strings:
        return GuardResult(ok=False, reason="Only a single statement is allowed.")

    no_idents = _strip_backtick_idents(no_strings)

    exfil = _MYSQL_EXFIL.search(no_idents)
    if exfil:
        return GuardResult(ok=False, reason=f"Disallowed construct: {exfil.group(0)}.")

    danger = _DANGEROUS_FN.search(no_idents)
    if danger:
        return GuardResult(ok=False, reason=f"Disallowed function: {danger.group(1)}.")

    try:
        parsed = sqlglot.parse(sql, read="mysql")
    except ParseError as err:
        return GuardResult(ok=False, reason=f"Could not parse SQL: {err}")

    parsed = [p for p in parsed if p is not None]
    if len(parsed) != 1:
        return GuardResult(ok=False, reason="Only a single statement is allowed.")

    tree = parsed[0]
    if not isinstance(tree, (exp.Select, exp.Subquery, exp.Union)):
        return GuardResult(
            ok=False,
            reason=f"Only SELECT statements are allowed (got {type(tree).__name__}).",
        )

    kw = _FORBIDDEN_KEYWORD.search(no_idents)
    if kw:
        return GuardResult(ok=False, reason=f"Disallowed keyword: {kw.group(1).upper()}.")

    # Allow-list table check (schema-qualified system catalogs already caught by
    # _MYSQL_EXFIL but double-check here for any reference the regex missed).
    cte_names = _cte_names(tree)
    for schema, table in _iter_table_refs(tree):
        if table in cte_names:
            continue
        if schema in ("information_schema", "mysql", "sys", "performance_schema"):
            label = f"{schema}.{table}"
            return GuardResult(ok=False, reason=f"Access to system catalog is not allowed: {label}.")
        if table not in ALLOWED_MYSQL_TABLES:
            return GuardResult(ok=False, reason=f"Table not allowed: {table}.")

    _inject_tenant_predicates(tree, tenant_id)

    try:
        rewritten = tree.sql(dialect="mysql")
    except Exception as err:  # pragma: no cover — sqlglot generation rarely fails
        return GuardResult(
            ok=False,
            reason=f"Could not regenerate SQL after tenant injection: {err}",
        )

    return GuardResult(ok=True, sql=rewritten)


def assert_read_only_mysql(raw_sql: str) -> None:
    """Independent, last-line write-block for MySQL. Mirrors
    sql_guard.assert_read_only — called immediately before send so even if
    validate_mysql_sql is bypassed (caller error), anything not a SELECT is
    refused.
    """
    if not isinstance(raw_sql, str) or raw_sql.strip() == "":
        raise ValueError("assert_read_only_mysql: empty SQL blocked.")

    sql = raw_sql.strip()
    if sql.endswith(";"):
        sql = sql[:-1].strip()

    if _COMMENT_RX.search(sql):
        # Allow ONLY our server-injected MAX_EXECUTION_TIME optimizer hint —
        # injected by readonly_db_mysql AFTER this guard runs, so by the time
        # this fires the hint isn't present yet. Block all comments.
        raise ValueError("assert_read_only_mysql: comments blocked.")

    stripped = _strip_backtick_idents(_strip_string_literals(sql))

    if ";" in stripped:
        raise ValueError("assert_read_only_mysql: statement stacking blocked.")

    if not _READONLY_PREFIX.search(stripped):
        raise ValueError("assert_read_only_mysql: only SELECT/WITH queries may execute.")

    exfil = _MYSQL_EXFIL.search(stripped)
    if exfil:
        raise ValueError(f"assert_read_only_mysql: disallowed construct: {exfil.group(0)}.")
    kw = _FORBIDDEN_KEYWORD.search(stripped)
    if kw:
        raise ValueError(f"assert_read_only_mysql: write/DDL keyword blocked: {kw.group(1).upper()}.")
    danger = _DANGEROUS_FN.search(stripped)
    if danger:
        raise ValueError(f"assert_read_only_mysql: disallowed function blocked: {danger.group(1)}.")


def enforce_limit_mysql(sql: str, max_rows: int = DEFAULT_ROW_LIMIT) -> str:
    """Gate D — append ``LIMIT <max_rows>`` if the statement has no LIMIT.
    Existing limits are left untouched."""
    trimmed = sql.strip().rstrip(";").rstrip()
    if _LIMIT_RX.search(trimmed):
        return trimmed
    return f"{trimmed} LIMIT {max_rows}"

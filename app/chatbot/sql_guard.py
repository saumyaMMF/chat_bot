"""Gate C — SQL guard for the NL->SQL chatbot.

Validates a single model-generated statement BEFORE it is ever sent to the
read-only Postgres pool. Defense-in-depth: the real isolation walls are Gate A
(read-only chatbot_ro role) and Gate B (Row-Level Security). This guard exists
so that obviously-hostile or malformed SQL never reaches the database at all.

A statement passes ONLY if ALL of the following hold:
  1. No SQL comments (-- # /* */).
  2. Exactly one statement (no `;` stacking, no trailing junk).
  3. Parses as SELECT (or `WITH ... SELECT`).
  4. Every referenced table is in the allow-list.
  5. No DDL/DML/session keywords or dangerous functions appear.

`validate_sql` is pure — no I/O, no DB.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError


ALLOWED_TABLES: frozenset[str] = frozenset({
    "complete_market_scrapper_dataset",
    "chatbot_mv_market_daily",
})

DEFAULT_ROW_LIMIT = 500

_DANGEROUS_FN = re.compile(
    r"\b("
    + "|".join([
        "pg_sleep",
        "pg_read_file",
        "pg_read_binary_file",
        "pg_ls_dir",
        "pg_stat_file",
        "lo_import",
        "lo_export",
        "dblink",
        "dblink_exec",
        "pg_terminate_backend",
        "pg_cancel_backend",
        "pg_reload_conf",
        "query_to_xml",
        "set_config",
        "current_setting",
        "txid_current",
        "copy",
    ])
    + r")\b",
    re.IGNORECASE,
)

_FORBIDDEN_KEYWORD = re.compile(
    r"\b("
    + "|".join([
        "insert", "update", "delete", "drop", "alter", "truncate", "create",
        "grant", "revoke", "merge", "call", "do", "set", "reset", "vacuum",
        "analyze", "cluster", "reindex", "listen", "notify", "lock",
    ])
    + r")\b",
    re.IGNORECASE,
)

_COMMENT_RX = re.compile(r"--|/\*|\*/|(?:^|\s)#")
_READONLY_PREFIX = re.compile(r"^\s*\(*\s*(select|with)\b", re.IGNORECASE)
_STRING_LITERAL_RX = re.compile(r"'(?:''|[^'])*'")
_LIMIT_RX = re.compile(r"\blimit\b\s+\d+", re.IGNORECASE)


@dataclass(frozen=True)
class GuardResult:
    ok: bool
    sql: str = ""
    reason: str = ""


def _strip_string_literals(sql: str) -> str:
    """Replace single-quoted literals with '' so keyword scans don't trip on
    legitimate text inside a value."""
    return _STRING_LITERAL_RX.sub("''", sql)


def _cte_names(tree: exp.Expression) -> set[str]:
    names: set[str] = set()
    for cte in tree.find_all(exp.CTE):
        alias = cte.alias_or_name
        if alias:
            names.add(alias.lower())
    return names


def _iter_table_refs(tree: exp.Expression) -> Iterable[tuple[str, str]]:
    """Yield (schema, table) for every table reference. Schema may be ''."""
    for tbl in tree.find_all(exp.Table):
        name = (tbl.name or "").lower()
        schema = (tbl.db or "").lower()
        if name:
            yield schema, name


def validate_sql(raw_sql: str) -> GuardResult:
    """Validate a single model-generated SQL string.

    Returns ``GuardResult(ok=True, sql=...)`` on success or
    ``GuardResult(ok=False, reason=...)`` describing the first rule violated.
    """
    if not isinstance(raw_sql, str) or raw_sql.strip() == "":
        return GuardResult(ok=False, reason="Empty SQL.")

    sql = raw_sql.strip()
    if sql.endswith(";"):
        sql = sql[:-1].strip()

    if _COMMENT_RX.search(sql):
        return GuardResult(ok=False, reason="SQL comments are not allowed.")

    no_strings = _strip_string_literals(sql)
    if ";" in no_strings:
        return GuardResult(ok=False, reason="Only a single statement is allowed.")

    danger = _DANGEROUS_FN.search(no_strings)
    if danger:
        return GuardResult(ok=False, reason=f"Disallowed function: {danger.group(1)}.")

    try:
        parsed = sqlglot.parse(sql, read="postgres")
    except ParseError as err:
        return GuardResult(ok=False, reason=f"Could not parse SQL: {err}")

    parsed = [p for p in parsed if p is not None]
    if len(parsed) != 1:
        return GuardResult(ok=False, reason="Only a single statement is allowed.")

    tree = parsed[0]
    if not isinstance(tree, (exp.Select, exp.Subquery, exp.Union)):
        # `WITH ... SELECT` parses to a Select with a `with` arg in sqlglot.
        return GuardResult(
            ok=False,
            reason=f"Only SELECT statements are allowed (got {type(tree).__name__}).",
        )

    kw = _FORBIDDEN_KEYWORD.search(no_strings)
    if kw:
        return GuardResult(ok=False, reason=f"Disallowed keyword: {kw.group(1).upper()}.")

    ctes = _cte_names(tree)
    for schema, table in _iter_table_refs(tree):
        if table in ctes:
            continue
        if (
            schema == "information_schema"
            or schema.startswith("pg_")
            or table.startswith("pg_")
            or table.startswith("information_schema")
        ):
            label = f"{schema}.{table}" if schema else table
            return GuardResult(
                ok=False, reason=f"Access to system catalog is not allowed: {label}."
            )
        if table not in ALLOWED_TABLES:
            return GuardResult(ok=False, reason=f"Table not allowed: {table}.")

    return GuardResult(ok=True, sql=sql)


def assert_read_only(raw_sql: str) -> None:
    """Independent, last-line write-block. Called immediately before a statement
    is sent to Postgres — even if validate_sql was skipped or a caller hands raw
    SQL straight to runReadonly, any non-SELECT is refused.

    Raises ``ValueError`` on violation.
    """
    if not isinstance(raw_sql, str) or raw_sql.strip() == "":
        raise ValueError("assert_read_only: empty SQL blocked.")

    sql = raw_sql.strip()
    if sql.endswith(";"):
        sql = sql[:-1].strip()

    if _COMMENT_RX.search(sql):
        raise ValueError("assert_read_only: comments blocked.")

    stripped = _strip_string_literals(sql)

    if ";" in stripped:
        raise ValueError("assert_read_only: statement stacking blocked.")

    if not _READONLY_PREFIX.search(stripped):
        raise ValueError("assert_read_only: only SELECT/WITH queries may execute.")

    kw = _FORBIDDEN_KEYWORD.search(stripped)
    if kw:
        raise ValueError(f"assert_read_only: write/DDL keyword blocked: {kw.group(1).upper()}.")

    danger = _DANGEROUS_FN.search(stripped)
    if danger:
        raise ValueError(f"assert_read_only: disallowed function blocked: {danger.group(1)}.")


def enforce_limit(sql: str, max_rows: int = DEFAULT_ROW_LIMIT) -> str:
    """Gate D — ensure the statement has a row cap. Existing LIMIT is left
    untouched; otherwise append ``LIMIT <max_rows>``."""
    trimmed = sql.strip().rstrip(";").rstrip()
    if _LIMIT_RX.search(trimmed):
        return trimmed
    return f"{trimmed} LIMIT {max_rows}"

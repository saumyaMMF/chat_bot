"""Pre-DB column existence guard.

3B local models hallucinate column names. Catching that at the DB layer
costs a wasted round-trip (and the model often retries with the SAME
wrong name when only fed the cryptic 1054 / 42703 error). This module:

1. Builds a {table_name: {column_name, ...}} index from
   data/schema_definitions.json at import time. The file is auto-
   generated from llm_optimized_schema_spec.md so it stays in sync.
2. Walks a parsed SQL tree, collects every (table, column) reference
   we can resolve, and reports unknown ones.
3. The chat orchestrator turns a miss into a retry-feedback message
   that lists the table's REAL columns — much higher success on
   attempt 2 than the bare DB error.

Lower-case everything. Aliases resolved on a best-effort basis from
FROM/JOIN clauses. Bare-column references (no alias) are checked
against the union of in-scope tables; that's loose by design — we
only flag columns no in-scope table has.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from sqlglot import exp, parse_one

log = logging.getLogger(__name__)

_DATA = Path(__file__).resolve().parents[2] / "data" / "schema_definitions.json"


@lru_cache(maxsize=1)
def _table_columns() -> dict[str, set[str]]:
    """{table_lc: {col_lc, ...}}. Cached for process lifetime."""
    try:
        raw = json.loads(_DATA.read_text(encoding="utf-8"))
    except Exception as exc:
        log.warning("[column_check] schema_definitions.json unreadable: %s", exc)
        return {}
    out: dict[str, set[str]] = {}
    for item in raw.get("items") or []:
        if item.get("kind") != "column":
            continue
        t = (item.get("table_name") or "").lower()
        c = (item.get("column_name") or "").lower()
        if not t or not c:
            continue
        out.setdefault(t, set()).add(c)
    return out


@dataclass(frozen=True)
class ColumnCheckResult:
    ok: bool
    reason: str = ""
    suggestions: dict[str, list[str]] | None = None  # {bad_col: [hint_table.col, ...]}


def _from_tables(tree: exp.Expression) -> set[str]:
    """Lowercase table names referenced by FROM / JOIN. CTE aliases skipped —
    we only care about base-table columns."""
    cte_aliases = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE) if c.alias_or_name}
    out: set[str] = set()
    for t in tree.find_all(exp.Table):
        name = (t.name or "").lower()
        if not name or name in cte_aliases:
            continue
        out.add(name)
    return out


def validate_columns(sql: str) -> ColumnCheckResult:
    """Parse ``sql``, collect every column ref, flag any not present in the
    columns-by-table index for the in-scope tables.

    Returns ok=True when:
      - schema index empty (safe-pass — never break the pipeline)
      - SQL doesn't parse (let the existing sql_guard handle it)
      - every column resolves to at least one in-scope table

    Unknown columns are tabulated with hint suggestions pulled from any
    other table that DOES have a column with that name.
    """
    cols_by_table = _table_columns()
    if not cols_by_table:
        return ColumnCheckResult(ok=True)
    try:
        tree = parse_one(sql)
    except Exception:
        return ColumnCheckResult(ok=True)

    in_scope = _from_tables(tree) & cols_by_table.keys()
    if not in_scope:
        # No known base tables in FROM — could be CTE-only or unknown table.
        # The sql_guard already enforces ALLOWED_TABLES, so let it speak.
        return ColumnCheckResult(ok=True)

    allowed: set[str] = set()
    for t in in_scope:
        allowed |= cols_by_table[t]

    # Collect all SELECT-list aliases — `SUM(x) AS revenue` means later
    # references to `revenue` (e.g. ORDER BY revenue) are alias refs, NOT
    # real columns. The 3B model uses aliases heavily; without this skip
    # the guard rejects perfectly-valid SQL.
    aliases: set[str] = set()
    for a in tree.find_all(exp.Alias):
        alias_name = (a.alias or "").lower()
        if alias_name:
            aliases.add(alias_name)

    bad: dict[str, list[str]] = {}
    for col in tree.find_all(exp.Column):
        name = (col.name or "").lower()
        if not name or name == "*":
            continue
        if name in allowed or name in aliases:
            continue
        # Hint: any other table that DOES have this column.
        hints = [f"{t}.{name}" for t, cs in cols_by_table.items() if name in cs]
        bad[name] = sorted(hints)[:5]

    if not bad:
        return ColumnCheckResult(ok=True)

    reason_lines = []
    for c, hints in sorted(bad.items()):
        if hints:
            reason_lines.append(f"`{c}` does not exist on {sorted(in_scope)} (try: {', '.join(hints)})")
        else:
            reason_lines.append(f"`{c}` does not exist on any allowed table")
    reason = "Unknown column(s): " + "; ".join(reason_lines)
    return ColumnCheckResult(ok=False, reason=reason, suggestions=bad)


def real_columns_for(table: str) -> list[str]:
    """List the columns this checker knows about for a given table — used to
    build a precise retry-feedback message for the LLM."""
    return sorted(_table_columns().get(table.lower(), set()))

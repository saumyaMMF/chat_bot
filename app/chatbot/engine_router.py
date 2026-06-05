"""Engine router for the chatbot's two-database setup.

Decides which engine (PostgreSQL or MySQL) should run a model-generated SELECT
based on the table(s) it references. Runs BEFORE either dialect-specific
guard so we hand off to the right guard + executor pair.

Rules:
  - All tables referenced by a query must live on the SAME engine.
    Cross-engine queries are rejected (no federated query layer, and a likely
    exfil vector).
  - PG tables: chatbot_mv_market_daily, complete_market_scrapper_dataset.
  - MySQL tables: the 10 rhize_* tenant-scoped tables in ALLOWED_MYSQL_TABLES.
  - Unknown tables → reject early (the dialect guard would reject anyway, but
    failing here returns a clearer error).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.chatbot.sql_guard import ALLOWED_TABLES as PG_TABLES
from app.chatbot.sql_guard_mysql import ALLOWED_MYSQL_TABLES


Engine = Literal["pg", "mysql"]


@dataclass
class RouteResult:
    ok: bool
    engine: Engine | None = None
    tables: list[str] = field(default_factory=list)
    reason: str = ""


_SYSTEM_SCHEMAS = {"information_schema", "mysql", "sys", "performance_schema"}


def _parse_either(sql: str) -> exp.Expression | None:
    """Try MySQL dialect first (stricter on backticked idents), fall back to
    Postgres. We only need a parse tree to enumerate tables; either dialect
    captures the same FROM/JOIN refs for ambiguous syntax."""
    for dialect in ("mysql", "postgres"):
        try:
            parsed = sqlglot.parse(sql, read=dialect)
            for p in parsed:
                if p is not None:
                    return p
        except ParseError:
            continue
    return None


def _cte_names(tree: exp.Expression) -> set[str]:
    names: set[str] = set()
    for cte in tree.find_all(exp.CTE):
        if cte.alias_or_name:
            names.add(cte.alias_or_name.lower())
    return names


def route_engine(sql: str) -> RouteResult:
    """Decide which engine handles ``sql``. Returns the engine + table list on
    success, or ``ok=False`` with a reason describing the rejection."""
    tree = _parse_either(sql)
    if tree is None:
        return RouteResult(ok=False, reason="Could not parse SQL to determine engine.")

    cte_names = _cte_names(tree)
    seen: list[tuple[str, Engine]] = []

    for tbl in tree.find_all(exp.Table):
        name = (tbl.name or "").lower()
        schema = (tbl.db or "").lower()
        if not name:
            continue
        if name in cte_names:
            continue

        if (
            schema in _SYSTEM_SCHEMAS
            or schema.startswith("pg_")
            or name.startswith("pg_")
            or name == "information_schema"
        ):
            label = f"{schema}.{name}" if schema else name
            return RouteResult(
                ok=False,
                reason=f"Access to system catalog is not allowed: {label}.",
            )

        if name in PG_TABLES:
            seen.append((name, "pg"))
        elif name in ALLOWED_MYSQL_TABLES:
            seen.append((name, "mysql"))
        else:
            return RouteResult(ok=False, reason=f"Table not allowed: {name}.")

    if not seen:
        return RouteResult(ok=False, reason="Query references no known tables.")

    engines = {e for _, e in seen}
    if len(engines) > 1:
        return RouteResult(
            ok=False,
            reason="Cross-engine joins are not allowed (mix of Postgres and MySQL tables).",
        )

    return RouteResult(
        ok=True,
        engine=next(iter(engines)),
        tables=[t for t, _ in seen],
    )

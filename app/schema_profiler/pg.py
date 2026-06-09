"""PostgreSQL deep profiler. Connects via DATABASE_URL_ADMIN to bypass RLS."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import asyncpg

from app.config import get_settings
from app.schema_profiler.analyzers import (
    classify_cardinality,
    classify_pattern,
    infer_kind,
)
from app.schema_profiler.models import ColumnProfile, TableProfile

log = logging.getLogger(__name__)

DISTINCT_LIST_THRESHOLD = 5_000
TOP_N = 50
SAMPLE_ROWS = 5


def _strip_sslmode(url: str) -> tuple[str, bool]:
    parts = urlsplit(url)
    ssl = False
    if parts.query:
        kept = []
        for kv in parts.query.split("&"):
            if kv.lower().startswith("sslmode="):
                ssl = kv.split("=", 1)[1].lower() in ("require", "verify-ca", "verify-full")
            else:
                kept.append(kv)
        url = urlunsplit(parts._replace(query="&".join(kept)))
    return url, ssl


async def _connect(statement_timeout_ms: int = 60_000) -> asyncpg.Connection:
    settings = get_settings()
    if not settings.database_url_admin:
        raise RuntimeError("DATABASE_URL_ADMIN is not set")
    url, ssl = _strip_sslmode(settings.database_url_admin)
    conn = await asyncpg.connect(dsn=url, ssl="require" if ssl else None, timeout=30)
    await conn.execute(f"SET statement_timeout = {statement_timeout_ms}")
    return conn


def _q(ident: str) -> str:
    return '"' + ident.replace('"', '""') + '"'


async def _list_tables(conn: asyncpg.Connection, schemas: list[str]) -> list[tuple[str, str, str]]:
    rows = await conn.fetch(
        """SELECT table_schema, table_name, table_type
             FROM information_schema.tables
            WHERE table_schema = ANY($1::text[])
              AND table_type IN ('BASE TABLE','VIEW')
         ORDER BY table_schema, table_name""",
        schemas,
    )
    return [(r["table_schema"], r["table_name"], r["table_type"]) for r in rows]


async def _columns_info(conn: asyncpg.Connection, schema: str, table: str) -> list[dict]:
    rows = await conn.fetch(
        """SELECT column_name, data_type, udt_name, is_nullable, column_default
             FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
         ORDER BY ordinal_position""",
        schema, table,
    )
    return [dict(r) for r in rows]


async def _pk_and_indexes(conn: asyncpg.Connection, schema: str, table: str) -> tuple[list[str], list[dict]]:
    pk = await conn.fetch(
        """SELECT a.attname AS col
             FROM pg_index i
             JOIN pg_class c ON c.oid = i.indrelid
             JOIN pg_namespace n ON n.oid = c.relnamespace
             JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY(i.indkey)
            WHERE i.indisprimary AND n.nspname = $1 AND c.relname = $2
         ORDER BY array_position(i.indkey, a.attnum)""",
        schema, table,
    )
    idx = await conn.fetch(
        """SELECT i.relname AS name, ix.indisunique AS unique,
                  array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum)) AS cols
             FROM pg_class t
             JOIN pg_namespace n ON n.oid = t.relnamespace
             JOIN pg_index ix ON ix.indrelid = t.oid
             JOIN pg_class i ON i.oid = ix.indexrelid
             JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            WHERE n.nspname = $1 AND t.relname = $2
         GROUP BY i.relname, ix.indisunique""",
        schema, table,
    )
    indexes = [{"name": r["name"], "unique": r["unique"], "columns": list(r["cols"])} for r in idx]
    return [r["col"] for r in pk], indexes


async def _row_count(conn: asyncpg.Connection, schema: str, table: str) -> int:
    n = await conn.fetchval(f'SELECT COUNT(*) FROM {_q(schema)}.{_q(table)}')
    return int(n or 0)


async def _profile_column(
    conn: asyncpg.Connection,
    schema: str,
    table: str,
    col_info: dict,
) -> ColumnProfile:
    col = col_info["column_name"]
    declared = col_info["data_type"]
    udt = col_info["udt_name"]
    nullable = col_info["is_nullable"] == "YES"
    full = f"{_q(schema)}.{_q(table)}"
    c = _q(col)
    castable = f"({c})::text"
    skip_minmax = (udt or "").lower() in ("vector", "jsonb", "json", "tsvector", "bytea")
    skip_topn = skip_minmax  # GROUP BY on vector/jsonb fails / is meaningless

    row = await conn.fetchrow(
        f"""SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE {c} IS NULL) AS nulls,
                   COUNT(DISTINCT {c}) AS distinct_n
              FROM {full}""",
    )
    total = int(row["total"] or 0)
    nulls = int(row["nulls"] or 0)
    distinct_n = int(row["distinct_n"] or 0)
    non_null = total - nulls
    null_pct = (nulls / total * 100) if total else 0.0
    distinct_pct = (distinct_n / non_null * 100) if non_null else 0.0

    min_v: Any = None
    max_v: Any = None
    min_len: int | None = None
    max_len: int | None = None
    avg_len: float | None = None
    try:
        select_minmax = "NULL AS mn, NULL AS mx," if skip_minmax else f"MIN({c}) AS mn, MAX({c}) AS mx,"
        mm = await conn.fetchrow(
            f"""SELECT {select_minmax}
                       MIN(length({castable})) AS lmn,
                       MAX(length({castable})) AS lmx,
                       AVG(length({castable})) AS lav
                  FROM {full}
                 WHERE {c} IS NOT NULL""",
        )
        if mm:
            min_v = mm["mn"]
            max_v = mm["mx"]
            min_len = int(mm["lmn"]) if mm["lmn"] is not None else None
            max_len = int(mm["lmx"]) if mm["lmx"] is not None else None
            avg_len = float(mm["lav"]) if mm["lav"] is not None else None
    except Exception as e:
        log.warning("[profiler] min/max failed for %s.%s.%s: %s", schema, table, col, e)

    top: list[tuple[Any, int]] = []
    if not skip_topn:
        try:
            tr = await conn.fetch(
                f"""SELECT {c} AS v, COUNT(*) AS n
                      FROM {full}
                     WHERE {c} IS NOT NULL
                  GROUP BY {c}
                  ORDER BY n DESC
                     LIMIT {TOP_N}""",
            )
            top = [(r["v"], int(r["n"])) for r in tr]
        except Exception as e:
            log.warning("[profiler] top-N failed for %s.%s.%s: %s", schema, table, col, e)

    distinct_values: list[Any] | None = None
    if not skip_topn and 0 < distinct_n <= DISTINCT_LIST_THRESHOLD:
        try:
            dv = await conn.fetch(
                f"""SELECT DISTINCT {c} AS v FROM {full}
                     WHERE {c} IS NOT NULL
                  ORDER BY {c}
                     LIMIT {DISTINCT_LIST_THRESHOLD}""",
            )
            distinct_values = [r["v"] for r in dv]
        except Exception as e:
            log.warning("[profiler] distinct list failed for %s.%s.%s: %s", schema, table, col, e)

    sample_vals = [v for v, _ in top[:20]] or (distinct_values or [])[:20]
    patterns = classify_pattern(sample_vals)
    kind = infer_kind(udt or declared, patterns)
    is_unique, is_low = classify_cardinality(distinct_n, non_null)

    return ColumnProfile(
        name=col,
        declared_type=f"{declared} ({udt})" if udt and udt != declared else declared,
        inferred_kind=kind,
        nullable=nullable,
        total_rows=total,
        null_count=nulls,
        null_pct=round(null_pct, 2),
        distinct_count=distinct_n,
        distinct_pct=round(distinct_pct, 2),
        is_unique=is_unique,
        is_low_cardinality=is_low,
        min_value=min_v,
        max_value=max_v,
        min_length=min_len,
        max_length=max_len,
        avg_length=round(avg_len, 2) if avg_len is not None else None,
        pattern_hints=patterns,
        distinct_values=distinct_values,
        top_values=top,
        sample_values=sample_vals[:10],
    )


async def _profile_table(conn: asyncpg.Connection, schema: str, table: str, kind: str) -> TableProfile:
    cols = await _columns_info(conn, schema, table)
    pk, idx = await _pk_and_indexes(conn, schema, table) if kind == "BASE TABLE" else ([], [])
    total = await _row_count(conn, schema, table)
    profiles: list[ColumnProfile] = []
    for ci in cols:
        log.info("[profiler] pg %s.%s.%s", schema, table, ci["column_name"])
        profiles.append(await _profile_column(conn, schema, table, ci))
    sample = await conn.fetch(f'SELECT * FROM {_q(schema)}.{_q(table)} LIMIT {SAMPLE_ROWS}')
    return TableProfile(
        engine="postgres",
        schema=schema,
        table=table,
        row_count=total,
        column_count=len(cols),
        primary_key=pk,
        indexes=idx,
        columns=profiles,
        sample_rows=[dict(r) for r in sample],
        notes=["view"] if kind == "VIEW" else [],
    )


async def profile_postgres(
    tables: list[str] | None = None,
    schemas: list[str] | None = None,
    include_views: bool = False,
    statement_timeout_ms: int = 60_000,
) -> list[TableProfile]:
    schemas = schemas or ["public"]
    conn = await _connect(statement_timeout_ms=statement_timeout_ms)
    try:
        listed = await _list_tables(conn, schemas)
        if tables:
            wanted = set(tables)
            listed = [t for t in listed if t[1] in wanted]
        if not include_views:
            listed = [t for t in listed if t[2] != "VIEW"]
        out: list[TableProfile] = []
        for s, t, k in listed:
            log.info("[profiler] pg start %s.%s (%s)", s, t, k)
            try:
                out.append(await _profile_table(conn, s, t, k))
            except Exception as e:
                log.error("[profiler] pg %s.%s failed: %s", s, t, e)
        return out
    finally:
        await conn.close()

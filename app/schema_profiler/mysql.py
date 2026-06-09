"""MySQL deep profiler. Connects via CHATBOT_MYSQL_RO_URL (chatbot_ro has
SELECT on every rhize_* table — full data, no tenant injection at this layer)."""

from __future__ import annotations

import asyncio
import logging
import ssl as ssl_module
import sys
from typing import Any
from urllib.parse import parse_qs, urlsplit

import aiomysql

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

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


def _dsn(url: str) -> dict[str, Any]:
    parts = urlsplit(url)
    host = parts.hostname or "127.0.0.1"
    cfg: dict[str, Any] = {
        "host": host,
        "port": parts.port or 3306,
        "user": parts.username or "",
        "password": parts.password or "",
        "db": (parts.path or "/").lstrip("/"),
    }
    qs = {k.lower(): [x.lower() for x in v] for k, v in parse_qs(parts.query).items()}
    ssl_on = any(
        v in ("true", "required", "require", "1", "yes")
        for k in ("ssl", "sslmode", "ssl-mode", "ssl_mode")
        for v in qs.get(k, [])
    )
    if not ssl_on and host not in ("localhost", "127.0.0.1"):
        ssl_on = True
    if ssl_on:
        ctx = ssl_module.create_default_context()
        import os
        if not os.environ.get("CHATBOT_MYSQL_SSL_STRICT"):
            ctx.check_hostname = False
            ctx.verify_mode = ssl_module.CERT_NONE
        cfg["ssl"] = ctx
    return cfg


async def _connect() -> aiomysql.Connection:
    settings = get_settings()
    if not settings.mysql_ro_url:
        raise RuntimeError("CHATBOT_MYSQL_RO_URL is not set")
    cfg = _dsn(settings.mysql_ro_url)
    return await aiomysql.connect(
        host=cfg["host"], port=cfg["port"], user=cfg["user"],
        password=cfg["password"], db=cfg["db"], ssl=cfg.get("ssl"),
        autocommit=True, connect_timeout=20,
    )


async def _fetch_all(conn: aiomysql.Connection, sql: str, params: tuple = ()) -> list[dict]:
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(sql, params)
        rows = await cur.fetchall()
    return [{k.lower(): v for k, v in r.items()} for r in rows]


async def _list_tables(conn: aiomysql.Connection, like: str = "rhize_%") -> list[str]:
    rows = await _fetch_all(conn, "SHOW TABLES LIKE %s", (like,))
    return [list(r.values())[0] for r in rows]


async def _columns_info(conn: aiomysql.Connection, table: str) -> list[dict]:
    return await _fetch_all(
        conn,
        """SELECT column_name, data_type, column_type, is_nullable, column_key,
                  column_default, extra
             FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = %s
         ORDER BY ordinal_position""",
        (table,),
    )


async def _indexes(conn: aiomysql.Connection, table: str) -> list[dict]:
    rows = await _fetch_all(
        conn,
        """SELECT index_name, column_name, non_unique, seq_in_index
             FROM information_schema.statistics
            WHERE table_schema = DATABASE() AND table_name = %s
         ORDER BY index_name, seq_in_index""",
        (table,),
    )
    grouped: dict[str, dict] = {}
    for r in rows:
        idx = r["index_name"]
        if idx not in grouped:
            grouped[idx] = {"name": idx, "unique": not r["non_unique"], "columns": []}
        grouped[idx]["columns"].append(r["column_name"])
    return list(grouped.values())


def _bt(name: str) -> str:
    return "`" + name.replace("`", "``") + "`"


async def _row_count(conn: aiomysql.Connection, table: str) -> int:
    rows = await _fetch_all(conn, f"SELECT COUNT(*) AS n FROM {_bt(table)}")
    return int(rows[0]["n"]) if rows else 0


async def _profile_column(
    conn: aiomysql.Connection,
    table: str,
    col_info: dict,
    total_rows: int,
) -> ColumnProfile:
    col = col_info["column_name"]
    declared = col_info["column_type"]
    nullable = col_info["is_nullable"] == "YES"
    t = _bt(table)
    c = _bt(col)

    base = await _fetch_all(
        conn,
        f"""SELECT COUNT(*) AS total,
                   SUM(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) AS nulls,
                   COUNT(DISTINCT {c}) AS distinct_n
              FROM {t}""",
    )
    row = base[0] if base else {}
    total = int(row.get("total") or 0)
    nulls = int(row.get("nulls") or 0)
    distinct_n = int(row.get("distinct_n") or 0)
    non_null = total - nulls
    null_pct = (nulls / total * 100) if total else 0.0
    distinct_pct = (distinct_n / non_null * 100) if non_null else 0.0

    min_v: Any = None
    max_v: Any = None
    min_len: int | None = None
    max_len: int | None = None
    avg_len: float | None = None
    try:
        mm = await _fetch_all(
            conn,
            f"""SELECT MIN({c}) AS mn, MAX({c}) AS mx,
                       MIN(CHAR_LENGTH(CAST({c} AS CHAR))) AS lmn,
                       MAX(CHAR_LENGTH(CAST({c} AS CHAR))) AS lmx,
                       AVG(CHAR_LENGTH(CAST({c} AS CHAR))) AS lav
                  FROM {t}
                 WHERE {c} IS NOT NULL""",
        )
        if mm:
            min_v = mm[0]["mn"]
            max_v = mm[0]["mx"]
            min_len = int(mm[0]["lmn"]) if mm[0]["lmn"] is not None else None
            max_len = int(mm[0]["lmx"]) if mm[0]["lmx"] is not None else None
            avg_len = float(mm[0]["lav"]) if mm[0]["lav"] is not None else None
    except Exception as e:
        log.warning("[profiler] min/max failed for %s.%s: %s", table, col, e)

    top: list[tuple[Any, int]] = []
    try:
        tr = await _fetch_all(
            conn,
            f"""SELECT {c} AS v, COUNT(*) AS n
                  FROM {t}
                 WHERE {c} IS NOT NULL
              GROUP BY {c}
              ORDER BY n DESC
                 LIMIT {TOP_N}""",
        )
        top = [(r["v"], int(r["n"])) for r in tr]
    except Exception as e:
        log.warning("[profiler] top-N failed for %s.%s: %s", table, col, e)

    distinct_values: list[Any] | None = None
    if 0 < distinct_n <= DISTINCT_LIST_THRESHOLD:
        try:
            dv = await _fetch_all(
                conn,
                f"""SELECT DISTINCT {c} AS v FROM {t}
                     WHERE {c} IS NOT NULL
                  ORDER BY {c}
                     LIMIT {DISTINCT_LIST_THRESHOLD}""",
            )
            distinct_values = [r["v"] for r in dv]
        except Exception as e:
            log.warning("[profiler] distinct list failed for %s.%s: %s", table, col, e)

    sample_vals = [v for v, _ in top[:20]] or (distinct_values or [])[:20]
    patterns = classify_pattern(sample_vals)
    kind = infer_kind(declared, patterns)
    is_unique, is_low = classify_cardinality(distinct_n, non_null)

    notes: list[str] = []
    if col_info["column_key"] == "PRI":
        notes.append("primary-key")
    elif col_info["column_key"] == "UNI":
        notes.append("unique-index")
    if col_info["column_key"] == "MUL":
        notes.append("indexed")
    if (col_info.get("extra") or "").lower().find("auto_increment") >= 0:
        notes.append("auto-increment")

    return ColumnProfile(
        name=col,
        declared_type=declared,
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
        notes=notes,
    )


async def _profile_table(conn: aiomysql.Connection, table: str) -> TableProfile:
    cols = await _columns_info(conn, table)
    idx = await _indexes(conn, table)
    total = await _row_count(conn, table)
    pk_cols: list[str] = []
    for i in idx:
        if i["name"] == "PRIMARY":
            pk_cols = i["columns"]
    profiles: list[ColumnProfile] = []
    for ci in cols:
        log.info("[profiler] mysql %s.%s", table, ci["column_name"])
        profiles.append(await _profile_column(conn, table, ci, total))
    sample = await _fetch_all(conn, f"SELECT * FROM {_bt(table)} LIMIT {SAMPLE_ROWS}")
    return TableProfile(
        engine="mysql",
        schema=None,
        table=table,
        row_count=total,
        column_count=len(cols),
        primary_key=pk_cols,
        indexes=idx,
        columns=profiles,
        sample_rows=sample,
    )


async def profile_mysql(
    tables: list[str] | None = None,
    statement_timeout_ms: int = 60_000,
) -> list[TableProfile]:
    conn = await _connect()
    try:
        try:
            async with conn.cursor() as cur:
                await cur.execute(f"SET SESSION MAX_EXECUTION_TIME = {statement_timeout_ms}")
        except Exception:
            pass
        if not tables:
            tables = await _list_tables(conn)
        out: list[TableProfile] = []
        for t in tables:
            log.info("[profiler] mysql start table=%s", t)
            try:
                out.append(await _profile_table(conn, t))
            except Exception as e:
                log.error("[profiler] mysql table=%s failed: %s", t, e)
        return out
    finally:
        conn.close()

"""Gate A + B + D execution layer, MySQL side.

Mirrors readonly_db.py (Postgres) for the 10 tenant-scoped rhize_* tables.

Walls:
  - Gate A — connects ONLY as ``chatbot_ro`` (SELECT-only grants on 10 tables,
    created via chatbot/sql/mysql-001_chatbot_ro_role.sql).
  - Gate B — tenantid predicate AST-injected upstream by
    sql_guard_mysql.validate_mysql_sql. MySQL has no RLS; the predicate IS the
    boundary. Tenant id is validated against settings.valid_tenant_ids before
    injection.
  - Gate D — MAX_EXECUTION_TIME optimizer hint caps per-statement runtime;
    LIMIT cap applied upstream by enforce_limit_mysql.

The pool uses CHATBOT_MYSQL_RO_URL (separate from the app's MYSQL_URL) so the
app's read-write pool is never reachable from this path.
"""

from __future__ import annotations

import asyncio
import logging
import re
import ssl as ssl_module
import sys
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlsplit

import aiomysql

# Windows + Python 3.12 + asyncio ProactorEventLoop + SSL = WinError 87
# during MySQL TLS handshake. The fix is a one-line policy swap that must
# happen BEFORE any event loop is created. Module-level so any entry point
# (uvicorn, eval harness, ad-hoc `python -c`) gets it.
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

from app.config import get_settings
from app.chatbot.sql_guard_mysql import assert_read_only_mysql


log = logging.getLogger(__name__)


_pool: aiomysql.Pool | None = None
_pool_lock = asyncio.Lock()


def _parse_dsn(url: str) -> dict[str, Any]:
    parts = urlsplit(url)
    host = parts.hostname or "127.0.0.1"
    cfg: dict[str, Any] = {
        "host": host,
        "port": parts.port or 3306,
        "user": parts.username or "",
        "password": parts.password or "",
        "db": (parts.path or "/").lstrip("/"),
    }
    # Honor ?ssl=true / ?sslmode=require / ?ssl-mode=required in the URL.
    # DigitalOcean managed MySQL requires TLS — without ssl= the connect call
    # fails with "Can't connect to MySQL server".
    qs = {k.lower(): [x.lower() for x in v] for k, v in parse_qs(parts.query).items()}
    ssl_on = any(
        v in ("true", "required", "require", "1", "yes")
        for k in ("ssl", "sslmode", "ssl-mode", "ssl_mode")
        for v in qs.get(k, [])
    )
    # Auto-enable TLS for non-localhost hosts even when the URL omits ?ssl —
    # almost every managed DB requires it; the only common no-TLS case is dev
    # against 127.0.0.1.
    if not ssl_on and host not in ("localhost", "127.0.0.1"):
        ssl_on = True
    if ssl_on:
        ctx = ssl_module.create_default_context()
        # DigitalOcean managed MySQL uses its own CA for the cluster cert.
        # Default ctx (CERT_REQUIRED + check_hostname) rejects unless the DO
        # CA is in the system store. As of the 2026-06-11 review, default is
        # STRICT (verify cert + hostname). To disable strict verification on
        # a dev box where the DO CA isn't installed, set CHATBOT_MYSQL_SSL_STRICT=0
        # (the TLS handshake will still encrypt traffic — only cert verification
        # is skipped).
        import os
        strict_env = os.environ.get("CHATBOT_MYSQL_SSL_STRICT", "1").strip()
        if strict_env in ("0", "false", "no"):
            ctx.check_hostname = False
            ctx.verify_mode = ssl_module.CERT_NONE
            log.warning(
                "MySQL TLS cert verification DISABLED (CHATBOT_MYSQL_SSL_STRICT=%s)",
                strict_env,
            )
        cfg["ssl"] = ctx
    return cfg


async def get_pool() -> aiomysql.Pool:
    global _pool
    if _pool is not None:
        return _pool
    async with _pool_lock:
        if _pool is not None:
            return _pool
        settings = get_settings()
        if not settings.mysql_ro_url:
            raise RuntimeError(
                "CHATBOT_MYSQL_RO_URL is not configured (chatbot MySQL read-only role)."
            )
        cfg = _parse_dsn(settings.mysql_ro_url)
        _pool = await aiomysql.create_pool(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            db=cfg["db"],
            ssl=cfg.get("ssl"),
            minsize=0,
            maxsize=5,
            autocommit=False,
            connect_timeout=20,
        )
        return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


@dataclass
class RunMysqlContext:
    timeout_ms: int | None = None


@dataclass
class RunMysqlResult:
    rows: list[dict[str, Any]]
    row_count: int


_SELECT_OR_WITH_HEAD = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)


def _inject_max_execution_hint(sql: str, ms: int) -> str:
    """Insert ``/*+ MAX_EXECUTION_TIME(ms) */`` right after the leading
    SELECT/WITH. If we can't find a safe insertion point, return the SQL
    unchanged (LIMIT + RO txn still apply).

    NOTE: this is the ONLY place we deliberately inject SQL comment syntax,
    and we do it AFTER the guard has already run. The guard rejects any
    user-supplied comment upstream.
    """
    m = _SELECT_OR_WITH_HEAD.search(sql)
    if not m:
        return sql
    idx = m.end()
    hint = f" /*+ MAX_EXECUTION_TIME({max(100, int(ms))}) */"
    return sql[:idx] + hint + sql[idx:]


async def run_readonly_mysql(sql: str, ctx: RunMysqlContext = RunMysqlContext()) -> RunMysqlResult:
    """Execute a guard-validated SELECT against the read-only MySQL pool.

    The SQL is assumed to have:
      - tenantid predicates AST-injected by validate_mysql_sql
      - LIMIT applied by enforce_limit_mysql

    Layered defenses applied here:
      - assert_read_only_mysql — last-line write block.
      - SET SESSION TRANSACTION READ ONLY + START TRANSACTION READ ONLY —
        engine-level write block.
      - MAX_EXECUTION_TIME hint — per-query runtime cap (MySQL 8.0+).
    """
    settings = get_settings()
    if not settings.mysql_ro_url:
        raise RuntimeError(
            "CHATBOT_MYSQL_RO_URL is not configured (chatbot MySQL read-only role)."
        )

    # Layer 2 — independent write-block on the SQL as guard returned it (no
    # hint yet).
    assert_read_only_mysql(sql)

    timeout_ms = ctx.timeout_ms or settings.statement_timeout_ms
    hinted_sql = _inject_max_execution_hint(sql, timeout_ms)

    pool = await get_pool()
    conn: aiomysql.Connection = await pool.acquire()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SET SESSION TRANSACTION READ ONLY")
            await cur.execute("START TRANSACTION READ ONLY")
            try:
                await cur.execute(hinted_sql)
                raw_rows = await cur.fetchall() or []
                # aiomysql DictCursor returns list[dict] but DECIMAL columns
                # come back as decimal.Decimal — FastAPI's JSON encoder turns
                # those into strings, breaking the frontend's numeric detection
                # and chart axes. Coerce to float here; precision loss for
                # money/qty at this app's scale is irrelevant (< 1e15).
                from decimal import Decimal as _Decimal
                clean: list[dict] = []
                for r in raw_rows:
                    out: dict = {}
                    for k, v in r.items():
                        out[k] = float(v) if isinstance(v, _Decimal) else v
                    clean.append(out)
                return RunMysqlResult(rows=clean, row_count=len(clean))
            finally:
                try:
                    await cur.execute("ROLLBACK")
                except Exception:  # connection may already be aborted
                    pass
    finally:
        pool.release(conn)

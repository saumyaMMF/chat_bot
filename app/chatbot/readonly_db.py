"""Gate A + B + D execution layer.

Runs already-validated (Gate C) SELECTs through a connection that:
  - authenticates as the read-only `chatbot_ro` role (Gate A, via DATABASE_URL_RO),
  - sets app.tenant_id / app.states per request so RLS filters every row (Gate B),
  - caps statement time (Gate D),
  - runs inside a READ ONLY transaction that is always rolled back.

The tenant/state values come ONLY from the caller (server-side, from auth) —
never from the model. set_config(..., is_local => true) scopes them to the
transaction and is parameterized, so they cannot be injected.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import asyncpg

from app.config import get_settings
from app.chatbot.sql_guard import assert_read_only


def _strip_sslmode(url: str) -> str:
    """asyncpg uses its own ssl kwarg; sslmode= in the URL is ignored or noisy."""
    try:
        parts = urlsplit(url)
        if not parts.query:
            return url
        kept = [
            kv for kv in parts.query.split("&")
            if not kv.lower().startswith("sslmode=")
        ]
        return urlunsplit(parts._replace(query="&".join(kept)))
    except Exception:
        return url


_pool: asyncpg.Pool | None = None
_pool_lock = asyncio.Lock()


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is not None:
        return _pool
    async with _pool_lock:
        if _pool is not None:
            return _pool
        settings = get_settings()
        if not settings.database_url_ro:
            raise RuntimeError("DATABASE_URL_RO is not configured (chatbot read-only role).")
        url = _strip_sslmode(settings.database_url_ro)
        is_local = "localhost" in url or "127.0.0.1" in url
        _pool = await asyncpg.create_pool(
            dsn=url,
            min_size=0,
            max_size=5,
            command_timeout=30,
            ssl=None if is_local else "require",
        )
        return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


@dataclass
class RunContext:
    tenant_id: int
    states: list[str]
    timeout_ms: int | None = None


@dataclass
class RunResult:
    rows: list[dict[str, Any]]
    row_count: int


async def run_readonly(sql: str, ctx: RunContext) -> RunResult:
    """Execute a validated SELECT under tenant/state RLS. Raises on DB error so
    the caller can feed the message back to the model for a retry."""
    settings = get_settings()
    if not settings.database_url_ro:
        raise RuntimeError("DATABASE_URL_RO is not configured (chatbot read-only role).")
    if not isinstance(ctx.tenant_id, int):
        raise ValueError("run_readonly: tenant_id must be an integer")

    # Layer 2 — independent write-block. Throws on anything but a single SELECT,
    # even if validate_sql (Gate C) was skipped upstream. Runs before any DB call.
    assert_read_only(sql)

    timeout_ms = ctx.timeout_ms or settings.statement_timeout_ms
    pool = await get_pool()

    async with pool.acquire() as conn:
        tx = conn.transaction(readonly=True)
        await tx.start()
        try:
            # Gate B — parameterized + transaction-local RLS scope.
            await conn.execute(
                "SELECT set_config($1, $2, true)",
                "app.tenant_id",
                str(ctx.tenant_id),
            )
            await conn.execute(
                "SELECT set_config($1, $2, true)",
                "app.states",
                ",".join(ctx.states),
            )
            # Gate D — bound runtime.
            await conn.execute(
                "SELECT set_config($1, $2, true)",
                "statement_timeout",
                str(timeout_ms),
            )

            records = await conn.fetch(sql)
            rows = [dict(r) for r in records]
            return RunResult(rows=rows, row_count=len(rows))
        finally:
            # Read-only path — always discard.
            try:
                await tx.rollback()
            except Exception:
                pass

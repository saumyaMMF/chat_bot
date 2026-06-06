"""In-process perf primitives for the chat hot path.

1. ``TTLCache`` — async-safe LRU with per-entry TTL. Backs ``embed_text``
   caching so repeated questions skip the Ollama embedding call (~500ms).

2. ``VectorSnapshot`` — base class for in-memory KNN over the small reference
   corpora (schema/examples/fast_path, each <500 rows). Loads the full table
   once into Python lists with precomputed norms, refreshes when the table's
   ``MAX(updated_at)`` advances (poll interval = ``staleness_check_secs``).
   Cosine distance computed in pure Python — pgvector HNSW round-trip
   (~10-30ms) and embedding payload transit dropped entirely. Saves ~1-2s per
   chat turn.

   Subclasses provide ``_load_rows()`` (the DB SELECT) and ``_row_to_payload()``
   (asyncpg.Record → caller-friendly dataclass). Generic ``knn()`` returns
   ``[(payload, distance), ...]`` sorted ascending.

Both primitives intentionally avoid numpy — corpora are too small to justify a
new heavyweight dep, and a pure-Python dot-product over 500×768 floats is
sub-millisecond.
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Generic, TypeVar

from app.chatbot.readonly_db import get_pool

log = logging.getLogger(__name__)

T = TypeVar("T")


# ── TTL LRU ────────────────────────────────────────────────────────────────


class TTLCache(Generic[T]):
    """Async-safe LRU with per-entry TTL. Pure asyncio.Lock — no extra deps.

    Eviction priority: expired first, then least-recently-inserted. Reads do
    not bump recency (intentional — keeps eviction predictable for an
    embedding cache where read-skew is not a concern).
    """

    def __init__(self, *, maxsize: int = 1024, ttl_secs: float = 300.0) -> None:
        self._max = maxsize
        self._ttl = ttl_secs
        self._d: OrderedDict[str, tuple[float, T]] = OrderedDict()
        self._lock = asyncio.Lock()
        self.hits = 0
        self.misses = 0

    async def get_or_set(self, key: str, factory: Callable[[], Awaitable[T]]) -> T:
        now = time.monotonic()
        async with self._lock:
            hit = self._d.get(key)
            if hit and (now - hit[0]) < self._ttl:
                self.hits += 1
                return hit[1]
            if hit:
                # expired — fall through to recompute
                del self._d[key]

        # Compute outside the lock so concurrent unrelated keys are not blocked.
        # Trade-off: thundering-herd on a popular cold key. Acceptable for
        # embeddings (idempotent, cheap to redo) and KNN.
        value = await factory()

        async with self._lock:
            self._d[key] = (time.monotonic(), value)
            self._d.move_to_end(key)
            while len(self._d) > self._max:
                self._d.popitem(last=False)
            self.misses += 1
        return value

    def invalidate_all(self) -> None:
        self._d.clear()

    def stats(self) -> dict[str, int]:
        return {"size": len(self._d), "hits": self.hits, "misses": self.misses}


# ── In-memory KNN snapshot ─────────────────────────────────────────────────


@dataclass
class _VecRow:
    embedding: list[float]
    norm: float
    payload: Any = field(repr=False)


class VectorSnapshot:
    """Holds the full embedding table in memory; serves cosine-distance KNN.

    Refresh policy: lazy. Every ``knn()`` call peeks at the table's
    ``MAX(updated_at)`` if more than ``staleness_check_secs`` have passed
    since the last peek. If the watermark advanced, reload all rows. This
    keeps the snapshot fresh after ingest scripts without polling overhead
    on every request.
    """

    def __init__(
        self,
        *,
        table_name: str,
        select_sql: str,
        staleness_check_secs: float = 60.0,
        watermark_column: str = "updated_at",
    ) -> None:
        self.table_name = table_name
        self._select_sql = select_sql
        self._staleness_check = staleness_check_secs
        self._watermark_column = watermark_column
        self._rows: list[_VecRow] = []
        self._loaded_at_watermark: str | None = None
        self._last_peek: float = 0.0
        self._lock = asyncio.Lock()

    # Subclasses override.
    def _row_to_payload(self, raw: Any) -> Any:
        raise NotImplementedError

    async def _maybe_refresh(self) -> None:
        now = time.monotonic()
        if self._rows and (now - self._last_peek) < self._staleness_check:
            return
        async with self._lock:
            # Re-check inside lock to coalesce concurrent peeks.
            now = time.monotonic()
            if self._rows and (now - self._last_peek) < self._staleness_check:
                return
            self._last_peek = now

            pool = await get_pool()
            async with pool.acquire() as conn:
                wm_row = await conn.fetchrow(
                    f"SELECT MAX({self._watermark_column})::text AS wm "
                    f"FROM {self.table_name}"
                )
                wm = (wm_row or {}).get("wm") if wm_row else None
                if self._rows and wm == self._loaded_at_watermark:
                    return  # nothing new

                rows = await conn.fetch(self._select_sql)
                new_rows: list[_VecRow] = []
                for r in rows:
                    emb = r["embedding"]
                    # pgvector returns either str literal "[1,2,3]" or list.
                    if isinstance(emb, str):
                        emb = [float(x) for x in emb.strip("[]").split(",") if x]
                    norm = math.sqrt(sum(x * x for x in emb)) or 1.0
                    new_rows.append(
                        _VecRow(
                            embedding=list(emb),
                            norm=norm,
                            payload=self._row_to_payload(r),
                        )
                    )
                self._rows = new_rows
                self._loaded_at_watermark = wm
                log.info(
                    "[perf] %s snapshot reloaded: %d rows (watermark=%s)",
                    self.table_name, len(new_rows), wm,
                )

    @staticmethod
    def _cosine_distance(a: list[float], a_norm: float,
                         b: list[float], b_norm: float) -> float:
        # cos = (a·b) / (|a||b|); cosine distance = 1 - cos.
        dot = 0.0
        for x, y in zip(a, b):
            dot += x * y
        return 1.0 - dot / (a_norm * b_norm)

    async def knn(
        self,
        query_vec: list[float],
        *,
        k: int,
        filter_fn: Callable[[Any], bool] | None = None,
    ) -> list[tuple[Any, float]]:
        await self._maybe_refresh()
        if not self._rows:
            return []
        q_norm = math.sqrt(sum(x * x for x in query_vec)) or 1.0
        scored: list[tuple[Any, float]] = []
        for row in self._rows:
            if filter_fn and not filter_fn(row.payload):
                continue
            d = self._cosine_distance(row.embedding, row.norm, query_vec, q_norm)
            scored.append((row.payload, d))
        scored.sort(key=lambda x: x[1])
        return scored[:k]

    def size(self) -> int:
        return len(self._rows)

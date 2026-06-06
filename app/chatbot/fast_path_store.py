"""Fast-path cache: curated Q->SQL pairs embedded once, KNN'd per request.

Ingest path (offline, scripts/ingest_fast_path.py):
  load data/fast_path_questions.json → embed each pair's question → upsert into
  chatbot_fast_path_embeddings.

Retrieval path (per request, chat_service.py):
  embed user question → cosine KNN top-1 (filtered by dialect) → if
  distance <= fast_path_distance_threshold AND pair is "literal" (no
  templating placeholders), return the cached SQL/refusal. Bot skips the LLM.

MVP: only literal pairs (params=[]) are returnable at runtime. Templated pairs
(params containing N/WINDOW/BRAND/COMPANY/CATEGORY) are still embedded so the
catalog is complete and KNN sees them, but the runtime checks for any `{...}`
placeholder in the returned SQL and falls through to the LLM if present.
Adding a slot-filler (extract N/WINDOW/etc from the user question, splice into
the SQL) is the next step — tracked separately.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.chatbot.embed_client import embed_text, to_pgvector_literal
from app.chatbot.readonly_db import get_pool
from app.chatbot._perf_cache import VectorSnapshot

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_CATALOG_FILE = _DATA_DIR / "fast_path_questions.json"
_PLACEHOLDER_RX = re.compile(r"\{[A-Z_]+\}")


@dataclass(frozen=True)
class FastPathPair:
    id: str
    group_name: str
    dialect: str  # 'postgres' | 'mysql' | 'any'
    question: str
    sql: str | None
    refusal: str | None
    params: list[str]

    @property
    def is_literal(self) -> bool:
        """A pair is literal when it has no template params AND no placeholders
        survive in its SQL/refusal — meaning the runtime can execute it as-is."""
        if self.params:
            return False
        body = (self.sql or "") + (self.refusal or "")
        return not _PLACEHOLDER_RX.search(body)

    @property
    def prompt_hash(self) -> str:
        body = self.sql or self.refusal or ""
        return hashlib.sha256(
            f"{self.question}\n---\n{body}".encode("utf-8")
        ).hexdigest()[:12]


@dataclass(frozen=True)
class FastPathHit:
    id: str
    group_name: str
    dialect: str
    question: str
    sql: str | None
    refusal: str | None
    params: list[str]
    distance: float

    @property
    def is_literal(self) -> bool:
        if self.params:
            return False
        body = (self.sql or "") + (self.refusal or "")
        return not _PLACEHOLDER_RX.search(body)


def load_pairs(path: Path = _CATALOG_FILE) -> list[FastPathPair]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    out: list[FastPathPair] = []
    for grp in parsed.get("groups") or []:
        group_name = grp.get("group", "")
        dialect = grp.get("dialect", "any")
        for idx, pair in enumerate(grp.get("pairs") or [], start=1):
            pair_id = f"{group_name}:{idx:03d}"
            out.append(FastPathPair(
                id=pair_id,
                group_name=group_name,
                dialect=dialect,
                question=pair.get("q", ""),
                sql=pair.get("sql"),
                refusal=pair.get("refusal"),
                params=list(pair.get("params") or []),
            ))
    return out


async def upsert_pair(
    pair: FastPathPair,
    embedding: list[float],
    conn: "object | None" = None,
) -> None:
    lit = to_pgvector_literal(embedding)
    sql = """
        INSERT INTO chatbot_fast_path_embeddings
            (id, group_name, question, sql, refusal, dialect, params, embedding, prompt_hash, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::vector, $9, now())
        ON CONFLICT (id) DO UPDATE SET
            group_name  = EXCLUDED.group_name,
            question    = EXCLUDED.question,
            sql         = EXCLUDED.sql,
            refusal     = EXCLUDED.refusal,
            dialect     = EXCLUDED.dialect,
            params      = EXCLUDED.params,
            embedding   = EXCLUDED.embedding,
            prompt_hash = EXCLUDED.prompt_hash,
            updated_at  = now()
        """
    params = (
        pair.id,
        pair.group_name,
        pair.question,
        pair.sql,
        pair.refusal,
        pair.dialect,
        json.dumps(pair.params),
        lit,
        pair.prompt_hash,
    )
    if conn is not None:
        await conn.execute(sql, *params)  # type: ignore[attr-defined]
        return
    pool = await get_pool()
    async with pool.acquire() as ro_conn:
        await ro_conn.execute(sql, *params)


async def delete_orphans(keep_ids: list[str], conn: "object | None" = None) -> int:
    sql = (
        "DELETE FROM chatbot_fast_path_embeddings "
        "WHERE id <> ALL($1::text[]) RETURNING id"
    )
    if conn is not None:
        rows = await conn.fetch(sql, keep_ids)  # type: ignore[attr-defined]
        return len(rows)
    pool = await get_pool()
    async with pool.acquire() as ro_conn:
        rows = await ro_conn.fetch(sql, keep_ids)
    return len(rows)


# ── In-memory snapshot of chatbot_fast_path_embeddings ──────────────────────


class _FastPathSnapshot(VectorSnapshot):
    def _row_to_payload(self, raw):  # type: ignore[override]
        raw_params = raw["params"]
        if isinstance(raw_params, str):
            try:
                raw_params = json.loads(raw_params)
            except json.JSONDecodeError:
                raw_params = []
        return {
            "id": raw["id"],
            "group_name": raw["group_name"],
            "dialect": raw["dialect"],
            "question": raw["question"],
            "sql": raw["sql"],
            "refusal": raw["refusal"],
            "params": list(raw_params or []),
        }


_SNAPSHOT = _FastPathSnapshot(
    table_name="chatbot_fast_path_embeddings",
    select_sql=(
        "SELECT id, group_name, question, sql, refusal, dialect, params, "
        "embedding FROM chatbot_fast_path_embeddings"
    ),
)


async def retrieve_match(
    question: str,
    *,
    distance_threshold: float,
    dialect: str | None = None,
) -> FastPathHit | None:
    """Embed the question and return the nearest cached pair if it clears the
    distance threshold. Optional dialect filter ('postgres' / 'mysql'); pairs
    tagged 'any' always match. Returns None on miss or embed error.

    Uses an in-process VectorSnapshot — no DB round-trip per request. embed_text
    itself is TTL-cached, so identical repeat questions resolve in <1 ms.
    """
    try:
        vec = await embed_text(question)
    except Exception:
        return None

    def _dialect_filter(payload):
        if not dialect:
            return True
        return payload["dialect"] == dialect or payload["dialect"] == "any"

    hits = await _SNAPSHOT.knn(vec, k=1, filter_fn=_dialect_filter)
    if not hits:
        return None
    payload, distance = hits[0]
    if distance > distance_threshold:
        return None
    return FastPathHit(
        id=payload["id"],
        group_name=payload["group_name"],
        dialect=payload["dialect"],
        question=payload["question"],
        sql=payload["sql"],
        refusal=payload["refusal"],
        params=payload["params"],
        distance=distance,
    )

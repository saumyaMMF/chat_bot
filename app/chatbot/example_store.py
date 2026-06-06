"""Few-shot example retrieval (cosine KNN).

Mirror of schema_store, scoped to the example corpus. Populated offline by
scripts/embed_examples.py. Queries at chat time return the top-k semantically
nearest question→sql/refusal pairs, filtered by a configurable distance
threshold so unrelated examples cannot leak into the prompt.

Table: chatbot_example_embeddings
  id text PK
  question text
  sql text NULL
  refusal text NULL
  expected_kind text  -- 'result' | 'refusal' | 'chat'
  embedding vector(768)
  row_hash text       -- sha256 of (question||body) — idempotent re-ingest
  updated_at timestamptz
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import re

from app.chatbot.embed_client import embed_text, to_pgvector_literal
from app.chatbot.readonly_db import get_pool
from app.chatbot._perf_cache import VectorSnapshot
from app.config import get_settings

log = logging.getLogger(__name__)

# Explicit market signals. Mirrors prompt_builder DEFAULT SCOPE rule.
_MARKET_SIGNALS = re.compile(
    r"\b(market|competitor|competitors|competing|rival|rivals|industry|"
    r"compared to others|vs others|scrape|scraped|across the market)\b",
    re.I,
)

# Tables/views considered MARKET (Postgres). Used to demote unrelated hits.
_MARKET_TABLES = {
    "chatbot_mv_market_daily",
    "complete_market_scrapper_dataset",
    "chatbot_market",
}


def _looks_market(question: str) -> bool:
    return bool(_MARKET_SIGNALS.search(question))


@dataclass
class ExampleHit:
    id: str
    question: str
    sql: str | None
    refusal: str | None
    expected_kind: str  # 'result' | 'refusal' | 'chat'
    distance: float


class ExampleRetrievalError(RuntimeError):
    pass


# ── In-memory snapshot of chatbot_example_embeddings ────────────────────────


class _ExampleSnapshot(VectorSnapshot):
    def _row_to_payload(self, raw):  # type: ignore[override]
        return {
            "id": raw["id"],
            "question": raw["question"],
            "sql": raw["sql"],
            "refusal": raw["refusal"],
            "expected_kind": raw["expected_kind"],
        }


_SNAPSHOT = _ExampleSnapshot(
    table_name="chatbot_example_embeddings",
    select_sql=(
        "SELECT id, question, sql, refusal, expected_kind, embedding "
        "FROM chatbot_example_embeddings"
    ),
    watermark_column="created_at",
)


async def retrieve_examples(question: str, k: int) -> list[ExampleHit]:
    """Return the top-k examples nearest the question, filtered by the cosine
    distance threshold in config. Raises if zero pass the threshold so the
    caller can fall back to the static slice instead of silently injecting
    irrelevant few-shot pairs (the TS sibling has this exact bug)."""
    settings = get_settings()
    threshold = settings.embed_distance_threshold

    vec = await embed_text(question)
    knn_hits = await _SNAPSHOT.knn(vec, k=k * 2)  # oversample, then filter
    if not knn_hits:
        raise ExampleRetrievalError(
            "chatbot_example_embeddings is empty — run scripts/embed_examples.py"
        )

    hits = [
        ExampleHit(
            id=p["id"],
            question=p["question"],
            sql=p["sql"],
            refusal=p["refusal"],
            expected_kind=p["expected_kind"],
            distance=d,
        )
        for (p, d) in knn_hits
    ]

    filtered = [h for h in hits if h.distance <= threshold]
    if not filtered:
        raise ExampleRetrievalError(
            f"no examples within cosine distance {threshold} "
            f"(closest={hits[0].distance:.3f})"
        )

    # Engine-aware re-rank. If the question has no market signal, demote
    # market-table examples by +0.2 cosine distance so own-data examples win
    # ties. Cheap fix for the bias where "revenue" hits market and own-data
    # columns equally — without a market keyword the user almost always means
    # their own data.
    if not _looks_market(question):
        for h in filtered:
            sql_lower = (h.sql or "").lower()
            if any(t in sql_lower for t in _MARKET_TABLES):
                h.distance += 0.2
        filtered.sort(key=lambda h: h.distance)

    return filtered[:k]

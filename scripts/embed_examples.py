"""Embed every entry in data/examples.json and UPSERT into
chatbot_example_embeddings.

Runs against DATABASE_URL_ADMIN (writer role) — the bot's chatbot_ro role
only reads from this table.

Idempotent: each row gets a sha256(question||body) hash. Re-runs only
re-embed rows whose hash changed. Rows for examples removed from JSON
get deleted so the table stays in sync.

Batched: nomic-embed-text supports array input → 25 examples = 1-2 round
trips instead of 25. ~30× faster than the sequential pattern in the
schema ingest script.

USAGE:
    python -m scripts.embed_examples
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Load .env BEFORE the settings cache reads env.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.chatbot.embed_client import embed_batch  # noqa: E402
from app.config import get_settings  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("embed_examples")

_DATA = Path(__file__).resolve().parents[1] / "data" / "examples.json"
BATCH = 16


def _prompt_hash(question: str, body: str) -> str:
    return hashlib.sha256(f"{question}\n---\n{body}".encode("utf-8")).hexdigest()[:16]


def _expected_kind(ex: dict) -> str:
    if ex.get("sql"):
        return "result"
    if ex.get("refusal"):
        return "refusal"
    return "chat"


def _body(ex: dict) -> str:
    return ex.get("sql") or ex.get("refusal") or ""


def _make_id(idx: int, ex: dict) -> str:
    """Stable id: prefer an explicit ``id`` field, else index-prefixed slug of
    the first 40 chars of the question. Allows re-ordering examples.json
    without churning every row."""
    if ex.get("id"):
        return str(ex["id"])
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in ex["question"][:40]).strip("-")
    return f"ex-{idx:03d}-{slug}"


async def main() -> None:
    settings = get_settings()
    if not settings.database_url_admin:
        raise SystemExit("DATABASE_URL_ADMIN is required for offline ingest")

    raw = json.loads(_DATA.read_text(encoding="utf-8"))
    examples = raw.get("examples") or []
    if not examples:
        raise SystemExit("data/examples.json has no examples")

    log.info("loaded %d examples", len(examples))

    # Compute target rows with hashes — we'll embed only changed ones.
    target: list[dict] = []
    for i, ex in enumerate(examples):
        q = ex.get("question") or ""
        if not q.strip():
            continue
        body = _body(ex)
        target.append({
            "id": _make_id(i, ex),
            "question": q,
            "sql": ex.get("sql"),
            "refusal": ex.get("refusal"),
            "expected_kind": _expected_kind(ex),
            "prompt_hash": _prompt_hash(q, body),
        })

    conn = await asyncpg.connect(settings.database_url_admin)
    try:
        # Read existing hashes to skip unchanged rows.
        existing = {
            r["id"]: r["prompt_hash"]
            for r in await conn.fetch(
                "SELECT id, prompt_hash FROM chatbot_example_embeddings"
            )
        }

        to_embed = [t for t in target if existing.get(t["id"]) != t["prompt_hash"]]
        log.info("to embed: %d  (unchanged: %d)", len(to_embed), len(target) - len(to_embed))

        # Batched embed.
        for start in range(0, len(to_embed), BATCH):
            chunk = to_embed[start : start + BATCH]
            vecs = await embed_batch([r["question"] for r in chunk])
            for r, vec in zip(chunk, vecs):
                r["embedding"] = vec
            log.info("embedded batch %d..%d", start, start + len(chunk))

        # Upsert.
        for r in to_embed:
            lit = "[" + ",".join(repr(float(x)) for x in r["embedding"]) + "]"
            await conn.execute(
                """
                INSERT INTO chatbot_example_embeddings
                  (id, question, sql, refusal, expected_kind, embedding, prompt_hash)
                VALUES ($1, $2, $3, $4, $5, $6::vector, $7)
                ON CONFLICT (id) DO UPDATE SET
                  question      = EXCLUDED.question,
                  sql           = EXCLUDED.sql,
                  refusal       = EXCLUDED.refusal,
                  expected_kind = EXCLUDED.expected_kind,
                  embedding     = EXCLUDED.embedding,
                  prompt_hash   = EXCLUDED.prompt_hash
                """,
                r["id"], r["question"], r["sql"], r["refusal"],
                r["expected_kind"], lit, r["prompt_hash"],
            )

        # Delete rows whose id is no longer in the JSON.
        keep = {t["id"] for t in target}
        stale = [eid for eid in existing if eid not in keep]
        if stale:
            await conn.execute(
                "DELETE FROM chatbot_example_embeddings WHERE id = ANY($1::text[])",
                stale,
            )
            log.info("deleted %d stale rows", len(stale))

        await conn.execute("ANALYZE chatbot_example_embeddings")
        log.info("done. total rows: %d", await conn.fetchval(
            "SELECT count(*) FROM chatbot_example_embeddings"
        ))
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

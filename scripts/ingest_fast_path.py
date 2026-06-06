"""Embed every pair in data/fast_path_questions.json and upsert into
chatbot_fast_path_embeddings. Idempotent — pairs whose prompt_hash is
unchanged are skipped. Pairs deleted from JSON are removed from the table.

Usage:
    python -m scripts.ingest_fast_path
    python -m scripts.ingest_fast_path --dry-run

Prereqs:
    1. sql/007_fast_path_embeddings.sql applied.
    2. Embedding endpoint reachable (nomic-embed-text via Ollama by default).
    3. DATABASE_URL_ADMIN (or RO with INSERT/DELETE) set.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import asyncpg

from app.chatbot.embed_client import embed_text
from app.chatbot.fast_path_store import (
    FastPathPair,
    delete_orphans,
    load_pairs,
    upsert_pair,
)
from app.chatbot.readonly_db import close_pool
from app.config import get_settings


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="ingest_fast_path")
    p.add_argument("--dry-run", action="store_true", help="print, don't write")
    return p.parse_args()


async def _run(args: argparse.Namespace) -> int:
    pairs: list[FastPathPair] = load_pairs()
    if not pairs:
        print("no pairs to ingest", file=sys.stderr)
        return 1

    settings = get_settings()
    admin_url = settings.database_url_admin or settings.database_url_ro
    if not admin_url:
        print("DATABASE_URL_ADMIN (or RO) required for ingest.", file=sys.stderr)
        return 1
    if not settings.database_url_admin and not args.dry_run:
        print(
            "WARN: DATABASE_URL_ADMIN unset — falling back to RO. Upsert/delete "
            "will fail if the RO role lacks INSERT/DELETE on the table.",
            file=sys.stderr,
        )

    admin_conn: asyncpg.Connection | None = None
    if not args.dry_run:
        admin_conn = await asyncpg.connect(dsn=admin_url)

    print(f"ingesting {len(pairs)} fast-path pair(s)...")
    ok = 0
    skipped = 0
    keep_ids: list[str] = []
    try:
        existing_hashes: dict[str, str] = {}
        if admin_conn is not None:
            rows = await admin_conn.fetch(
                "SELECT id, prompt_hash FROM chatbot_fast_path_embeddings"
            )
            existing_hashes = {r["id"]: r["prompt_hash"] for r in rows}

        for pair in pairs:
            keep_ids.append(pair.id)
            if existing_hashes.get(pair.id) == pair.prompt_hash:
                skipped += 1
                continue

            try:
                vec = await embed_text(pair.question)
            except Exception as exc:
                print(f"  [SKIP] {pair.id}: embed failed: {exc}", file=sys.stderr)
                continue

            if args.dry_run:
                print(f"  [DRY ] {pair.id} ({len(vec)} dims)")
                ok += 1
                continue

            try:
                await upsert_pair(pair, vec, conn=admin_conn)
            except Exception as exc:
                print(f"  [FAIL] {pair.id}: upsert failed: {exc}", file=sys.stderr)
                continue
            print(f"  [OK  ] {pair.id}")
            ok += 1

        deleted = 0
        if not args.dry_run and admin_conn is not None:
            try:
                deleted = await delete_orphans(keep_ids, conn=admin_conn)
            except Exception as exc:
                print(f"orphan delete failed: {exc}", file=sys.stderr)
    finally:
        if admin_conn is not None:
            await admin_conn.close()

    print(
        f"done: upserted={ok} skipped(unchanged)={skipped} "
        f"deleted={deleted if not args.dry_run else 0} total_pairs={len(pairs)}"
    )
    return 0


def main() -> None:
    args = _parse_args()
    try:
        rc = asyncio.run(_wrap(args))
    except KeyboardInterrupt:
        rc = 130
    sys.exit(rc)


async def _wrap(args: argparse.Namespace) -> int:
    try:
        return await _run(args)
    finally:
        await close_pool()


if __name__ == "__main__":
    main()

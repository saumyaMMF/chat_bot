"""Embed every entry in data/schema_definitions.json and upsert into
chatbot_schema_embeddings.

Usage:
    python -m scripts.ingest_schema             # embed all
    python -m scripts.ingest_schema --dry-run   # print, don't write
    python -m scripts.ingest_schema --only complete_market_scrapper_dataset

Prereqs:
    1. sql/006_schema_embeddings.sql applied (table + ivfflat index).
    2. Ollama running with the embed model (nomic-embed-text).
    3. DATABASE_URL_RO set (the chatbot_ro role needs INSERT on this table —
       in dev you may want a separate DATABASE_URL with broader perms;
       see README for the recommended split).
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import asyncpg

from app.chatbot.embed_client import embed_text
from app.chatbot.readonly_db import close_pool
from app.chatbot.schema_store import (
    SchemaItem,
    analyze_table,
    load_definitions,
    upsert_item,
)
from app.config import get_settings


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="ingest_schema")
    p.add_argument("--dry-run", action="store_true", help="print, don't write")
    p.add_argument("--only", default=None, help="filter by table_name")
    return p.parse_args()


async def _run(args: argparse.Namespace) -> int:
    items: list[SchemaItem] = load_definitions()
    if args.only:
        items = [i for i in items if i.table_name == args.only]
    if not items:
        print("no items to ingest", file=sys.stderr)
        return 1

    settings = get_settings()
    admin_url = settings.database_url_admin or settings.database_url_ro
    if not admin_url:
        print(
            "DATABASE_URL_ADMIN (or DATABASE_URL_RO) must be set for ingest.",
            file=sys.stderr,
        )
        return 1
    if not settings.database_url_admin and not args.dry_run:
        print(
            "WARN: DATABASE_URL_ADMIN not set — falling back to DATABASE_URL_RO. "
            "If the RO role lacks INSERT on chatbot_schema_embeddings, upserts will fail.",
            file=sys.stderr,
        )

    admin_conn: asyncpg.Connection | None = None
    if not args.dry_run:
        admin_conn = await asyncpg.connect(dsn=admin_url)

    print(f"ingesting {len(items)} schema item(s)...")
    ok = 0
    try:
        for it in items:
            text = it.embed_text
            try:
                vec = await embed_text(text)
            except Exception as exc:
                print(f"  [SKIP] {it.id}: embed failed: {exc}", file=sys.stderr)
                continue

            if args.dry_run:
                print(f"  [DRY ] {it.id} ({len(vec)} dims)")
                ok += 1
                continue

            try:
                await upsert_item(it, vec, conn=admin_conn)
            except Exception as exc:
                print(f"  [FAIL] {it.id}: upsert failed: {exc}", file=sys.stderr)
                continue
            print(f"  [OK  ] {it.id}")
            ok += 1

        if not args.dry_run and ok > 0 and admin_conn is not None:
            try:
                await analyze_table(conn=admin_conn)
                print("ANALYZE complete")
            except Exception as exc:
                print(f"ANALYZE failed: {exc}", file=sys.stderr)
    finally:
        if admin_conn is not None:
            await admin_conn.close()

    print(f"done: {ok}/{len(items)} ingested")
    return 0 if ok == len(items) else 2


def main() -> None:
    args = _parse_args()
    try:
        rc = asyncio.run(_run(args) if False else _wrap(args))
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

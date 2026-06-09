"""Delete chatbot_schema_embeddings rows whose id is not in the current
data/schema_definitions.json. Run after regenerating defs to drop orphans.

Usage:
    python -m scripts.prune_schema_embeddings           # delete
    python -m scripts.prune_schema_embeddings --dry-run # show only
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import asyncpg

from app.config import get_settings

DEF_PATH = Path(__file__).resolve().parents[1] / "data" / "schema_definitions.json"


async def _run(dry: bool) -> int:
    ids = [i["id"] for i in json.loads(DEF_PATH.read_text(encoding="utf-8"))["items"]]
    settings = get_settings()
    url = settings.database_url_admin or settings.database_url_ro
    if not url:
        print("DATABASE_URL_ADMIN or DATABASE_URL_RO required", file=sys.stderr)
        return 1
    conn = await asyncpg.connect(dsn=url)
    try:
        orphans = await conn.fetch(
            "SELECT id FROM chatbot_schema_embeddings WHERE id <> ALL($1::text[])",
            ids,
        )
        print(f"orphans: {len(orphans)}")
        for r in orphans:
            print(f"  {r['id']}")
        if dry or not orphans:
            return 0
        n = await conn.execute(
            "DELETE FROM chatbot_schema_embeddings WHERE id <> ALL($1::text[])",
            ids,
        )
        print(f"deleted: {n}")
    finally:
        await conn.close()
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sys.exit(asyncio.run(_run(args.dry_run)))


if __name__ == "__main__":
    main()

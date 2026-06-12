"""One-shot migration: widen chatbot_example_embeddings.expected_kind check
constraint to allow 'clarify' (bare-entity clarify teaching examples).

Run: python scripts/apply_clarify_constraint.py
Then: python -m scripts.embed_examples
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


async def main() -> None:
    conn = await asyncpg.connect(os.environ["DATABASE_URL_ADMIN"])
    try:
        await conn.execute(
            "ALTER TABLE chatbot_example_embeddings "
            "DROP CONSTRAINT IF EXISTS chatbot_example_embeddings_expected_kind_check"
        )
        await conn.execute(
            "ALTER TABLE chatbot_example_embeddings "
            "ADD CONSTRAINT chatbot_example_embeddings_expected_kind_check "
            "CHECK (expected_kind IN ('result','refusal','chat','clarify'))"
        )
        print("constraint updated: expected_kind now allows 'clarify'")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

"""Debug what the retrieval layer returns for a given question.

Usage:
    python -m scripts.debug_retrieval "latest revenue peak"
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.chatbot.example_store import retrieve_examples  # noqa: E402
from app.chatbot.schema_store import retrieve_top_k  # noqa: E402
from app.config import get_settings  # noqa: E402


async def main() -> None:
    question = " ".join(sys.argv[1:]) or "latest revenue peak"
    settings = get_settings()
    print(f"\n=== question ===\n{question}\n")
    print(f"distance threshold: {settings.embed_distance_threshold}\n")

    print("=== schema chunks ===")
    chunks = await retrieve_top_k(question, k=settings.schema_top_k)
    for c in chunks:
        marker = " " if c.distance <= settings.embed_distance_threshold else "X"
        col = c.column_name or "-"
        print(f"  [{marker}] {c.distance:.3f}  {c.kind:6}  {c.table_name}.{col}")

    print("\n=== examples ===")
    try:
        hits = await retrieve_examples(question, k=settings.top_k)
        for h in hits:
            kind = "result" if h.sql else "refusal"
            print(f"  {h.distance:.3f}  [{kind:7}]  {h.question}")
    except Exception as exc:
        print(f"  FAILED: {exc}")


if __name__ == "__main__":
    asyncio.run(main())


"""Render the exact messages the LLM sees for a sample question.

Usage: python scripts/dump_prompt.py "your question here"
"""
import asyncio
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.chatbot.prompt_builder import build_messages


async def main(q: str) -> None:
    msgs = await build_messages(
        q,
        brand_name="Acme",
        display_name="Acme Cannabis",
        tenant_id=1,
        states=["VT"],
    )
    for i, m in enumerate(msgs):
        print(f"\n===== [{i}] role={m.role} =====")
        print(m.content)
    print("\n===== END =====")
    print(f"total messages: {len(msgs)}")


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "top brands in the market"
    asyncio.run(main(q))

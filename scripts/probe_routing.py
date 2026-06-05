"""Routing probe — read-only, no SQL execution.

Pipe questions in, get back the SQL the model would emit and which engine +
table(s) the router would dispatch to. Useful for verifying table-selection
behaviour without touching the databases.

Usage:
    # one-off
    python -m scripts.probe_routing "top brands in the market"

    # batch from stdin (one question per line)
    python -m scripts.probe_routing < questions.txt

    # batch from a file
    python -m scripts.probe_routing -f questions.txt

    # change tenant / states / brand identity
    python -m scripts.probe_routing --tenant 1 --states VT,MA --brand "Acme" "my revenue last 30 days"

Output per question (TSV-friendly):
    Q: <question>
    SQL: <model SQL or non-SQL reply>
    ENGINE: pg | mysql | -
    TABLES: t1, t2
    NOTE: <router rejection reason, if any>
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from app.chatbot.engine_router import route_engine
from app.chatbot.llm_client import chat_complete
from app.chatbot.prompt_builder import build_messages


def _read_questions(args: argparse.Namespace) -> list[str]:
    if args.questions:
        return args.questions
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]


async def _probe_one(
    question: str,
    *,
    tenant_id: int,
    states: list[str],
    brand_name: str | None,
    display_name: str | None,
) -> None:
    messages = await build_messages(
        question,
        brand_name=brand_name,
        display_name=display_name,
        tenant_id=tenant_id,
        states=states,
    )
    reply = await chat_complete(messages)
    text = (reply or "").strip()

    print(f"Q: {question}")
    upper = text.upper()
    if upper.startswith(("CHAT:", "REFUSE:", "CLARIFY:")):
        prefix = text.split(":", 1)[0].upper()
        print(f"SQL: <{prefix}> {text.split(':', 1)[1].strip() if ':' in text else ''}")
        print("ENGINE: -")
        print("TABLES: -")
        print("NOTE: model did not emit SQL")
        print()
        return

    print(f"SQL: {text}")
    route = route_engine(text)
    if route.ok:
        print(f"ENGINE: {route.engine}")
        print(f"TABLES: {', '.join(route.tables)}")
        print("NOTE: ok")
    else:
        print("ENGINE: -")
        print("TABLES: -")
        print(f"NOTE: {route.reason}")
    print()


async def _main(args: argparse.Namespace) -> None:
    states = [s.strip().upper() for s in args.states.split(",") if s.strip()]
    questions = _read_questions(args)
    if not questions:
        print("no questions provided", file=sys.stderr)
        sys.exit(2)

    for q in questions:
        try:
            await _probe_one(
                q,
                tenant_id=args.tenant,
                states=states,
                brand_name=args.brand,
                display_name=args.display,
            )
        except Exception as e:
            print(f"Q: {q}")
            print(f"SQL: <error> {e}")
            print("ENGINE: -")
            print("TABLES: -")
            print("NOTE: probe failed")
            print()


def main() -> None:
    p = argparse.ArgumentParser(prog="probe_routing")
    p.add_argument("questions", nargs="*", help="questions to probe (else read stdin / -f)")
    p.add_argument("-f", "--file", help="read questions from a file (one per line)")
    p.add_argument("--tenant", type=int, default=1)
    p.add_argument("--states", default="")
    p.add_argument("--brand", default=None)
    p.add_argument("--display", default=None)
    args = p.parse_args()
    asyncio.run(_main(args))


if __name__ == "__main__":
    main()

"""Interactive CLI for the chatbot.

Usage:
    python -m app.cli                       # defaults: tenant_id=1, no states
    python -m app.cli --tenant 42 --states VT,MA --brand "Acme"

At the prompt: type a question, press Enter. `exit` / `quit` / Ctrl+C to leave.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from app.chatbot.chat_service import ChatInput, run_chat
from app.chatbot.readonly_db import close_pool


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="rhize-chatbot")
    p.add_argument("--tenant", type=int, default=1, help="tenant_id (default 1)")
    p.add_argument("--states", default="", help="comma-separated, e.g. VT,MA")
    p.add_argument("--brand", default=None, help="tenant brand name (identity fast-path)")
    p.add_argument("--display", default=None, help="tenant display name")
    p.add_argument("--rows", type=int, default=10, help="max rows to print (default 10)")
    p.add_argument("--json", action="store_true", help="raw JSON output")
    return p.parse_args()


def _print_result(result, max_rows: int, as_json: bool) -> None:
    if as_json:
        payload = {
            "kind": result.kind,
            "message": result.message,
            "sql": result.sql,
            "row_count": result.row_count,
            "rows": result.rows,
        }
        print(json.dumps(payload, default=str, indent=2))
        return

    if result.kind == "chat":
        print(f"\nbot: {result.message}\n")
    elif result.kind == "refusal":
        print(f"\nbot (refused): {result.message}\n")
    elif result.kind == "error":
        print(f"\nbot (error): {result.message}\n")
        if result.sql:
            print(f"  last SQL: {result.sql}\n")
    elif result.kind == "result":
        print(f"\nSQL: {result.sql}")
        print(f"rows: {result.row_count}")
        for row in result.rows[:max_rows]:
            print(f"  {row}")
        if result.row_count > max_rows:
            print(f"  ... ({result.row_count - max_rows} more)")
        print()


async def _repl(args: argparse.Namespace) -> None:
    states = [s.strip().upper() for s in args.states.split(",") if s.strip()]
    print(f"rhize-chatbot REPL  tenant={args.tenant}  states={states or '(none)'}")
    print("Type a question, or 'exit' / Ctrl+C to quit.\n")

    try:
        while True:
            try:
                question = input("you> ").strip()
            except EOFError:
                break
            if not question:
                continue
            if question.lower() in {"exit", "quit", ":q"}:
                break

            try:
                result = await run_chat(
                    ChatInput(
                        tenant_id=args.tenant,
                        states=states,
                        question=question,
                        brand_name=args.brand,
                        display_name=args.display,
                    )
                )
            except Exception as exc:
                print(f"\nbot (crash): {type(exc).__name__}: {exc}\n", file=sys.stderr)
                continue

            _print_result(result, max_rows=args.rows, as_json=args.json)
    finally:
        await close_pool()


def main() -> None:
    args = _parse_args()
    try:
        asyncio.run(_repl(args))
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()

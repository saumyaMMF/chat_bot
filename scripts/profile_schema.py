"""Deep schema profiler — CLI.

Examples:
    python -m scripts.profile_schema --engine both
    python -m scripts.profile_schema --engine mysql --tables rhize_orders,rhize_stores
    python -m scripts.profile_schema --engine pg --tables chatbot_mv_market_daily
    python -m scripts.profile_schema --out data/profiles --engine both

Produces in --out:
    mysql__<table>.md  +  mysql__<table>.json
    postgres__<table>.md +  postgres__<table>.json
    INDEX.md  (overview of every profiled table)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from app.schema_profiler import profile_mysql, profile_postgres
from app.schema_profiler.writer import write_json, write_markdown


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="profile_schema")
    p.add_argument("--engine", choices=["mysql", "pg", "both"], default="both")
    p.add_argument("--tables", default=None,
                   help="Comma-separated table names. Omit for all (mysql=rhize_*, pg=public).")
    p.add_argument("--schemas", default="public",
                   help="Comma-separated PG schemas (default: public).")
    p.add_argument("--out", default="data/profiles", help="Output directory.")
    p.add_argument("--include-views", action="store_true",
                   help="Profile PG views too (slow — views re-aggregate base tables).")
    p.add_argument("--timeout-ms", type=int, default=60_000,
                   help="Per-statement timeout in ms (default 60s).")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


def _write_index(out_dir: Path, all_profiles) -> Path:
    lines = ["# Schema profiles — index", ""]
    by_engine: dict[str, list] = {}
    for prof in all_profiles:
        by_engine.setdefault(prof.engine, []).append(prof)
    for engine, profs in sorted(by_engine.items()):
        lines.append(f"## {engine}")
        lines.append("")
        lines.append("| Table | Rows | Cols | PK |")
        lines.append("| --- | ---: | ---: | --- |")
        for p in sorted(profs, key=lambda x: x.table):
            pk = ", ".join(p.primary_key) or "—"
            lines.append(f"| [`{p.table}`]({engine}__{p.table}.md) | {p.row_count:,} | {p.column_count} | {pk} |")
        lines.append("")
    idx = out_dir / "INDEX.md"
    idx.write_text("\n".join(lines), encoding="utf-8")
    return idx


async def _run(args: argparse.Namespace) -> int:
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    out_dir = Path(args.out)
    tables = [t.strip() for t in args.tables.split(",")] if args.tables else None
    schemas = [s.strip() for s in args.schemas.split(",")] if args.schemas else ["public"]

    all_profiles: list = []

    if args.engine in ("mysql", "both"):
        try:
            print("==> profiling MySQL…", flush=True)
            profs = await profile_mysql(tables, statement_timeout_ms=args.timeout_ms)
            all_profiles.extend(profs)
        except Exception as e:
            print(f"!! mysql profiling failed: {e}", file=sys.stderr)

    if args.engine in ("pg", "both"):
        try:
            print("==> profiling PostgreSQL…", flush=True)
            profs = await profile_postgres(
                tables, schemas=schemas,
                include_views=args.include_views,
                statement_timeout_ms=args.timeout_ms,
            )
            all_profiles.extend(profs)
        except Exception as e:
            print(f"!! pg profiling failed: {e}", file=sys.stderr)

    if not all_profiles:
        print("no profiles produced", file=sys.stderr)
        return 1

    for prof in all_profiles:
        md = write_markdown(prof, out_dir)
        js = write_json(prof, out_dir)
        print(f"   wrote {md.name} + {js.name}  ({prof.row_count:,} rows · {prof.column_count} cols)")

    idx = _write_index(out_dir, all_profiles)
    print(f"==> done. Index: {idx}")
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_run(_parse_args())))


if __name__ == "__main__":
    main()

"""Ingest data/profiles/*.json into chatbot_schema_embeddings.

Each profile emits:
  - 1 TABLE-level SchemaItem  (id=profile:tbl:<engine>:<table>)
  - 1 COLUMN-level SchemaItem per column (id=profile:col:<engine>:<table>:<col>)

Definition text packs everything the LLM needs to pick the right table/column
and avoid placeholder values: declared type, inferred kind, null %, distinct
count + full distinct list (when small), top values, pattern hints.

Usage:
    python -m scripts.ingest_profiles
    python -m scripts.ingest_profiles --dry-run
    python -m scripts.ingest_profiles --only rhize_orders
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import asyncpg

from app.chatbot.embed_client import embed_text
from app.chatbot.readonly_db import close_pool
from app.chatbot.schema_store import SchemaItem, analyze_table, upsert_item
from app.config import get_settings

PROFILES_DIR = Path(__file__).resolve().parents[1] / "data" / "profiles"
TOP_PREVIEW = 20
DISTINCT_PREVIEW = 80
MAX_DEF_CHARS = 4000


def _trim(s: str, limit: int = MAX_DEF_CHARS) -> str:
    return s if len(s) <= limit else s[: limit - 30] + " …(truncated)"


def _fmt_val(v: Any) -> str:
    if v is None:
        return "NULL"
    s = str(v)
    return s if len(s) <= 60 else s[:57] + "…"


def _table_definition(prof: dict) -> str:
    eng = prof["engine"]
    tbl = prof["table"]
    rows = prof["row_count"]
    cols = prof["column_count"]
    pk = ", ".join(prof.get("primary_key") or []) or "—"
    col_names = [c["name"] for c in prof["columns"]]
    lines = [
        f"TABLE {tbl} (engine={eng})",
        f"Rows: {rows:,} · Columns: {cols}",
        f"Primary key: {pk}",
        f"Columns: {', '.join(col_names)}",
    ]
    idx = prof.get("indexes") or []
    if idx:
        idx_str = "; ".join(
            f"{i['name']}({'U' if i.get('unique') else 'N'}: {','.join(i['columns'])})"
            for i in idx[:10]
        )
        lines.append(f"Indexes: {idx_str}")
    return "\n".join(lines)


def _column_definition(table: str, engine: str, col: dict) -> str:
    lines = [
        f"COLUMN {table}.{col['name']} (engine={engine})",
        f"Declared type: {col['declared_type']} · Inferred kind: {col['inferred_kind']}",
        f"Nullable: {col['nullable']} · Null %: {col['null_pct']}",
        f"Distinct: {col['distinct_count']:,} ({col['distinct_pct']}% of non-null)",
    ]
    flags: list[str] = []
    if col.get("is_unique"):
        flags.append("UNIQUE")
    if col.get("is_low_cardinality"):
        flags.append("LOW-CARDINALITY")
    for n in col.get("notes") or []:
        flags.append(n.upper())
    if flags:
        lines.append("Flags: " + ", ".join(flags))
    if col.get("min_value") is not None or col.get("max_value") is not None:
        lines.append(f"Range: min={_fmt_val(col.get('min_value'))} · max={_fmt_val(col.get('max_value'))}")
    if col.get("min_length") is not None:
        lines.append(
            f"Length: min={col['min_length']} · max={col['max_length']} · avg={col['avg_length']}"
        )
    if col.get("pattern_hints"):
        lines.append("Patterns: " + ", ".join(col["pattern_hints"]))
    dv = col.get("distinct_values")
    if dv:
        preview = dv[:DISTINCT_PREVIEW]
        more = f" (+{len(dv) - DISTINCT_PREVIEW} more)" if len(dv) > DISTINCT_PREVIEW else ""
        joined = ", ".join(f"'{_fmt_val(v)}'" for v in preview)
        lines.append(f"All distinct values ({len(dv)}): {joined}{more}")
    elif col.get("top_values"):
        top = col["top_values"][:TOP_PREVIEW]
        joined = ", ".join(f"'{_fmt_val(v)}'({n:,})" for v, n in top)
        lines.append(f"Top values: {joined}")
    return _trim("\n".join(lines))


def _restrictions_for_column(table: str, engine: str, col: dict) -> str:
    bits: list[str] = []
    name = col["name"]
    if name in ("tenantid", "state"):
        bits.append("Auto-injected by isolation layer — NEVER filter on this column.")
    if "currency-string" in (col.get("pattern_hints") or []):
        bits.append("Stored as TEXT with currency formatting — wrap in CAST(... AS DECIMAL(10,2)) for math.")
    if "integer-as-text" in (col.get("pattern_hints") or []) or "float-as-text" in (col.get("pattern_hints") or []):
        bits.append("Numeric value stored as TEXT — CAST before aggregating.")
    if "date-string-YYYY-MM-DD" in (col.get("pattern_hints") or []) and col.get("inferred_kind") != "date":
        bits.append("Date stored as TEXT YYYY-MM-DD — comparable with DATE_FORMAT(CURRENT_DATE,'%Y-%m-%d') style strings.")
    if col.get("is_low_cardinality") and col.get("distinct_values"):
        bits.append("Categorical — use only values from the distinct list above; never invent literals.")
    return " ".join(bits)


def _build_items(profile: dict) -> list[SchemaItem]:
    engine = profile["engine"]
    table = profile["table"]
    items: list[SchemaItem] = []
    items.append(SchemaItem(
        id=f"profile:tbl:{engine}:{table}",
        kind="table",
        table_name=table,
        column_name=None,
        data_type=None,
        definition=_table_definition(profile),
        restrictions="",
    ))
    for col in profile["columns"]:
        items.append(SchemaItem(
            id=f"profile:col:{engine}:{table}:{col['name']}",
            kind="column",
            table_name=table,
            column_name=col["name"],
            data_type=col["declared_type"],
            definition=_column_definition(table, engine, col),
            restrictions=_restrictions_for_column(table, engine, col),
        ))
    return items


def _load_profiles(only: str | None) -> list[dict]:
    out: list[dict] = []
    for p in sorted(PROFILES_DIR.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        if only and data.get("table") != only:
            continue
        out.append(data)
    return out


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="ingest_profiles")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--only", default=None, help="single table_name")
    return p.parse_args()


async def _run(args: argparse.Namespace) -> int:
    profiles = _load_profiles(args.only)
    if not profiles:
        print("no profile JSON found in data/profiles/", file=sys.stderr)
        return 1

    items: list[SchemaItem] = []
    for prof in profiles:
        items.extend(_build_items(prof))
    print(f"will ingest {len(items)} item(s) from {len(profiles)} profile(s)")

    settings = get_settings()
    admin_url = settings.database_url_admin or settings.database_url_ro
    if not admin_url:
        print("DATABASE_URL_ADMIN (or DATABASE_URL_RO) required", file=sys.stderr)
        return 1

    admin_conn: asyncpg.Connection | None = None
    if not args.dry_run:
        admin_conn = await asyncpg.connect(dsn=admin_url)

    ok = 0
    try:
        for it in items:
            try:
                vec = await embed_text(it.embed_text)
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
        await close_pool()

    print(f"done: {ok}/{len(items)} ingested")
    return 0 if ok == len(items) else 2


def main() -> None:
    try:
        rc = asyncio.run(_run(_parse_args()))
    except KeyboardInterrupt:
        rc = 130
    sys.exit(rc)


if __name__ == "__main__":
    main()

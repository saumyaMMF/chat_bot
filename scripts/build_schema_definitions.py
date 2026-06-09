"""Parse data/llm_optimized_schema_spec.md → data/schema_definitions.json.

The spec is the source of truth. This script converts its TABLE + Columns
sections into the JSON chunks consumed by scripts/ingest_schema.py.

Usage:
    python -m scripts.build_schema_definitions
    python -m scripts.build_schema_definitions --out data/schema_definitions.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "data" / "llm_optimized_schema_spec.md"
OUT_DEFAULT = ROOT / "data" / "schema_definitions.json"

TABLE_HEADER_RE = re.compile(r"^###\s+TABLES?:\s+`([^`]+)`(?:\s*\+\s*`([^`]+)`)?", re.M)
COL_SECTION_RE = re.compile(r"####\s+Columns\s*\n+(.+?)(?=\n###\s|\n---\s*\n|\Z)", re.S)
ATTR_KIND_RE = re.compile(r"\|\s*\*\*Kind\*\*\s*\|\s*([^|]+)\|")
ATTR_PURPOSE_RE = re.compile(r"\|\s*\*\*Purpose\*\*\s*\|\s*([^|]+)\|")
ATTR_USE_RE = re.compile(r"\|\s*\*\*Use When\*\*\s*\|\s*([^|]+)\|")
ATTR_AVOID_RE = re.compile(r"\|\s*\*\*Avoid When\*\*\s*\|\s*([^|]+)\|")
ATTR_GRAIN_RE = re.compile(r"\|\s*\*\*Data Grain\*\*\s*\|\s*([^|]+)\|")
ATTR_TENANCY_RE = re.compile(r"\|\s*\*\*Tenancy\*\*\s*\|\s*([^|]+)\|")
ATTR_RLS_RE = re.compile(r"\|\s*\*\*RLS\*\*\s*\|\s*([^|]+)\|")


def _clean(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("⚠️", "").strip()
    return s


def _kind_label(raw: str) -> str:
    raw_l = raw.lower()
    if "view" in raw_l:
        return "view"
    if "lookup" in raw_l:
        return "table"
    return "table"


def _split_md_row(line: str) -> list[str]:
    parts = [p.strip() for p in line.strip().strip("|").split("|")]
    return parts


def _parse_columns_block(block: str) -> list[dict]:
    lines = [ln for ln in block.splitlines() if ln.strip().startswith("|")]
    # drop header + separator
    rows = []
    for ln in lines:
        cells = _split_md_row(ln)
        if not cells or not cells[0]:
            continue
        if set(cells[0].replace(":", "").strip()) <= {"-"}:
            continue
        if cells[0].lower() == "column":
            continue
        rows.append(cells)
    return rows


def _strip_backticks(name: str) -> str:
    return name.strip().strip("`").strip()


def _build_table_item(table_name: str, header_attrs: str) -> dict:
    kind = "table"
    m = ATTR_KIND_RE.search(header_attrs)
    if m:
        kind = _kind_label(m.group(1))

    pieces: list[str] = []
    for label, rx in (
        ("Purpose", ATTR_PURPOSE_RE),
        ("Data grain", ATTR_GRAIN_RE),
        ("Use when", ATTR_USE_RE),
        ("Avoid when", ATTR_AVOID_RE),
    ):
        m = rx.search(header_attrs)
        if m:
            pieces.append(f"{label}: {_clean(m.group(1))}")

    restrictions_bits: list[str] = []
    m = ATTR_TENANCY_RE.search(header_attrs)
    if m:
        restrictions_bits.append(_clean(m.group(1)))
    m = ATTR_RLS_RE.search(header_attrs)
    if m:
        restrictions_bits.append("RLS: " + _clean(m.group(1)))

    return {
        "id": f"table:{table_name}",
        "kind": kind,
        "table_name": table_name,
        "definition": " ".join(pieces).strip() or f"Table {table_name}.",
        "restrictions": " ".join(restrictions_bits).strip(),
    }


def _build_column_item(table_name: str, cells: list[str]) -> dict | None:
    # | Column | Type | Nullable | Business Definition | Usage Notes |
    if len(cells) < 4:
        return None
    col_name = _strip_backticks(cells[0])
    if not col_name:
        return None
    data_type = _clean(cells[1]) if len(cells) > 1 else ""
    definition = _clean(cells[3]) if len(cells) > 3 else ""
    restrictions = _clean(cells[4]) if len(cells) > 4 else ""
    return {
        "id": f"col:{table_name}.{col_name}",
        "kind": "column",
        "table_name": table_name,
        "column_name": col_name,
        "data_type": data_type,
        "definition": definition,
        "restrictions": restrictions,
    }


def parse_spec(text: str) -> list[dict]:
    items: list[dict] = []
    # Split into per-table chunks by ### TABLE header
    headers = list(TABLE_HEADER_RE.finditer(text))
    for i, hdr in enumerate(headers):
        start = hdr.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        chunk = text[start:end]
        table_name = hdr.group(1)
        # extra name (e.g. infra dual-table section) — only first is the canonical
        items.append(_build_table_item(table_name, chunk))
        col_m = COL_SECTION_RE.search(chunk)
        if not col_m:
            continue
        for row in _parse_columns_block(col_m.group(1)):
            item = _build_column_item(table_name, row)
            if item:
                items.append(item)
    return items


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    ap.add_argument("--spec", default=str(SPEC))
    args = ap.parse_args()

    text = Path(args.spec).read_text(encoding="utf-8")
    items = parse_spec(text)
    payload = {
        "_comment": (
            "Auto-generated from data/llm_optimized_schema_spec.md by "
            "scripts/build_schema_definitions.py. Do not hand-edit — "
            "edit the spec md and regenerate."
        ),
        "dialect": "mixed",
        "items": items,
    }
    Path(args.out).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    n_tab = sum(1 for it in items if it["kind"] in ("table", "view"))
    n_col = sum(1 for it in items if it["kind"] == "column")
    print(f"wrote {args.out}: {len(items)} items ({n_tab} tables/views, {n_col} columns)")


if __name__ == "__main__":
    main()

"""Validate every SQL in data/examples.json against REAL column lists from
data/profiles/*.json. Reports unknown columns per example.

Run: python -m scripts.validate_examples
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlglot import exp, parse_one

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "data" / "profiles"
EXAMPLES = ROOT / "data" / "examples.json"


def load_table_cols() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for p in PROFILES.glob("*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        # filename = <engine>__<table>.json
        stem = p.stem
        if "__" not in stem:
            continue
        _, table = stem.split("__", 1)
        cols = {c["name"] for c in d.get("columns", []) if c.get("name")}
        out[table.lower()] = {c.lower() for c in cols}
    return out


def from_tables(tree) -> set[str]:
    ctes = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE) if c.alias_or_name}
    out = set()
    for t in tree.find_all(exp.Table):
        n = (t.name or "").lower()
        if n and n not in ctes:
            out.add(n)
    return out


def select_aliases(tree) -> set[str]:
    out = set()
    for a in tree.find_all(exp.Alias):
        nm = (a.alias or "").lower()
        if nm:
            out.add(nm)
    return out


def check(sql: str, cols_by_table: dict[str, set[str]]) -> list[str]:
    # CLARIFY teaching examples carry the clarify protocol text in the sql
    # field (prompt_builder renders it as the assistant turn) — not SQL.
    if sql.lstrip().upper().startswith("CLARIFY:"):
        return []
    try:
        tree = parse_one(sql)
    except Exception as e:
        return [f"parse error: {e}"]

    tables = from_tables(tree)
    known = tables & cols_by_table.keys()
    unknown_tables = tables - cols_by_table.keys()

    issues: list[str] = []
    for t in unknown_tables:
        # Postgres market tables not in MySQL profiles — skip.
        if t.startswith("chatbot_") or t.startswith("complete_market_") or t.startswith("market_"):
            continue
        issues.append(f"unknown table: {t}")

    if not known:
        return issues  # nothing to check against

    allowed: set[str] = set()
    for t in known:
        allowed |= cols_by_table[t]
    aliases = select_aliases(tree)

    bad: dict[str, list[str]] = {}
    for c in tree.find_all(exp.Column):
        nm = (c.name or "").lower()
        if not nm or nm == "*":
            continue
        if nm in allowed or nm in aliases:
            continue
        hints = [t for t, cs in cols_by_table.items() if nm in cs]
        bad.setdefault(nm, []).extend(hints)

    for col, hints in sorted(bad.items()):
        hint_str = f" (exists on: {', '.join(sorted(set(hints))[:3])})" if hints else ""
        issues.append(f"`{col}` not on {sorted(known)}{hint_str}")

    return issues


def main() -> int:
    cols_by_table = load_table_cols()
    print(f"loaded {len(cols_by_table)} table profiles")
    data = json.loads(EXAMPLES.read_text(encoding="utf-8"))
    fail = 0
    for i, ex in enumerate(data.get("examples") or []):
        sql = ex.get("sql")
        if not sql:
            continue
        issues = check(sql, cols_by_table)
        if issues:
            fail += 1
            print(f"\n[#{i}] {ex.get('question')!r}")
            for it in issues:
                print(f"    - {it}")
    print(f"\nfailed: {fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

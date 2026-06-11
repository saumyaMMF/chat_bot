"""Build eval/cases.json from eval/questionnaire.md.

Reads the per-table headings (`## N. <table_name>  (...)`) and the
numbered questions beneath each. Emits one case per question, tagged by
table, with a loose `sql_match` regex that asserts the generated SQL
references the correct table.

This keeps the questionnaire as the single source of truth — edit
questionnaire.md and re-run this to regenerate cases.json.

USAGE:
    python -m eval.build_cases_from_questionnaire
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "questionnaire.md"
OUT = ROOT / "cases.json"

# Heading line shape: `## 1. rhize_dataset_main  (own daily sales ...)`
_HEADING_RX = re.compile(r"^##\s+\d+\.\s+([A-Za-z_][A-Za-z0-9_]*)\b")
_QUESTION_RX = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")

# Identity / chat-only questions that should not be SQL-graded.
_CHAT_RX = re.compile(r"^(what is my brand|list my brands|how many brands do i own)$", re.I)


def _expected_kind(table: str, q: str) -> str:
    # Brand "what is my brand" hits identity fast-path.
    if _CHAT_RX.search(q):
        return "chat"
    return "result"


def _sql_match(table: str, q: str) -> str | None:
    if _CHAT_RX.search(q):
        return None
    return rf"(?i){re.escape(table)}"


def main() -> int:
    lines = SRC.read_text(encoding="utf-8").splitlines()
    current_table: str | None = None
    cases: list[dict] = []
    counter: dict[str, int] = {}

    for line in lines:
        m = _HEADING_RX.match(line)
        if m:
            current_table = m.group(1)
            counter[current_table] = 0
            continue
        if current_table is None:
            continue
        mq = _QUESTION_RX.match(line)
        if not mq:
            continue
        counter[current_table] += 1
        n = counter[current_table]
        q = mq.group(2).strip()
        case = {
            "id": f"{current_table}-{n:02d}",
            "tag": f"sql-{current_table}",
            "question": q,
            "expected_kind": _expected_kind(current_table, q),
        }
        sm = _sql_match(current_table, q)
        if sm:
            case["sql_match"] = sm
        cases.append(case)

    payload = {
        "_comment": (
            "Auto-generated from eval/questionnaire.md by "
            "eval.build_cases_from_questionnaire. Hand-edit at your own "
            "risk — re-run the script to regenerate. Each case asserts "
            "kind=result + sql_match on the source table for that section. "
            "Identity questions are kind=chat (no SQL)."
        ),
        "tenant_id": 1,
        "states": ["CA"],
        "brand_name": "Rhize",
        "display_name": "Rhize",
        "cases": cases,
    }

    OUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"wrote {OUT} ({len(cases)} cases across {len(counter)} tables)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

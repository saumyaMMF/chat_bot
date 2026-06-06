"""Render a natural-language summary of a SQL result for chat display.

The bot returns ``ChatResult(kind="result", rows=[...], row_count=N)`` to the
UI. Without a summary the UI shows a raw widget — fine for a table, awkward
for a one-cell answer like ``Yes`` or ``12``. This module produces a short
sentence that sits above the widget so the user gets a human answer first.

Approach: deterministic templates keyed off question shape + result shape.
No second LLM round-trip — formatting must add <1 ms to the response, and
the LLM is already slow enough on CPU.

Shapes detected (priority order):
  - empty rows                              -> "No matches found ..."
  - 1 row, 1 column, EXISTS-style answer    -> "Yes" / "No"
  - 1 row, 1 column, count                  -> "12 products were added today."
  - 1 row, 1 column, generic                -> "{value}"
  - 1 row, many columns                     -> bullet of key fields
  - many rows                               -> "Found 23 results. Showing the
                                               top: A, B, C."

Question-intent hints come from the FIRST verb / wh-word — cheap to classify,
robust to typos because we lowercase + match prefixes. Falls back to a generic
"Here are the results." when nothing matches.
"""

from __future__ import annotations

import re
from typing import Any

# ── Intent classifiers ─────────────────────────────────────────────────────

_YES_NO_RX = re.compile(
    r"^\s*(does|do|did|is|are|was|were|has|have|had|will|can|could|should|"
    r"any|am)\b",
    re.I,
)
_COUNT_RX = re.compile(r"\b(how many|count of|number of|total\s+\w+\s+count)\b", re.I)
_LIST_RX = re.compile(
    r"\b(list|show|what|which|give me|find|fetch|display|tell me|name)\b",
    re.I,
)
_TOTAL_RX = re.compile(r"\b(total|sum|overall|grand|combined)\b", re.I)


# ── Helpers ────────────────────────────────────────────────────────────────


_MONEY_HINT_RX = re.compile(r"revenue|sales|price|balance|subtotal|total|cost|rev",
                            re.I)
_PCT_HINT_RX = re.compile(r"thc|pct|percent|share|rate", re.I)


def _fmt_value(value: Any, key_hint: str = "") -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int,)):
        if _MONEY_HINT_RX.search(key_hint):
            return f"${value:,}"
        return f"{value:,}"
    if isinstance(value, float):
        if _MONEY_HINT_RX.search(key_hint):
            return f"${value:,.2f}"
        if _PCT_HINT_RX.search(key_hint):
            return f"{value:.1f}%"
        return f"{value:,.2f}"
    s = str(value).strip()
    return s if s else "—"


def _looks_yes_no(rows: list[dict[str, Any]]) -> tuple[bool, str | None]:
    if len(rows) != 1:
        return False, None
    row = rows[0]
    if len(row) != 1:
        return False, None
    val = next(iter(row.values()))
    if isinstance(val, bool):
        return True, "Yes" if val else "No"
    if isinstance(val, str) and val.strip().lower() in {"yes", "no", "true", "false", "y", "n"}:
        s = val.strip().lower()
        return True, "Yes" if s in {"yes", "true", "y"} else "No"
    if isinstance(val, (int, float)):
        # CASE WHEN returning 1/0 sometimes
        col = next(iter(row.keys())).lower()
        if any(t in col for t in ("exists", "has_", "is_", "added_today",
                                  "removed_today", "found")):
            return True, "Yes" if val else "No"
    return False, None


def _looks_count(question: str, rows: list[dict[str, Any]]) -> tuple[bool, int | None, str]:
    if not _COUNT_RX.search(question):
        return False, None, ""
    if len(rows) != 1:
        return False, None, ""
    row = rows[0]
    if len(row) != 1:
        return False, None, ""
    key = next(iter(row.keys()))
    val = next(iter(row.values()))
    if isinstance(val, int):
        return True, val, key
    if isinstance(val, float) and val.is_integer():
        return True, int(val), key
    return False, None, ""


def _looks_single_aggregate(rows: list[dict[str, Any]]) -> tuple[bool, str, Any]:
    if len(rows) != 1:
        return False, "", None
    row = rows[0]
    if len(row) != 1:
        return False, "", None
    key = next(iter(row.keys()))
    val = next(iter(row.values()))
    return True, key, val


def _column_phrase(col: str) -> str:
    """Turn a column name into a phrase. ``added_count`` -> ``added``,
    ``total_revenue`` -> ``total revenue``, ``no_change_count`` -> ``unchanged``."""
    c = col.lower().strip()
    c = re.sub(r"_count$", "", c)
    c = c.replace("_", " ")
    aliases = {
        "no change": "unchanged",
        "added": "added",
        "removed": "removed",
        "n": "items",
        "added count": "added",
        "removed count": "removed",
    }
    return aliases.get(c, c) or "items"


def _list_sample(rows: list[dict[str, Any]], limit: int = 3) -> str:
    """Render up to ``limit`` row names for a list preview."""
    if not rows:
        return ""
    names: list[str] = []
    for r in rows[:limit]:
        # Prefer a name-like column over IDs.
        candidate = None
        for k in r:
            kl = k.lower()
            if any(t in kl for t in ("name", "product", "brand", "company",
                                     "customer", "strain", "title")):
                candidate = r[k]
                break
        if candidate is None:
            candidate = next(iter(r.values()))
        s = str(candidate).strip() if candidate is not None else ""
        if s:
            names.append(s)
    return ", ".join(names)


# ── Public entrypoint ──────────────────────────────────────────────────────


def is_terminal_answer(question: str, rows: list[dict[str, Any]]) -> bool:
    """True when the rendered ``format_answer`` string is the complete answer
    and the row widget adds no value — e.g. yes/no questions, COUNT(*),
    SUM(*). Caller should emit ``kind="chat"`` with just the message so the
    UI does not draw a one-cell table underneath.
    """
    if len(rows) != 1:
        return False
    row = rows[0]
    # Single cell results: trivially terminal.
    if len(row) != 1:
        return False
    q = (question or "").strip()
    if _YES_NO_RX.match(q):
        return True
    if _COUNT_RX.search(q):
        return True
    if _TOTAL_RX.search(q):
        return True
    val = next(iter(row.values()))
    # numeric/bool single-cell almost always terminal.
    if isinstance(val, (bool, int, float)):
        return True
    return False


def format_answer(question: str, sql: str | None, rows: list[dict[str, Any]]) -> str:
    """Return a one-sentence natural-language summary for the chat UI.

    Always returns SOMETHING — falls back to a generic blurb on unknown shape.
    Never raises; formatting must not break the request.
    """
    try:
        q = (question or "").strip()
        n = len(rows)

        # Empty result.
        if n == 0:
            if _YES_NO_RX.match(q):
                return "No."
            if _COUNT_RX.search(q):
                return "Zero results."
            return "No matches found."

        # Yes/No.
        yes_no, verdict = _looks_yes_no(rows)
        if yes_no:
            return verdict or "—"

        # Count question with single integer result.
        is_count, count_val, count_key = _looks_count(q, rows)
        if is_count and count_val is not None:
            phrase = _column_phrase(count_key)
            if phrase == "items":
                return f"{count_val:,} found."
            return f"{count_val:,} {phrase}."

        # Single-row single-column generic aggregate.
        is_single, key, val = _looks_single_aggregate(rows)
        if is_single:
            shaped = _fmt_value(val, key)
            label = key.replace("_", " ").strip()
            return f"{label.capitalize()}: {shaped}"

        # Multi-row list.
        if n == 1:
            row = rows[0]
            bits = [f"**{k.replace('_',' ')}**: {_fmt_value(v, k)}" for k, v in row.items()][:5]
            return "Here's what I found — " + "; ".join(bits) + "."

        sample = _list_sample(rows, limit=3)
        intent = "Found" if not _LIST_RX.search(q) else "Here are"
        if sample:
            more = "" if n <= 3 else f" (+{n - 3} more)"
            return f"{intent} {n:,} results: {sample}{more}."
        return f"{intent} {n:,} results."
    except Exception:
        return "Here are the results."

"""Shared pure-Python helpers — classification, pattern detection, type inference."""

from __future__ import annotations

import re
from typing import Any


_DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RX = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?")
_CURRENCY_RX = re.compile(r"^\s*\$?\s*-?\d{1,3}(,\d{3})*(\.\d+)?\s*$|^\s*-?\d+(\.\d+)?\s*$")
_PCT_RX = re.compile(r"^\s*-?\d+(\.\d+)?\s*%\s*$")
_INT_RX = re.compile(r"^-?\d+$")
_FLOAT_RX = re.compile(r"^-?\d+\.\d+$")
_JSON_RX = re.compile(r"^\s*[\[{].*[\]}]\s*$", re.S)
_EMAIL_RX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_UUID_RX = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_BOOL_TOKENS = {"true", "false", "yes", "no", "y", "n", "0", "1", "t", "f"}


def classify_pattern(samples: list[Any]) -> list[str]:
    """Inspect distinct sample values, return list of detected patterns."""
    if not samples:
        return []
    strs = [str(s).strip() for s in samples if s is not None][:200]
    if not strs:
        return ["all-null"]
    hits: dict[str, int] = {}
    for s in strs:
        if _DATE_RX.match(s):
            hits["date-string-YYYY-MM-DD"] = hits.get("date-string-YYYY-MM-DD", 0) + 1
        if _DATETIME_RX.match(s):
            hits["datetime-string"] = hits.get("datetime-string", 0) + 1
        if _PCT_RX.match(s):
            hits["percent-string"] = hits.get("percent-string", 0) + 1
        if "$" in s and _CURRENCY_RX.match(s):
            hits["currency-string"] = hits.get("currency-string", 0) + 1
        elif _INT_RX.match(s):
            hits["integer-as-text"] = hits.get("integer-as-text", 0) + 1
        elif _FLOAT_RX.match(s):
            hits["float-as-text"] = hits.get("float-as-text", 0) + 1
        if _JSON_RX.match(s):
            hits["json-like"] = hits.get("json-like", 0) + 1
        if _EMAIL_RX.match(s):
            hits["email"] = hits.get("email", 0) + 1
        if _UUID_RX.match(s):
            hits["uuid"] = hits.get("uuid", 0) + 1
        if s.lower() in _BOOL_TOKENS:
            hits["boolean-token"] = hits.get("boolean-token", 0) + 1
    threshold = max(1, int(0.7 * len(strs)))
    return sorted(k for k, n in hits.items() if n >= threshold) or []


def infer_kind(declared_type: str, patterns: list[str]) -> str:
    t = declared_type.lower()
    if any(k in t for k in ("int", "serial", "bigserial")):
        return "integer"
    if any(k in t for k in ("decimal", "numeric", "real", "double", "float")):
        return "float"
    if "bool" in t:
        return "bool"
    if "json" in t:
        return "json"
    if "timestamp" in t or "datetime" in t:
        return "datetime"
    if t == "date":
        return "date"
    if "date-string-YYYY-MM-DD" in patterns:
        return "date"
    if "datetime-string" in patterns:
        return "datetime"
    if "currency-string" in patterns or "integer-as-text" in patterns or "float-as-text" in patterns:
        return "numeric"
    if "boolean-token" in patterns:
        return "bool"
    if "json-like" in patterns:
        return "json"
    if any(k in t for k in ("char", "text", "varchar", "string")):
        return "text"
    return "unknown"


def classify_cardinality(distinct: int, total_non_null: int) -> tuple[bool, bool]:
    """Return (is_unique, is_low_cardinality)."""
    if total_non_null == 0:
        return False, False
    is_unique = distinct == total_non_null and distinct > 1
    is_low = distinct <= 50
    return is_unique, is_low

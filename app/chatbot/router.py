"""Deterministic stage-1 router.

Runs BEFORE fast-path / RAG / LLM. Two cheap lookups:

  1. `column_pin(question)` — exact substring match against the
     `column_index.json` unique-column tokens. If a question contains a token
     owned by exactly one table, that table is pinned and the engine
     (postgres / mysql) is locked. Skips the LLM's table-choice step
     entirely.

  2. `route_signal(question)` — synonym tagging (`synonyms.json`).
     Categorises the question into ownership (`own` / `market` / `mixed`)
     and surfaces candidate tables ranked by best→worst. Used to bias the
     engine gate, fast-path dialect, and few-shot retrieval bucket.

Both functions are pure-Python regex over a question string. No DB, no
embed, no LLM. Sub-millisecond. Loaded once at module import via
`@functools.lru_cache`.

If the routing pack is missing (e.g. test env without data files), the
functions return `None` / empty so callers fall through to the legacy
heuristics — never break the request.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

log = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "routing"


# ── Table → engine map (mirrors engine_router) ──────────────────────────────
_TABLE_ENGINE = {
    "chatbot_mv_market_daily": "postgres",
    "chatbot_market":          "postgres",
    "rhize_orders":            "mysql",
    "rhize_live_inventory":    "mysql",
    "rhize_product_lots":      "mysql",
    "rhize_brands":            "mysql",
    "rhize_stores":            "mysql",
    "rhize_partner_stores":    "mysql",
    "rhize_strain_info":       "mysql",
    "rhize_sales_actions":     "mysql",
    "rhize_dataset_main":      "mysql",
    "rhize_dataset_store":     "mysql",
}


def _engine_for(table: str) -> str | None:
    return _TABLE_ENGINE.get(table)


@dataclass(frozen=True)
class ColumnPin:
    """Deterministic table pin from a uniquely-owning column token."""
    token: str
    table: str
    engine: str


@dataclass(frozen=True)
class RouteSignal:
    """Synonym-tagged routing hint."""
    ownership: str  # 'own' | 'market' | 'mixed' | 'unknown'
    candidate_tables: list[str]
    matched_tokens: list[str]

    @property
    def engine_hint(self) -> str | None:
        if not self.candidate_tables:
            return None
        return _engine_for(self.candidate_tables[0])


# ── Loaders ─────────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def _load_column_index() -> dict[str, str]:
    """Return ``{lowercased token: owning table}`` for unique columns only."""
    path = _DATA_DIR / "column_index.json"
    if not path.exists():
        log.warning("[router] column_index.json missing at %s", path)
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        idx = raw.get("unique_to_table") or {}
        # Defensive: lowercase keys, drop anything that maps to a multi-table list.
        return {
            str(k).lower(): str(v)
            for k, v in idx.items()
            if isinstance(v, str) and "|" not in v
        }
    except Exception as exc:
        log.error("[router] failed to load column_index.json: %s", exc)
        return {}


@lru_cache(maxsize=1)
def _load_synonyms() -> dict[str, dict[str, list[str]]]:
    """Return ``{section: {token: [table, ...]}}`` from synonyms.json. Values
    are split on ``|`` so the first entry is the preferred table."""
    path = _DATA_DIR / "synonyms.json"
    if not path.exists():
        log.warning("[router] synonyms.json missing at %s", path)
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        log.error("[router] failed to load synonyms.json: %s", exc)
        return {}
    out: dict[str, dict[str, list[str]]] = {}
    for section in ("ownership", "market", "concepts"):
        section_map = raw.get(section) or {}
        cleaned: dict[str, list[str]] = {}
        for token, target in section_map.items():
            if token.startswith("_") or not isinstance(target, str):
                continue
            tables = [t.strip() for t in target.split("|") if t.strip()]
            if tables:
                cleaned[str(token).lower()] = tables
        out[section] = cleaned
    return out


# ── Public API ──────────────────────────────────────────────────────────────


_TOKEN_BOUNDARY_RE = re.compile(r"[^\w']+")


def _normalise(question: str) -> str:
    """Lowercase + collapse whitespace. Keep apostrophes (Today's_...)."""
    return _TOKEN_BOUNDARY_RE.sub(" ", question.lower()).strip()


def column_pin(question: str) -> ColumnPin | None:
    """If the question contains a token uniquely owned by one table, pin it.

    Multi-word tokens are checked as raw substrings on the lowercased question;
    single-word tokens are checked as whole-word matches to avoid `lot` matching
    `slot`. Returns the longest matching token's pin (most specific wins).
    """
    idx = _load_column_index()
    if not idx:
        return None
    q_norm = _normalise(question)
    if not q_norm:
        return None

    best: tuple[str, str] | None = None  # (token, table)
    for token, table in idx.items():
        if " " in token:
            # multi-word: substring match on normalised text
            if token in q_norm:
                if best is None or len(token) > len(best[0]):
                    best = (token, table)
        else:
            # single-word: word-boundary match
            if re.search(rf"\b{re.escape(token)}\b", q_norm):
                if best is None or len(token) > len(best[0]):
                    best = (token, table)
    if best is None:
        return None
    engine = _engine_for(best[1])
    if engine is None:
        log.warning("[router] column_pin token=%r → unknown table %r", best[0], best[1])
        return None
    return ColumnPin(token=best[0], table=best[1], engine=engine)


def route_signal(question: str) -> RouteSignal:
    """Tag the question with ownership + candidate tables via synonyms."""
    syn = _load_synonyms()
    q_norm = _normalise(question)
    matched: list[str] = []
    own_hits: list[list[str]] = []
    market_hits: list[list[str]] = []
    concept_hits: list[list[str]] = []

    def _match_section(section: dict[str, list[str]], bucket: list[list[str]]) -> None:
        for token, tables in section.items():
            if " " in token or "*" in token:
                if token in q_norm:
                    matched.append(token)
                    bucket.append(tables)
            else:
                if re.search(rf"\b{re.escape(token)}\b", q_norm):
                    matched.append(token)
                    bucket.append(tables)

    _match_section(syn.get("ownership", {}), own_hits)
    _match_section(syn.get("market", {}), market_hits)
    _match_section(syn.get("concepts", {}), concept_hits)

    if own_hits and market_hits:
        ownership = "mixed"
    elif own_hits:
        ownership = "own"
    elif market_hits:
        ownership = "market"
    else:
        ownership = "unknown"

    # Resolve "rhize_*" wildcard from ownership hits — we don't pick a specific
    # rhize_* table from a bare possessive, just signal the dialect.
    candidates: list[str] = []
    for hit in own_hits + market_hits + concept_hits:
        for t in hit:
            if t.endswith("*"):
                continue
            if t in _TABLE_ENGINE and t not in candidates:
                candidates.append(t)

    return RouteSignal(
        ownership=ownership,
        candidate_tables=candidates,
        matched_tokens=matched,
    )

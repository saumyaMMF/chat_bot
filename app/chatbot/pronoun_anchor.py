"""Pronoun-anchored fast-path.

Local 3B model can't bind anaphora ("how many of them", "show 5 of those")
to prior turns even when the history block is in the prompt. Result: 40-60s
LLM round-trip that returns CHAT prose instead of SQL.

This module detects a follow-up that has ONLY pronouns / vague entity refs
and rewrites the question into deterministic SQL by reusing the FROM /
WHERE of the most recent successful turn. The rewritten SQL goes through
the same guard + LIMIT enforcement as the LLM path, so safety invariants
(tenant scope, statement timeout, row cap) are preserved.

Pure-Python — no LLM, no DB. Returns None when no confident anchor exists
so the caller can fall through to the normal pipeline.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from sqlglot import exp, parse_one

log = logging.getLogger(__name__)

# Sentence must contain at least one of these pronouns / vague refs, and
# must NOT name any new entity-type keyword on its own.
_PRONOUN_RX = re.compile(r"\b(them|those|these|it|that one|this one|that)\b", re.I)

# Words that strongly imply the user just wants the list of the prior
# entity. "name(s)", "show", "list", "give", "display" → SELECT name path.
_LIST_INTENT_RX = re.compile(
    r"\b(name|names|list|show|display|give|tell|share|return)\b",
    re.I,
)

# Count intent ("how many", "count").
_COUNT_INTENT_RX = re.compile(r"\b(how many|count|number of)\b", re.I)

# Quantity/qty intent — user wants stock/units column added to the projection.
_QTY_INTENT_RX = re.compile(r"\b(quantity|qty|units|stock|how much)\b", re.I)

# Revenue/sales intent — swap projection to Revenue/subtotal.
_REVENUE_INTENT_RX = re.compile(r"\b(revenue|sales|sold|earnings|earned)\b", re.I)

# LIMIT N hints in the follow-up. Defaults to 10 / 5 if absent.
_TOP_N_RX = re.compile(r"\b(?:top|first|name(?: of)?|show|list|give me)\s+(\d{1,3})\b", re.I)
_BARE_N_RX = re.compile(r"\b(\d{1,3})\b")

# If any of these tokens appears the question is NOT a pure follow-up; let
# the LLM path handle it (the user introduced a new entity). Metric words
# (revenue/sales/quantity/stock/inventory) are NOT here — they're intent
# modifiers like "qty"/"how much" and routinely co-occur with pronouns
# ("revenue of these products").
_NEW_ENTITY_RX = re.compile(
    r"\b(brand|brands|company|companies|sku|skus|order|orders|customer|"
    r"customers|product|products|category|categories|lots|"
    r"market|competitor|competitors|dispensary|"
    r"dispensaries|store|stores|partner|partners)\b",
    re.I,
)

# Semantic qualifiers the anchor templates cannot express — state changes
# ("inactive", "removed") and time windows ("past 7 days"). A COUNT/list
# pivot over the prior WHERE would silently answer a different question;
# bail to the LLM path instead.
_SEMANTIC_BAIL_RX = re.compile(
    r"\b(inactive|active|removed|dropped|gone|missing|new|changed|added|"
    r"since|before|after|between|growth|grew|declin\w*|compar\w*|trend\w*)\b"
    r"|\b(past|last|previous|next)\s+\d*\s*(day|days|week|weeks|month|months|year|years)\b",
    re.I,
)


@dataclass(frozen=True)
class AnchorResult:
    sql: str
    dialect: str  # 'mysql' | 'postgres'
    explanation: str


def _last_anchorable_sql(history) -> tuple[str, str] | None:
    """Walk history newest→oldest, return (sql, dialect) for the most recent
    turn whose SQL parses to a single SELECT we can pivot off of."""
    if not history:
        return None
    for turn in reversed(history):
        sql = (getattr(turn, "sql", None) or "").strip()
        if not sql:
            continue
        try:
            tree = parse_one(sql)
        except Exception:
            continue
        if not isinstance(tree, exp.Select):
            continue
        # Heuristic: pick dialect from table-name shape. `rhize_*` => mysql,
        # otherwise => postgres. Good enough since the routing pack
        # partitions tables that way.
        tables = [(t.name or "").lower() for t in tree.find_all(exp.Table)]
        if not tables:
            continue
        dialect = "mysql" if any(t.startswith("rhize_") for t in tables) else "postgres"
        return (sql, dialect)
    return None


def _swap_select_list(tree: exp.Select, new_select: str) -> exp.Select:
    """Replace the SELECT projection list while keeping FROM/WHERE/GROUP/ORDER
    intact. Returns a NEW tree (sqlglot expressions are mutable but copying
    keeps the original safe for logging)."""
    cloned = tree.copy()
    cloned.set(
        "expressions",
        [parse_one(new_select).args.get("this") or parse_one(new_select)
            for new_select in [new_select]],
    )
    return cloned


def _override_limit(tree: exp.Select, n: int) -> exp.Select:
    cloned = tree.copy()
    cloned.set("limit", exp.Limit(expression=exp.Literal.number(n)))
    return cloned


def _pick_list_columns(tree: exp.Select, *, qty_intent: bool = False,
                       revenue_intent: bool = False) -> list[str]:
    """Choose columns for the new SELECT. Intent flags swap in the metric
    column the user actually asked about — "quantity of these" should
    project a qty field, not the prior turn's columns."""
    tables = {(t.name or "").lower() for t in tree.find_all(exp.Table)}
    if "rhize_stores" in tables:
        return ["name", "city", "tier"]
    if "rhize_dataset_main" in tables:
        if qty_intent:
            return ["Product_Name", "Company_Name", "Today's_Quantity_Total"]
        if revenue_intent:
            return ["Product_Name", "Company_Name", "Revenue"]
        return ["Product_Name", "Brand_Name", "Revenue"]
    if "rhize_orders" in tables:
        if qty_intent:
            return ["productName", "qty", "subtotal"]
        if revenue_intent:
            return ["productName", "subtotal", "date"]
        return ["customerName", "subtotal", "createdAt"]
    if "rhize_live_inventory" in tables:
        return ["product", "qty", "unit"]
    if "rhize_brands" in tables:
        return ["name", "isRhize"]
    # Postgres market table fallback.
    if "chatbot_mv_market_daily" in tables:
        if qty_intent:
            return ["brand", "company", "quantity"]
        return ["brand", "company", "revenue"]
    return ["*"]


def try_pronoun_anchor(question: str, history) -> AnchorResult | None:
    """If ``question`` is a pronoun-only follow-up AND we have an anchorable
    last turn, return rewritten SQL. Else None.

    Conservative: bails out the moment a new entity word appears so the
    LLM path still gets ordinary mixed questions. Better to lose a fast-
    path opportunity than to answer the wrong question deterministically.
    """
    if not question or not history:
        return None
    if not _PRONOUN_RX.search(question):
        return None
    # Strip "(the|these|those|that) <entity>" before the new-entity check —
    # those phrases are anaphoric, not new-entity intros. "quantity of these
    # products" should anchor to the prior turn's product list, not be
    # treated as a brand-new "products" query.
    deanaphor = re.sub(
        r"\b(the|these|those|that)\s+(brand|brands|company|companies|sku|skus|"
        r"order|orders|customer|customers|product|products|category|categories|"
        r"revenue|inventory|stock|lots|sale|sales|market|competitor|competitors|"
        r"dispensary|dispensaries|store|stores|partner|partners)\b",
        " ",
        question,
        flags=re.I,
    )
    if _NEW_ENTITY_RX.search(deanaphor):
        return None
    if _SEMANTIC_BAIL_RX.search(question):
        return None

    anchor = _last_anchorable_sql(history)
    if anchor is None:
        return None
    prev_sql, dialect = anchor

    try:
        tree = parse_one(prev_sql)
    except Exception:
        return None
    if not isinstance(tree, exp.Select):
        return None

    n_match = _TOP_N_RX.search(question) or _BARE_N_RX.search(question)
    n = int(n_match.group(1)) if n_match else 10
    n = max(1, min(n, 200))

    out_dialect = "mysql" if dialect == "mysql" else "postgres"

    # Re-parse with the detected dialect. Dialect-less parse + dialect-ed
    # regen corrupts constructs like INTERVAL 7 DAY into
    # INTERVAL (INTERVAL '7' DAY) DAY, which the DB then rejects.
    try:
        tree = parse_one(prev_sql, read=out_dialect)
    except Exception:
        return None
    if not isinstance(tree, exp.Select):
        return None

    # COUNT intent: "how many of them" → SELECT COUNT(*) FROM same WHERE same
    if _COUNT_INTENT_RX.search(question):
        cloned = tree.copy()
        cloned.set("expressions", [exp.alias_(exp.Count(this=exp.Star()), "n")])
        # Drop ORDER/LIMIT/GROUP — they're meaningless for COUNT(*)
        for k in ("order", "limit", "group"):
            cloned.set(k, None)
        new_sql = cloned.sql(dialect=out_dialect)
        return AnchorResult(
            sql=new_sql,
            dialect=dialect,
            explanation=f"pronoun-anchor: COUNT(*) over prior FROM/WHERE (n={n} ignored for count)",
        )

    qty_intent = bool(_QTY_INTENT_RX.search(question))
    revenue_intent = bool(_REVENUE_INTENT_RX.search(question))

    # LIST intent: "names of them", "show 5 of those" → SELECT cols FROM same
    # qty/revenue intent on its own also implies list — "quantity of these"
    # means "list the entities with their quantity".
    if _LIST_INTENT_RX.search(question) or qty_intent or revenue_intent:
        # When the prior turn was an aggregate over a specific dimension
        # (COUNT(DISTINCT Company_Name)), "name them" means THAT column —
        # not the table's generic list projection. Reuse it.
        prior_dims = [
            c.name for e in tree.expressions for c in e.find_all(exp.Column)
            if c.name and not qty_intent and not revenue_intent
        ]
        if prior_dims and any(isinstance(a, exp.AggFunc) for e in tree.expressions for a in e.find_all(exp.AggFunc)):
            cols = list(dict.fromkeys(prior_dims))
        else:
            cols = _pick_list_columns(tree, qty_intent=qty_intent, revenue_intent=revenue_intent)
        select_expr_list = [
            exp.column(c) if c != "*" else exp.Star()
            for c in cols
        ]
        cloned = tree.copy()
        cloned.set("expressions", select_expr_list)
        cloned = _override_limit(cloned, n)
        # If no ORDER BY, add one on first non-star col for stable output
        if not cloned.args.get("order") and cols and cols[0] != "*":
            cloned.set("order", exp.Order(expressions=[exp.Ordered(this=exp.column(cols[0]))]))
        new_sql = cloned.sql(dialect=out_dialect)
        return AnchorResult(
            sql=new_sql,
            dialect=dialect,
            explanation=f"pronoun-anchor: SELECT {', '.join(cols)} LIMIT {n}",
        )

    # Default: re-run the prior SELECT with a smaller LIMIT so we surface
    # something useful instead of refusing.
    cloned = _override_limit(tree.copy(), n)
    new_sql = cloned.sql(dialect=out_dialect)
    return AnchorResult(
        sql=new_sql,
        dialect=dialect,
        explanation=f"pronoun-anchor: rerun prior SELECT LIMIT {n}",
    )

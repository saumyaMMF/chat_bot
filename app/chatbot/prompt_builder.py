"""Prompt builder.

Assembles the message list sent to the model:

  [system] RESTRICTION_RULES (always present, exact verbatim)
           + schema context (dynamic schema-RAG, static fallback)
           + per-request restrictions extracted from retrieved chunks
  [user/assistant] few-shot pairs (static top-K from examples.json)
  [user] the question

Schema context selection:
  1. PREFERRED — embed the question, KNN against chatbot_schema_embeddings,
     format the top-k chunks for the prompt. Tokens scale with retrieval, not
     with total schema size.
  2. FALLBACK — if the embed model or DB is unreachable, fall back to the full
     static schema_context.md dump. Bot keeps responding; logs a warning.

Isolation note: examples deliberately OMIT tenantid/state filters. RLS applies
them at the engine. The model is told NOT to add them.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.chatbot.llm_client import ChatMessage
from app.chatbot.example_store import ExampleRetrievalError, retrieve_examples
from app.chatbot.schema_store import (
    collect_restrictions,
    format_chunks_for_prompt,
    retrieve_top_k,
)
from app.config import get_settings

# Module-level breadcrumbs the eval harness can read to detect silent fallback.
# Reset at the start of every build_messages call.
LAST_BUILD_INFO: dict[str, Any] = {
    "schema_retrieval_ok": False,
    "schema_retrieval_reason": None,
    "schema_chunks": 0,
    "example_retrieval_ok": False,
    "example_retrieval_reason": None,
    "examples_used": 0,
    "examples_closest_distance": None,
}

log = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


# ----------------------------- restrictions (always-on) -----------------------------

_INTRO = (
    'You are the "Rhize Brand Intelligence Assistant" — a precise, read-only '
    "SQL analyst for a cannabis market-intelligence platform. You translate "
    "business questions about brands, companies, products, stores, inventory, "
    "sales, orders, and the broader market into a single safe SELECT "
    "statement, or you respond with CHAT / REFUSE / CLARIFY when SQL is not "
    "warranted."
)

_SECTION_1_REPLY_FORMAT = """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 1 — REPLY FORMAT (always pick exactly ONE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHAT:    <one short sentence>     → greetings, small talk, capabilities
REFUSE:  <one short sentence>     → per Section 6 refusal rules
CLARIFY: <question> + options     → per Section 4 disambiguation rules
<raw SQL>                         → all real data questions; no prose, no fences,
                                    no comments, no extra text"""

_SECTION_3_ENGINE_ROUTING = """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 3 — ENGINE ROUTING (pick ONE engine per query)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFAULT → MySQL (rhize_* tables)
  Apply to ALL questions unless an explicit market signal is present (see below).
  "My", "our", "we", and bare unqualified questions always mean own data.

  Common phrase → table mapping:
  ┌─────────────────────────────────┬─────────────────────────────────────────┐
  │ Phrase                          │ Table / approach                        │
  ├─────────────────────────────────┼─────────────────────────────────────────┤
  │ revenue, my revenue, our revenue│ rhize_dataset_main (cast Revenue, group │
  │                                 │ by date)                                │
  │ sales                           │ rhize_orders WHERE status='Completed'   │
  │ orders                          │ rhize_orders                            │
  │ open balance                    │ rhize_orders WHERE status<>'Completed'  │
  │ inventory, stock                │ rhize_live_inventory                    │
  │ lots, expiring                  │ rhize_product_lots                      │
  │ stores, partners                │ rhize_stores                            │
  │ sales actions, CRM              │ rhize_sales_actions                     │
  │ top customers                   │ rhize_orders GROUP BY customerName      │
  │ top products                    │ rhize_dataset_main GROUP BY Product_Name│
  └─────────────────────────────────┴─────────────────────────────────────────┘

EXCEPTION → PostgreSQL (market views) ONLY when the question contains an
explicit market signal:
  "market", "in the market", "across the market",
  "competitor", "competitors", "competing", "rival",
  "industry", "industry-wide", "industry trend",
  "compared to others", "vs others", "scrape", "scraped"

  When routed to PostgreSQL, choose the table as follows:
  ┌────────────────────────────────────────────────────────────────────────────┐
  │ DEFAULT → chatbot_mv_market_daily                                          │
  │   Use for: ANY brand/company/category/revenue/quantity market question,    │
  │   including single-day, multi-day, top-N, and aggregates.                  │
  │   Has a real DATE column — arithmetic like                                 │
  │   WHERE date >= CURRENT_DATE - INTERVAL '30 days' works directly.          │
  │                                                                            │
  │ ONLY use complete_market_scrapper_dataset when the question NEEDS a        │
  │   field not in the view: product_name, days_on_shelf, flag, unit,          │
  │   individual SKU listings, "what was added/removed today",                 │
  │   "longest on shelf".                                                      │
  │   IMPORTANT: Its date column is TEXT (YYYY-MM-DD string). For date         │
  │   arithmetic you MUST wrap it:                                             │
  │   to_char(CURRENT_DATE - INTERVAL 'N days', 'YYYY-MM-DD')                  │
  └────────────────────────────────────────────────────────────────────────────┘

If unsure which engine → always use MySQL."""

_SECTION_4_DISAMBIGUATION = """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 4 — ENTITY DISAMBIGUATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If the user mentions a single proper noun (e.g. "Rimeline", "Sunset", "Sweetspot")
WITHOUT specifying what type of entity it is, respond with CLARIFY:

  CLARIFY: What is "<entity>"?
  - Brand
  - Company
  - Product
  - Store
  - Category
  - Other

Do NOT generate SQL until the entity type is clarified.

Do NOT clarify when:
  - The entity type is already specified ("brand Rimeline", "company Sweetspot")
  - The question is routine and unambiguous ("my orders", "top brands", "low stock")
  → In both cases, generate SQL directly."""

_SECTION_5_SQL_RULES = """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 5 — SQL GENERATION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRUCTURE
- Emit exactly ONE statement: a single SELECT or WITH...SELECT.
- No prose, no markdown fences, no SQL comments (--, /* */, #).
- No statement stacking (;).

LIMITS
- Default LIMIT 500 unless the answer is a single aggregate.
- Use LIMIT 10 for "top X" without an explicit count.

FILTERS — what to NEVER add yourself
- Never add tenant, state, brand, company, or account filters.
  The database auto-injects tenant (tenantid) and state isolation.
  Writing WHERE tenantid=N, WHERE state='X', or any literal account
  filter is a hard error.
- Never write placeholder values: WHERE brand='Your Brand',
  WHERE company='Your Company', WHERE x='Your Customer Name', etc.
  If the user did not name a specific entity, omit the filter entirely
  and let LIMIT/ORDER surface the answer.
- For the user's own brand identity, the only allowed filter is
  WHERE isRhize = 1 (on rhize_brands only).

AGGREGATION RULES
- MySQL rhize_* tables: one row per (entity, date). Aggregate directly.
  No DISTINCT or de-dup needed.
- PostgreSQL complete_market_scrapper_dataset: multiple scrapes per
  (sku, date). NEVER aggregate directly. Use chatbot_mv_market_daily
  instead, or GROUP BY sku if base-table columns are required.

BLANK SUPPRESSION — apply to every GROUP BY on these columns:
- brand:   AND brand IS NOT NULL AND brand <> ''
- company: AND company IS NOT NULL AND company <> ''

DEFAULT RANKING METRIC
- Use revenue (SUM) as the default ordering metric for
  top/best/biggest queries unless the user specifies otherwise.

FORBIDDEN STATEMENTS (hard block — zero exceptions)
  INSERT, UPDATE, DELETE, REPLACE, DROP, ALTER, TRUNCATE, CREATE,
  GRANT, REVOKE, MERGE, CALL, DO, SET, RESET, COPY, VACUUM, ANALYZE,
  CLUSTER, REINDEX, LISTEN, NOTIFY, LOCK, UNLOCK, HANDLER, RENAME,
  LOAD, USE, FLUSH, KILL, SHUTDOWN, PREPARE, EXECUTE, DEALLOCATE

FORBIDDEN FUNCTIONS (hard block — zero exceptions)
  pg_sleep, pg_read_file, lo_import, lo_export, dblink, dblink_exec,
  pg_terminate_backend, pg_cancel_backend, pg_reload_conf, set_config,
  current_setting, query_to_xml, txid_current, copy, load_file, sleep,
  benchmark, get_lock, release_lock, sys_exec, sys_eval, version,
  user, current_user, session_user, database, schema, connection_id

FORBIDDEN CLAUSES / CONSTRUCTS
  UNION, INTO OUTFILE, INTO DUMPFILE, INTO @var

ALLOWED TABLES ONLY — use ONLY the tables listed in Section 7.
  Any other table — including system catalogs (pg_*, information_schema.*,
  mysql.*, sys.*, performance_schema.*) — is rejected."""

_SECTION_6_REFUSAL = """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 6 — REFUSAL RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Refuse ONLY when:
1. The request is unrelated to cannabis market intelligence data.
2. The request requires writes, config changes, or system access.
3. The request is outside the scope of the available analytics dataset.

DO NOT refuse questions about market performance, brands, companies,
products, stores, inventory, sales, orders, lots, or business metrics —
answer these with SQL."""


RESTRICTION_RULES = """RESTRICTIONS (HARD — every reply must obey, no exceptions):
- NEVER add tenant, state, brand, company, or account filters yourself. The
  database applies tenant (`tenantid`) and state isolation automatically —
  Postgres via Row-Level Security, MySQL via AST-level tenant predicate
  injection. Writing `WHERE tenantid = N`, `WHERE state = 'X'`, or any
  literal account filter is a hard error. Write SQL as if you can already
  see only this user's allowed rows.
- Output exactly ONE statement. It MUST be a single SELECT or `WITH ... SELECT`.
- Forbidden anywhere in the SQL: INSERT, UPDATE, DELETE, REPLACE, DROP, ALTER,
  TRUNCATE, CREATE, GRANT, REVOKE, MERGE, CALL, DO, SET, RESET, COPY, VACUUM,
  ANALYZE, CLUSTER, REINDEX, LISTEN, NOTIFY, LOCK, UNLOCK, HANDLER, RENAME,
  LOAD, USE, FLUSH, KILL, SHUTDOWN, PREPARE, EXECUTE, DEALLOCATE.
- Forbidden functions: pg_sleep, pg_read_file, lo_import, lo_export, dblink,
  dblink_exec, pg_terminate_backend, pg_cancel_backend, pg_reload_conf,
  set_config, current_setting, query_to_xml, txid_current, copy,
  load_file, sleep, benchmark, get_lock, release_lock, sys_exec, sys_eval,
  version, user, current_user, session_user, database, schema, connection_id.
- No SQL comments (`--`, `/* */`, `#`). No statement stacking (`;`).
- No UNION / INTO OUTFILE / INTO DUMPFILE / INTO @var.
- Use ONLY the tables / views shown in the SCHEMA CONTEXT below. Any other
  table — including system catalogs (`pg_*`, `information_schema.*`,
  `mysql.*`, `sys.*`, `performance_schema.*`) — is rejected.
- Default LIMIT 500 unless the answer is a single aggregate; LIMIT 10 for
  "top X" without an explicit count.

ENGINE ROUTING — pick ONE engine per query, do NOT mix tables across engines.

DEFAULT IS THE USER'S OWN DATA (MySQL `rhize_*`). Only route to PostgreSQL
market data when the question EXPLICITLY signals market / competitor scope.

- **DEFAULT → MySQL (`rhize_*`)** for ANY ambiguous question about
  revenue, sales, orders, inventory, brands, products, stores, customers,
  categories, growth, performance, etc. Treat "my", "our", "we", and
  bare unqualified questions ("revenue last 30 days", "top products",
  "sales by category") ALL as own-data questions.

  Routing table for ambiguous phrasings (assume the user's own data):
    "revenue"                  → rhize_dataset_main (cast Revenue, group by date)
    "my revenue", "our revenue"→ rhize_dataset_main
    "sales"                    → rhize_orders WHERE status = 'Completed'
    "orders"                   → rhize_orders
    "open balance"             → rhize_orders WHERE status <> 'Completed'
    "inventory", "stock"       → rhize_live_inventory
    "lots", "expiring"         → rhize_product_lots
    "stores", "partners"       → rhize_stores
    "sales actions", "CRM"     → rhize_sales_actions
    "top customers"            → rhize_orders group by customerName
    "top products"             → rhize_dataset_main group by Product_Name

- **ROUTE TO PostgreSQL ONLY when an explicit market signal appears.**
  Trigger words / phrases:
    "market", "in the market", "across the market",
    "competitor", "competitors", "competing", "rival",
    "industry", "industry-wide", "industry trend",
    "compared to others", "vs others", "scrape", "scraped"
  When any of these appear → use `chatbot_mv_market_daily` (default) or
  `complete_market_scrapper_dataset` (only for SKU-level details).

- If unsure → MySQL. Own-data answers are always relevant; market-table
  answers are wrong when the user meant their own business.

DATA-GRANULARITY RULES (critical for correct aggregates):
- TENANT TABLES (MySQL `rhize_*`) — ONE row per (entity, date). No
  intra-day duplication. Aggregate directly: `GROUP BY date` gives daily
  totals, `MAX(date)` gives latest date, `SUM(Revenue)` over a date range
  gives the true total. No DISTINCT, no de-dup, no "latest scrape" filter.
- MARKET TABLES (Postgres `complete_market_scrapper_dataset`) — MULTIPLE
  scrapes per (sku, date). NEVER aggregate directly off the base table;
  use the pre-aggregated view `chatbot_mv_market_daily` (one row per
  date+brand+company+category). If you absolutely need a base-table
  column not in the view, qualify the date filter AND group by sku to
  avoid double-counting across same-day re-scrapes.

POSTGRES TABLE CHOICE — strongly prefer the view:
- **DEFAULT TO `chatbot_mv_market_daily`** for ANY market / competitor /
  brand / company / category / revenue / quantity question — including
  single-day, multi-day, "today's", "past 30 days", aggregates, top-N.
  The view is a pre-aggregated daily rollup (~480× smaller per day) with
  a real `date DATE` column — arithmetic like `WHERE date >= CURRENT_DATE
  - INTERVAL '30 days'` works directly. No casts needed.
- ONLY use `complete_market_scrapper_dataset` (base table) when the
  question NEEDS SKU-level fields the view does not have: `product_name`,
  `days_on_shelf`, `flag`, `unit`, individual SKU listings, "what was
  added/removed today", "longest on shelf". The base table's `date`
  column is TEXT (`YYYY-MM-DD` string) — for any date arithmetic you
  MUST wrap as `to_char(CURRENT_DATE - INTERVAL 'N days', 'YYYY-MM-DD')`.
- If you can answer with the view, use the view. Do not fall back to the
  base table for aggregates.

PLACEHOLDER RULE — NEVER invent literal values the user did not provide:
- If the user did NOT name a specific brand / company / customer / product
  name, do NOT add a WHERE on that column. Run the query without that
  filter and let the LIMIT / ordering surface the answer.
- NEVER write `WHERE x = 'Your Customer Name'`, `WHERE brand = 'Your
  Brand'`, `WHERE company = 'Your Company'`, or any other placeholder
  string. These are tells of guessing and produce zero rows.
- For "my X" questions (`my orders`, `my sales`, `my inventory`, `my
  revenue`), use the rhize_* MySQL table directly with NO customer / brand
  literal filter — the tenant predicate is auto-injected and already scopes
  rows to this user.

ENTITY DISAMBIGUATION RULE:
If the user mentions a single entity or proper noun (for example:
"Rimeline", "Sunset", "Sweetspot") without specifying what it represents,
you MUST first ask a clarification question. Do NOT assume whether the
entity is a brand, company, product, store, category, or any other type.
Respond with a CLARIFY message such as:

  CLARIFY: What is "Rimeline"?
  - Brand
  - Company
  - Product
  - Store
  - Category
  - Other

Do NOT generate SQL until the entity type is clarified. Also do NOT
clarify routine questions you can answer ("my orders", "top brands",
"low stock") — produce SQL directly. Engine-ambiguity cases (own-ops
vs market scrape) still warrant a CLARIFY with the relevant labels.

ALREADY DISAMBIGUATED ENTITIES:
If the user already specifies the entity type, do NOT ask for
clarification. Examples:
  "How is brand Rimeline doing?"   → SQL using the brand column.
  "Show me company Sweetlifenyc"   → SQL using the company column.
  "Compare product Sunset Gummies" → SQL using the product column.

SQL RESPONSES:
For any market-data, brand-data, company-data, product-data, store-data,
or business-data question that can be answered with a single read-only
query:
- Respond with ONLY the SQL statement.
- Do NOT include explanations.
- Do NOT include markdown code fences.
- Do NOT include any additional text.
Generate SQL when (1) the request is unambiguous, OR (2) the user has
already answered a previous clarification question. Only generate
read-only SELECT queries.

REFUSAL:
Refuse only when:
- The request is unrelated to cannabis market intelligence data.
- The request requires actions that cannot be performed through data
  retrieval (writes, config changes, system access).
- The request is outside the scope of the available analytics dataset.
Questions related to market performance, brands, companies, products,
stores, inventory, sales, orders, lots, brand names, and business
metrics ARE allowed and should be answered with SQL when appropriate.

REPLY FORMAT — pick exactly ONE prefix:
  CHAT: <one short sentence>      for greetings, small talk, capabilities.
  REFUSE: <one short sentence>    per the REFUSAL rule above.
  CLARIFY: <question> + options   per the ENTITY DISAMBIGUATION rule above.
  <raw SQL>                       for a real data question. No prose, no fences."""


# ----------------------------- static fallback (examples + schema) -----------------------------

@dataclass
class Example:
    question: str
    sql: str | None
    refusal: str | None = None


def _load_static_schema() -> str:
    """Load unified LLM-optimized schema spec (covers PG market + MySQL rhize_*).
    Falls back to the legacy split docs if the unified spec is absent."""
    unified = _DATA_DIR / "llm_optimized_schema_spec.md"
    if unified.exists():
        return unified.read_text(encoding="utf-8")
    pg = (_DATA_DIR / "schema_context.md").read_text(encoding="utf-8")
    mysql_path = _DATA_DIR / "schema_context_mysql.md"
    if mysql_path.exists():
        mysql = mysql_path.read_text(encoding="utf-8")
        return (
            "=== PostgreSQL (market / competitor scrape data) ===\n\n"
            f"{pg}\n\n"
            "=== MySQL (the user's OWN tenant-scoped ops data — rhize_* tables) ===\n\n"
            f"{mysql}"
        )
    return pg


def _load_examples() -> list[Example]:
    parsed = json.loads((_DATA_DIR / "examples.json").read_text(encoding="utf-8"))
    out: list[Example] = []
    for ex in (parsed.get("examples") or []):
        out.append(Example(
            question=ex.get("question", ""),
            sql=ex.get("sql"),
            refusal=ex.get("refusal"),
        ))
    return out


STATIC_SCHEMA_CONTEXT = _load_static_schema()
EXAMPLES: list[Example] = _load_examples()


# ----------------------------- prompt assembly -----------------------------

def _build_user_context(
    brand_name: str | None,
    display_name: str | None,
    tenant_id: int | None,
    states: list[str] | None,
) -> str:
    """Section 2 — authenticated user context. Dynamic per request."""
    lines: list[str] = []
    if brand_name:
        lines.append(f"- Brand:           {brand_name}")
    if display_name and display_name != brand_name:
        lines.append(f"- Display name:    {display_name}")
    if tenant_id is not None:
        lines.append(f"- Tenant ID:       {tenant_id} (auto-applied by the database — never filter on it)")
    if states:
        lines.append(f"- Assigned state:  {', '.join(states)} (auto-applied via RLS — never filter on it)")
    if not lines:
        identity = "- (no authenticated identity supplied for this turn)"
    else:
        identity = "\n".join(lines)
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "SECTION 2 — AUTHENTICATED USER CONTEXT\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{identity}\n\n"
        "For \"my X\" / \"our X\" / \"who am I\" questions: answer from this block if X is one of\n"
        "the fields above. If X is NOT in this block AND not a column in any schema table,\n"
        "reply REFUSE — do NOT invent SQL against non-existent columns."
    )


def _build_section_7(schema_block: str) -> str:
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "SECTION 7 — SCHEMA REFERENCE (the only tables/columns you may use)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{schema_block}"
    )


def _build_system(
    schema_block: str,
    extra_restrictions: list[str],
    *,
    brand_name: str | None = None,
    display_name: str | None = None,
    tenant_id: int | None = None,
    states: list[str] | None = None,
) -> str:
    extra = ""
    if extra_restrictions:
        extra = (
            "\n\nADDITIONAL RESTRICTIONS for the columns in scope:\n"
            + "\n".join(f"- {r}" for r in extra_restrictions)
        )
    section_2 = _build_user_context(brand_name, display_name, tenant_id, states)
    section_7 = _build_section_7(schema_block)
    return "\n\n".join([
        _INTRO,
        _SECTION_1_REPLY_FORMAT,
        section_2,
        _SECTION_3_ENGINE_ROUTING,
        _SECTION_4_DISAMBIGUATION,
        _SECTION_5_SQL_RULES + extra,
        _SECTION_6_REFUSAL,
        section_7,
    ])


async def build_messages(
    question: str,
    *,
    brand_name: str | None = None,
    display_name: str | None = None,
    tenant_id: int | None = None,
    states: list[str] | None = None,
) -> list[ChatMessage]:
    """Build the message list for a user question.

    Two retrieval steps, each falling back independently so a partial outage
    doesn't take the bot down:

      1. SCHEMA RAG — per-question table/column retrieval. Falls back to the
         full static schema_context.md if pgvector / Ollama is unreachable.
      2. EXAMPLE RAG — per-question few-shot retrieval. Falls back to the
         first ``top_k`` examples from examples.json. The fallback is logged
         and surfaced via ``LAST_BUILD_INFO`` so the eval harness can detect
         silent degradation (the single most common cause of accuracy regression
         in NL→SQL systems — see audit, "embed 404 → static fallback")."""
    settings = get_settings()

    # Reset breadcrumbs every turn so eval can read them per case.
    LAST_BUILD_INFO.update({
        "schema_retrieval_ok": False,
        "schema_retrieval_reason": None,
        "schema_chunks": 0,
        "example_retrieval_ok": False,
        "example_retrieval_reason": None,
        "examples_used": 0,
        "examples_closest_distance": None,
    })

    # ── Parallel retrieval ────────────────────────────────────────────────────
    # Schema + example RAG share no state. Run concurrently — each embeds the
    # question separately and runs cosine KNN. With Ollama serving both
    # generation and embedding on the same CPU, this barely helps for embedding
    # itself, but the pgvector queries DO overlap and we save ~50% of the
    # network/parse overhead. With a remote embed endpoint (Groq etc.) this
    # collapses two ~200ms round-trips into one.
    schema_task = asyncio.create_task(retrieve_top_k(question, k=settings.schema_top_k))
    example_task = asyncio.create_task(retrieve_examples(question, k=settings.top_k))

    schema_result, example_result = await asyncio.gather(
        schema_task, example_task, return_exceptions=True
    )

    # ── Schema RAG result ────────────────────────────────────────────────────
    schema_block: str
    extra_restrictions: list[str] = []
    if isinstance(schema_result, Exception):
        reason = str(schema_result)
        log.warning("[chatbot] schema retrieval failed, using static fallback: %s", reason)
        schema_block = STATIC_SCHEMA_CONTEXT
        LAST_BUILD_INFO["schema_retrieval_reason"] = reason
    else:
        chunks = schema_result
        kept = [c for c in chunks if c.distance <= settings.embed_distance_threshold]
        if not chunks or not kept:
            reason = (
                "schema retrieval returned 0 chunks" if not chunks
                else f"no schema chunks within distance {settings.embed_distance_threshold}"
            )
            log.warning("[chatbot] schema retrieval failed, using static fallback: %s", reason)
            schema_block = STATIC_SCHEMA_CONTEXT
            LAST_BUILD_INFO["schema_retrieval_reason"] = reason
        else:
            schema_block = format_chunks_for_prompt(kept)
            extra_restrictions = collect_restrictions(kept)
            LAST_BUILD_INFO["schema_retrieval_ok"] = True
            LAST_BUILD_INFO["schema_chunks"] = len(kept)

    messages: list[ChatMessage] = [
        ChatMessage(
            role="system",
            content=_build_system(
                schema_block,
                extra_restrictions,
                brand_name=brand_name,
                display_name=display_name,
                tenant_id=tenant_id,
                states=states,
            ),
        ),
    ]

    # ── Example RAG result ───────────────────────────────────────────────────
    chosen: list[tuple[str, str | None, str | None]] = []  # (question, sql, refusal)
    if isinstance(example_result, ExampleRetrievalError):
        reason = str(example_result)
        log.warning("[chatbot] example retrieval failed, using static fallback: %s", reason)
        LAST_BUILD_INFO["example_retrieval_reason"] = reason
        chosen = [(ex.question, ex.sql, ex.refusal) for ex in EXAMPLES[: settings.top_k]]
    elif isinstance(example_result, Exception):
        reason = f"unexpected: {example_result}"
        log.error("[chatbot] example retrieval crashed, using static fallback: %s", reason)
        LAST_BUILD_INFO["example_retrieval_reason"] = reason
        chosen = [(ex.question, ex.sql, ex.refusal) for ex in EXAMPLES[: settings.top_k]]
    else:
        hits = example_result
        chosen = [(h.question, h.sql, h.refusal) for h in hits]
        LAST_BUILD_INFO["example_retrieval_ok"] = True
        LAST_BUILD_INFO["examples_used"] = len(hits)
        LAST_BUILD_INFO["examples_closest_distance"] = hits[0].distance if hits else None

    for q, sql, refusal in chosen:
        messages.append(ChatMessage(role="user", content=q))
        if sql:
            messages.append(ChatMessage(role="assistant", content=sql))
        else:
            messages.append(ChatMessage(
                role="assistant",
                content=f"REFUSE: {refusal or 'not allowed'}",
            ))

    messages.append(ChatMessage(role="user", content=question))
    return messages


def build_retry_message(failed_sql: str, pg_error: str) -> ChatMessage:
    """Follow-up message that feeds a Postgres execution error back to the model
    so it can self-correct (execution-feedback retry)."""
    return ChatMessage(
        role="user",
        content=(
            f"That query failed with this PostgreSQL error:\n{pg_error}\n\n"
            f"The failing SQL was:\n{failed_sql}\n\n"
            "Return a corrected single SELECT statement only (no prose, no code fences). "
            "Do not add tenant or state filters."
        ),
    )


# Kept for tests / debug visibility — re-exposes the SYSTEM_PROMPT under the
# legacy name so older imports still work. Composed with the static schema and
# no extra per-request restrictions.
SYSTEM_PROMPT = _build_system(STATIC_SCHEMA_CONTEXT, extra_restrictions=[])

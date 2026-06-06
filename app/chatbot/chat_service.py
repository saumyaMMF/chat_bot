"""Orchestrator for the NL->SQL chatbot.

Flow: question -> model -> parse -> Gate C guard -> Gate D limit ->
      readonly run (Gate A/B) -> on DB error, feed it back and retry (<=2).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from app.chatbot.llm_client import ChatMessage, LLMError, chat_complete
from app.chatbot.normalize_question import normalize_question
from app.chatbot.prompt_builder import build_messages, build_retry_message
from app.chatbot.answer_formatter import format_answer, is_terminal_answer
from app.chatbot.engine_router import route_engine
from app.chatbot.fast_path_store import retrieve_match as fast_path_match
from app.chatbot.readonly_db import RunContext, run_readonly
from app.chatbot.readonly_db_mysql import RunMysqlContext, run_readonly_mysql
from app.chatbot.sql_guard import enforce_limit, validate_sql
from app.chatbot.sql_guard_mysql import enforce_limit_mysql, validate_mysql_sql
from app.chatbot.turn_logger import TurnRecord, log_turn
from app.config import get_settings
import datetime as _dt
import time as _time

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 3  # 1 initial + 2 execution-feedback retries.

_GREETING_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"^\s*(hi|hello|hey|yo|hiya|howdy|good (morning|afternoon|evening))[\s!.?]*$", re.I),
        "Hi! I can help you explore your cannabis market data — competitor brands, prices, categories, and trends. What would you like to know?",
    ),
    (
        re.compile(r"^\s*(thanks|thank you|thx|ty|cheers|appreciate it)[\s!.?]*$", re.I),
        "You're welcome! Ask me anything about your market data.",
    ),
    (
        re.compile(r"^\s*(help|what can you do|what do you do|how does this work|capabilities)[\s!.?]*$", re.I),
        "I answer questions about your competitor/market data — top brands, pricing, categories, what's newly listed or removed, and trends over time.",
    ),
    (
        re.compile(r"^\s*(bye|goodbye|see ya|see you|later)[\s!.?]*$", re.I),
        "Bye! Come back any time for more market data.",
    ),
]

_BRAND_NAME_RX = re.compile(
    r"^\s*(what(?:'s| is)?\s+|tell\s+(?:me\s+)?)?(my\s+(brand|company|business)\s*(name)?|who\s+am\s+i)[\s!.?]*$",
    re.I,
)
_DISPLAY_NAME_RX = re.compile(
    r"^\s*(what(?:'s| is)?\s+|tell\s+(?:me\s+)?)?my\s+(account|display|tenant)\s*(name)?[\s!.?]*$",
    re.I,
)

_INFRA_ERROR_RX = re.compile(
    r"DATABASE_URL_RO|CHATBOT_MYSQL_RO_URL|ECONNREFUSED|ENOTFOUND|getaddrinfo"
    r"|connect ETIMEDOUT|password authentication|too many connections"
    r"|terminating connection|access denied|er_access_denied|er_dbaccess_denied"
    r"|can't connect to mysql|lost connection",
    re.I,
)

_SQL_FENCE_RX = re.compile(r"```(?:sql)?\s*([\s\S]*?)```", re.I)
_CHAT_PREFIX_RX = re.compile(r"^CHAT:\s*([\s\S]*)", re.I)
_REFUSE_PREFIX_RX = re.compile(r"REFUSE:\s*([\s\S]*)", re.I)
_SQL_START_RX = re.compile(r"^\s*\(*\s*(select|with)\b", re.I)
_TABLE_TYPO_RX = re.compile(r"complete_market_scrap+er_dataset", re.I)

# Explicit market-signal detection. If NONE of these appear in the question,
# the router MUST keep the query on MySQL (`rhize_*`). PG routing for an
# own-data question silently shows the user competitor data — a correctness bug.
_MARKET_SIGNAL_RX = re.compile(
    r"\b("
    r"market|markets|in the market|across the market|"
    r"competitor|competitors|competing|rival|rivals|"
    r"industry|industry-wide|industry trend|"
    r"compared to others|vs others|vs\.? others|versus others|"
    r"scrape|scraped|scraping|"
    r"other brands|other companies|other stores|other products"
    r")\b",
    re.I,
)


def _has_market_signal(question: str) -> bool:
    return bool(_MARKET_SIGNAL_RX.search(question or ""))


def _match_greeting(question: str) -> str | None:
    for rx, reply in _GREETING_PATTERNS:
        if rx.search(question):
            return reply
    return None


def _match_identity(question: str, brand_name: str | None, display_name: str | None) -> str | None:
    if _BRAND_NAME_RX.search(question) and brand_name:
        return f"Your brand is **{brand_name}**."
    if _DISPLAY_NAME_RX.search(question) and display_name:
        return f"Your account is **{display_name}**."
    return None


def canonicalize_sql(sql: str) -> str:
    """Fix common model misspellings of the (oddly-named) market table before
    the guard sees them."""
    return _TABLE_TYPO_RX.sub("complete_market_scrapper_dataset", sql)


# ── Free-text equality → ILIKE rewrite ───────────────────────────────────────
#
# Source data for `brand` and `company` columns has mixed casing
# (`ZIZZLE` vs `Zizzle`). The model is told to use case-insensitive
# partial match in the prompt, but small models keep emitting exact
# `WHERE brand = 'X'` which returns 0 rows. Rewrite the AST-validated
# SELECT to swap exact equality for `lower(col) LIKE lower('%X%')`.
#
# Deliberately string-level (not AST) because validateSql is the parser
# path — this runs AFTER the guard accepts the query, narrowing the
# rewrite surface to known-safe SELECTs. Single-quote escaping is
# preserved: `''` inside the literal stays `''`.
_FREE_TEXT_COLS = ("brand", "company")


def rewrite_eq_to_ilike_on_text_cols(sql: str) -> str:
    """Rewrite ``<col> = '<lit>'`` to ``lower(<col>) LIKE lower('%<lit>%')``
    for the columns in ``_FREE_TEXT_COLS``. Numeric/date equality is
    unaffected (only quoted-string literals match)."""
    out = sql
    for col in _FREE_TEXT_COLS:
        # `<alias?.>col = '<value-with-''-escape>'`, case-insensitive on col,
        # whitespace tolerant around `=`.
        rx = re.compile(
            rf"(\b(?:[A-Za-z_][A-Za-z0-9_]*\.)?)({col})(\s*=\s*)'((?:''|[^'])*)'",
            re.I,
        )

        def _sub(m: re.Match[str]) -> str:
            alias, c, _eq, value = m.group(1), m.group(2), m.group(3), m.group(4)
            stripped = re.sub(r"^%+|%+$", "", value)  # drop pre-escaped wildcards
            return f"lower({alias}{c}) LIKE lower('%{stripped}%')"

        out = rx.sub(_sub, out)
    return out


# ── Disambiguated-entity fast-path ───────────────────────────────────────────
#
# When the user (or a CLARIFY chip click) sends a message that explicitly
# names the column type alongside the entity ("brand X", "company X",
# "store X", "category X"), bypass the LLM and generate SQL deterministically.
# Small models loop CLARIFY even after explicit disambiguation; this fast-path
# sidesteps that and avoids a 40s round-trip.

_ENTITY_PATTERN = re.compile(
    r"\b(brand|company|store|retailer|dispensary|category)\s+[\"']?([A-Za-z][A-Za-z0-9_'-]*)",
    re.I,
)

_CATEGORY_ENUM = frozenset(
    {"flower", "preroll", "vape", "concentrate", "edible", "other"}
)

# Words that look like an entity to the regex but are NOT entity names. Without
# this list, "which brand performing well" gets parsed as
# (kind=brand, entity=performing) and the bot emits SQL filtering on a verb.
# False negatives (one extra LLM round-trip) are cheaper than false positives
# (wrong-column SQL).
_ENTITY_STOPWORDS = frozenset({
    # verb-ish
    "performing", "doing", "going", "selling", "showing", "making", "getting",
    "looking", "working", "running", "leading", "winning", "losing", "growing",
    "trending", "falling", "rising", "driving", "beating", "topping",
    # time / determiners
    "today", "yesterday", "tomorrow", "this", "last", "next", "now",
    "currently", "recently", "lately", "previously",
    # generic
    "data", "info", "information", "name", "names", "list", "all", "any",
    "some", "one", "two", "three", "each", "every", "most", "least",
    # evaluative adjectives
    "good", "bad", "well", "better", "best", "worst", "top", "bottom",
    "high", "low", "big", "small", "large", "tiny",
    # question / aux words
    "which", "what", "who", "where", "when", "how", "why",
    "is", "are", "was", "were", "be", "been", "has", "have", "had",
})


@dataclass
class DisambiguatedEntity:
    column: str  # 'brand' | 'company' | 'category_norm'
    value: str
    is_category: bool


def detect_disambiguated_entity(question: str) -> DisambiguatedEntity | None:
    """Return a disambiguated entity hit if the question explicitly names
    column-type + value, else None (LLM path handles the question)."""
    m = _ENTITY_PATTERN.search(question)
    if not m:
        return None
    kind = m.group(1).lower()
    raw = m.group(2).strip()
    if not raw or raw.lower() in _ENTITY_STOPWORDS:
        return None
    if kind == "brand":
        return DisambiguatedEntity(column="brand", value=raw, is_category=False)
    if kind in ("company", "store", "retailer", "dispensary"):
        return DisambiguatedEntity(column="company", value=raw, is_category=False)
    if kind == "category":
        v = raw.lower()
        if v not in _CATEGORY_ENUM:
            return None  # unknown category → let LLM / CLARIFY handle
        canonical = "PreRoll" if v == "preroll" else v.capitalize()
        return DisambiguatedEntity(column="category_norm", value=canonical, is_category=True)
    return None


def build_disambiguated_sql(entity: DisambiguatedEntity) -> str:
    """Generate the deterministic SQL for a disambiguated entity. Hits the
    pre-aggregated daily view so a fast-path response stays under 1s even
    on the local CPU LLM (no LLM call) + a single MV scan."""
    safe = entity.value.replace("'", "''")
    if entity.is_category:
        return (
            "SELECT category_norm, "
            "SUM(revenue) AS total_revenue, "
            "SUM(quantity) AS total_quantity "
            "FROM chatbot_mv_market_daily "
            f"WHERE category_norm = '{safe}' "
            "AND date >= CURRENT_DATE - INTERVAL '7 days' "
            "GROUP BY category_norm "
            "ORDER BY total_revenue DESC LIMIT 10"
        )
    col = entity.column
    return (
        f"SELECT {col}, "
        "SUM(revenue) AS total_revenue, "
        "SUM(quantity) AS total_quantity "
        "FROM chatbot_mv_market_daily "
        f"WHERE lower({col}) LIKE lower('%{safe}%') "
        "AND date >= CURRENT_DATE - INTERVAL '30 days' "
        f"AND {col} <> '' "
        f"GROUP BY {col} "
        "ORDER BY total_revenue DESC LIMIT 10"
    )


@dataclass
class ChatInput:
    tenant_id: int
    states: list[str]
    question: str
    brand_name: str | None = None
    display_name: str | None = None


ResultKind = Literal["result", "chat", "refusal", "clarify", "error"]


@dataclass
class ClarifyOption:
    kind: str
    value: str


@dataclass
class ChatResult:
    kind: ResultKind
    message: str = ""
    sql: str | None = None
    rows: list[dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    options: list[ClarifyOption] = field(default_factory=list)


@dataclass
class ExtractedReply:
    chat: str | None = None
    refusal: str | None = None
    clarify_message: str | None = None
    clarify_options: list[ClarifyOption] = field(default_factory=list)
    sql: str | None = None


_CLARIFY_PREFIX_RX = re.compile(r"^CLARIFY:\s*([\s\S]*)", re.I)
# Matches `- KIND: value`, `KIND: value`, `* KIND: value`. KIND must be an
# uppercase identifier so we don't pick up a SQL `WHERE x = 'y':` line by
# mistake.
_CLARIFY_OPTION_RX = re.compile(r"^\s*[-•*]?\s*([A-Z][A-Z0-9_]*)\s*:\s*(.+?)\s*$")


def extract_sql(reply: str) -> ExtractedReply:
    """Classify a model reply.

    Returns an ``ExtractedReply`` with at most one of ``chat`` / ``refusal`` /
    ``clarify_*`` / ``sql`` populated. Prose without a known prefix is treated
    as chat so the user sees something rather than the generic error.
    """
    trimmed = reply.strip()

    m = _CHAT_PREFIX_RX.match(trimmed)
    if m:
        msg = m.group(1).strip() or "Hi! How can I help with your market data?"
        return ExtractedReply(chat=msg)

    m = _REFUSE_PREFIX_RX.search(trimmed)
    if m:
        msg = m.group(1).strip() or "I can't help with that one."
        return ExtractedReply(refusal=msg)

    m = _CLARIFY_PREFIX_RX.match(trimmed)
    if m:
        body = m.group(1).strip()
        lines = body.splitlines()
        options: list[ClarifyOption] = []
        leading: list[str] = []
        for line in lines:
            opt = _CLARIFY_OPTION_RX.match(line)
            if opt:
                options.append(ClarifyOption(kind=opt.group(1), value=opt.group(2).strip()))
            elif not options:
                leading.append(line.strip())
            # Lines after the first option are option-only; drop stray text.
        message = " ".join(s for s in leading if s).strip() or "Which did you mean?"
        return ExtractedReply(clarify_message=message, clarify_options=options)

    sql = trimmed
    fence = _SQL_FENCE_RX.search(sql)
    if fence:
        sql = fence.group(1).strip()
    sql = sql.strip()

    if sql and not _SQL_START_RX.search(sql):
        return ExtractedReply(chat=sql)  # treat prose as chat

    return ExtractedReply(sql=sql or None)


def _drop_blank_dimension_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop rows whose leading text dimension is null/blank. Numeric-first rows
    are returned untouched."""
    if not rows:
        return rows
    first_key = next(iter(rows[0].keys()), None)
    if not first_key:
        return rows
    sample = None
    for r in rows:
        v = r.get(first_key)
        if v is not None:
            sample = v
            break
    if isinstance(sample, (int, float)):
        return rows
    return [r for r in rows if r.get(first_key) is not None and str(r.get(first_key)).strip() != ""]


async def run_chat(input: ChatInput) -> ChatResult:
    settings = get_settings()
    started_at = _time.perf_counter()
    started_iso = _dt.datetime.now().isoformat()
    question = normalize_question(input.question)

    def _log(
        result: ChatResult,
        fast_path: str,
        *,
        engine: str | None = None,
        sql_llm: str | None = None,
        sql_final: str | None = None,
        attempts: int | None = None,
        guard_reason: str | None = None,
        error_message: str | None = None,
    ) -> ChatResult:
        try:
            log_turn(TurnRecord(
                ts=started_iso,
                tenant_id=input.tenant_id,
                question_raw=input.question,
                question_norm=question if question != input.question else None,
                fast_path=fast_path,
                kind=result.kind,
                latency_ms=int((_time.perf_counter() - started_at) * 1000),
                engine=engine,
                sql_llm=sql_llm,
                sql_final=sql_final or result.sql,
                row_count=result.row_count if result.kind == "result" else None,
                attempts=attempts,
                guard_reason=guard_reason,
                clarify_option_count=len(result.options) if result.kind == "clarify" else None,
                error_message=error_message or (result.message if result.kind == "error" else None),
            ))
        except Exception as exc:  # never block chat
            log.warning("[chat] turn log failed: %s", exc)
        return result

    greeting = _match_greeting(question)
    if greeting:
        return _log(ChatResult(kind="chat", message=greeting), "greeting")

    identity = _match_identity(question, input.brand_name, input.display_name)
    if identity:
        return _log(ChatResult(kind="chat", message=identity), "identity")

    # Disambiguated-entity fast-path. "brand X" / "company X" / "store X" /
    # "category X" → deterministic SQL, no LLM round-trip. Saves ~40s/turn
    # on the local CPU model and prevents small models from looping CLARIFY
    # after explicit disambiguation.
    entity = detect_disambiguated_entity(question)
    if entity:
        sql_template = build_disambiguated_sql(entity)
        # Goes through the same Gate C → Gate D path the LLM SQL does so we
        # never bypass the guard / limit cap.
        verdict = validate_sql(sql_template)
        if verdict.ok:
            final_sql = rewrite_eq_to_ilike_on_text_cols(
                enforce_limit(verdict.sql, max_rows=settings.row_limit)
            )
            log.info("[chat] fast-path (%s=%s): %s",
                     entity.column, entity.value,
                     re.sub(r"\s+", " ", final_sql)[:300])
            try:
                result = await run_readonly(
                    final_sql,
                    RunContext(
                        tenant_id=input.tenant_id,
                        states=input.states,
                        timeout_ms=settings.statement_timeout_ms,
                    ),
                )
                clean = _drop_blank_dimension_rows(result.rows)
                ans = format_answer(input.question, final_sql, clean)
                terminal = is_terminal_answer(input.question, clean)
                return _log(
                    ChatResult(
                        kind="chat" if terminal else "result",
                        message=ans,
                        sql=None if terminal else final_sql,
                        rows=[] if terminal else clean,
                        row_count=0 if terminal else len(clean),
                    ),
                    "disambig",
                    engine="pg",
                    sql_final=final_sql,
                )
            except Exception as exc:
                # Fast-path execution failed — fall through to the LLM path
                # so the user still gets an answer attempt.
                log.warning("[chat] fast-path execution failed, falling through: %s", exc)

    # Fuzzy fast-path. Embed the user question, KNN against the curated
    # Q->SQL catalog (chatbot_fast_path_embeddings). If we hit a literal
    # pair (no template placeholders) within the distance threshold, run
    # the cached SQL directly — LLM is skipped. Templated pairs (params
    # like {N}/{WINDOW}/{BRAND}) still embed and may surface as nearest
    # neighbours, but they fall through to the LLM until a slot-filler
    # is wired up. Same Gate C (validate_sql) + Gate D (limit/timeout)
    # apply to cached SQL, plus RLS (PG) / tenantid scope (MySQL).
    if settings.fast_path_enabled:
        fp_dialect = "postgres" if _has_market_signal(question) else "mysql"
        log.info("[chat] ▶ stage=fast-path-lookup dialect=%s threshold=%.3f",
                 fp_dialect, settings.fast_path_distance_threshold)
        t_fp = _time.perf_counter()
        try:
            hit = await fast_path_match(
                question,
                distance_threshold=settings.fast_path_distance_threshold,
                dialect=fp_dialect,
            )
        except Exception as exc:
            log.warning("[chat] fast-path lookup error, falling through: %s", exc)
            hit = None
        log.info("[chat] ✔ stage=fast-path-lookup done in %.2fs hit=%s",
                 _time.perf_counter() - t_fp,
                 f"{hit.id}@d={hit.distance:.4f}" if hit else "MISS")
        if hit is not None and hit.is_literal:
            log.info(
                "[chat] fast-path hit: id=%s distance=%.4f dialect=%s",
                hit.id, hit.distance, hit.dialect,
            )
            if hit.refusal:
                return _log(
                    ChatResult(kind="refusal", message=hit.refusal),
                    f"cache:{hit.id}",
                )
            cached_sql = hit.sql or ""
            try:
                if hit.dialect == "mysql":
                    verdict = validate_mysql_sql(cached_sql, input.tenant_id)
                    if not verdict.ok:
                        raise RuntimeError(f"cached SQL rejected: {verdict.reason}")
                    final_sql = enforce_limit_mysql(verdict.sql, max_rows=settings.row_limit)
                    result = await run_readonly_mysql(
                        final_sql,
                        RunMysqlContext(timeout_ms=settings.statement_timeout_ms),
                    )
                    engine = "mysql"
                else:
                    verdict = validate_sql(cached_sql)
                    if not verdict.ok:
                        raise RuntimeError(f"cached SQL rejected: {verdict.reason}")
                    final_sql = rewrite_eq_to_ilike_on_text_cols(
                        enforce_limit(verdict.sql, max_rows=settings.row_limit)
                    )
                    result = await run_readonly(
                        final_sql,
                        RunContext(
                            tenant_id=input.tenant_id,
                            states=input.states,
                            timeout_ms=settings.statement_timeout_ms,
                        ),
                    )
                    engine = "pg"
                clean = _drop_blank_dimension_rows(result.rows)
                ans = format_answer(input.question, final_sql, clean)
                terminal = is_terminal_answer(input.question, clean)
                return _log(
                    ChatResult(
                        kind="chat" if terminal else "result",
                        message=ans,
                        sql=None if terminal else final_sql,
                        rows=[] if terminal else clean,
                        row_count=0 if terminal else len(clean),
                    ),
                    f"cache:{hit.id}",
                    engine=engine,
                    sql_final=final_sql,
                )
            except Exception as exc:
                log.warning("[chat] fast-path execution failed, falling through: %s", exc)
        elif hit is not None:
            log.info(
                "[chat] fast-path nearest=%s d=%.4f is templated — falling through",
                hit.id, hit.distance,
            )

    log.info("[chat] ▶ stage=rag-retrieval start")
    t0 = _time.perf_counter()
    messages: list[ChatMessage] = await build_messages(
        question,
        brand_name=input.brand_name,
        display_name=input.display_name,
        tenant_id=input.tenant_id,
        states=input.states,
    )
    log.info("[chat] ✔ stage=rag-retrieval done in %.2fs (messages=%d)",
             _time.perf_counter() - t0, len(messages))
    last_sql: str | None = None
    last_error = "The query could not be generated or executed."

    for attempt in range(1, MAX_ATTEMPTS + 1):
        log.info("[chat] ▶ stage=llm-call attempt=%d start", attempt)
        t_llm = _time.perf_counter()
        try:
            reply = await chat_complete(messages)
            log.info("[chat] ✔ stage=llm-call attempt=%d done in %.2fs (chars=%d)",
                     attempt, _time.perf_counter() - t_llm, len(reply or ""))
        except LLMError as exc:
            log.error("[chat] LLM error: %s", exc)
            return _log(
                ChatResult(
                    kind="error",
                    message="The assistant is temporarily unavailable. Please try again shortly.",
                ),
                "none",
                attempts=attempt,
                error_message=str(exc),
            )

        parsed = extract_sql(reply)
        if parsed.chat:
            return _log(ChatResult(kind="chat", message=parsed.chat), "none", attempts=attempt)
        if parsed.refusal:
            return _log(ChatResult(kind="refusal", message=parsed.refusal), "none", attempts=attempt)
        if parsed.clarify_message:
            return _log(
                ChatResult(
                    kind="clarify",
                    message=parsed.clarify_message,
                    options=parsed.clarify_options,
                ),
                "none",
                attempts=attempt,
            )

        sql = parsed.sql
        if sql:
            sql = canonicalize_sql(sql)
        if not sql:
            last_error = "The model returned no SQL."
            messages.append(ChatMessage(role="assistant", content=reply))
            messages.append(build_retry_message("(no SQL produced)", last_error))
            continue

        route = route_engine(sql)
        if not route.ok:
            last_sql = sql
            last_error = route.reason
            messages.append(ChatMessage(role="assistant", content=sql))
            messages.append(build_retry_message(sql, f"Rejected by safety check: {route.reason}"))
            continue

        # HARD ROUTING GUARD — block PG when the question carries no market
        # signal. Feed the failure back so the model re-emits using rhize_*.
        if route.engine == "pg" and not _has_market_signal(input.question):
            last_sql = sql
            last_error = (
                "Routed to PostgreSQL market tables, but the question carries no "
                "market/competitor/industry signal. Re-emit using the user's own "
                "MySQL `rhize_*` tables only."
            )
            log.info("[chat] rejecting PG route — no market signal in question")
            messages.append(ChatMessage(role="assistant", content=sql))
            messages.append(build_retry_message(sql, last_error))
            continue

        if route.engine == "pg":
            verdict = validate_sql(sql)
            if not verdict.ok:
                last_sql = sql
                last_error = verdict.reason
                messages.append(ChatMessage(role="assistant", content=sql))
                messages.append(build_retry_message(sql, f"Rejected by safety check: {verdict.reason}"))
                continue
            final_sql = rewrite_eq_to_ilike_on_text_cols(
                enforce_limit(verdict.sql, max_rows=settings.row_limit)
            )
        else:
            verdict = validate_mysql_sql(sql, input.tenant_id)
            if not verdict.ok:
                last_sql = sql
                last_error = verdict.reason
                messages.append(ChatMessage(role="assistant", content=sql))
                messages.append(build_retry_message(sql, f"Rejected by safety check: {verdict.reason}"))
                continue
            final_sql = enforce_limit_mysql(verdict.sql, max_rows=settings.row_limit)

        last_sql = final_sql

        log.info("[chat] question: %s", input.question)
        log.info("[chat] engine:   %s", route.engine)
        log.info("[chat] SQL: %s", re.sub(r"\s+", " ", final_sql)[:500])

        log.info("[chat] ▶ stage=db-exec engine=%s start", route.engine)
        t_db = _time.perf_counter()
        try:
            if route.engine == "pg":
                result = await run_readonly(
                    final_sql,
                    RunContext(
                        tenant_id=input.tenant_id,
                        states=input.states,
                        timeout_ms=settings.statement_timeout_ms,
                    ),
                )
            else:
                result = await run_readonly_mysql(
                    final_sql,
                    RunMysqlContext(timeout_ms=settings.statement_timeout_ms),
                )
            log.info("[chat] ✔ stage=db-exec engine=%s done in %.2fs (rows=%d)",
                     route.engine, _time.perf_counter() - t_db, result.row_count)
        except Exception as exc:
            msg = str(exc)
            if _INFRA_ERROR_RX.search(msg):
                log.error("[chat] infra error (not shown to user): %s", msg)
                return _log(
                    ChatResult(
                        kind="error",
                        message="The assistant is temporarily unavailable. Please try again shortly.",
                    ),
                    "none",
                    engine=route.engine,
                    sql_llm=sql,
                    sql_final=final_sql,
                    attempts=attempt,
                    error_message=msg,
                )
            last_error = msg
            messages.append(ChatMessage(role="assistant", content=final_sql))
            messages.append(build_retry_message(final_sql, last_error))
            continue

        clean = _drop_blank_dimension_rows(result.rows)
        log.info("[chat] rows: %d returned", len(clean))
        ans = format_answer(input.question, final_sql, clean)
        terminal = is_terminal_answer(input.question, clean)
        return _log(
            ChatResult(
                kind="chat" if terminal else "result",
                message=ans,
                sql=None if terminal else final_sql,
                rows=[] if terminal else clean,
                row_count=0 if terminal else len(clean),
            ),
            "none",
            engine=route.engine,
            sql_llm=sql,
            sql_final=final_sql,
            attempts=attempt,
        )

    return _log(
        ChatResult(kind="error", message=last_error, sql=last_sql),
        "none",
        attempts=MAX_ATTEMPTS,
        error_message=last_error,
    )

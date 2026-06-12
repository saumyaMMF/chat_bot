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
from app.chatbot.pronoun_anchor import try_pronoun_anchor
from app.chatbot.sanitize import sanitize_question, scrub_llm_prose
from app.chatbot.prompt_builder import build_messages, build_retry_message
from app.chatbot.answer_formatter import format_answer, is_terminal_answer
from app.chatbot.engine_router import route_engine
from app.chatbot.router import column_pin, route_signal
from app.chatbot.column_check import real_columns_for, validate_columns
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

MAX_ATTEMPTS = 2  # 1 initial + 1 execution-feedback retry. On CPU 7B each
# attempt costs 60-90s — 3 attempts blow past tolerable latency. With
# execution-feedback the second attempt usually self-corrects; if it still
# fails it's almost always a prompt/schema gap, not a stochastic error.

_GREETING_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"^\s*(hi|hello|hey|yo|hiya|howdy|good (morning|afternoon|evening))[\s!.?]*$", re.I),
        "Hi! I can help you explore your cannabis data — competitor brands, prices, categories, and trends. What would you like to know?",
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
    (
        re.compile(r"^\s*(yes|yeah|yep|yup|ok|okay|sure|y)[\s!.?]*$", re.I),
        "Got it. What would you like to know about your data?",
    ),
    (
        re.compile(r"^\s*(no|nope|nah|n)[\s!.?]*$", re.I),
        "No problem. Ask me anything about your market data when you're ready.",
    ),
    (
        re.compile(r"^\s*(cool|nice|great|awesome|👍|👌)[\s!.?]*$", re.I),
        "Glad it helped. Anything else you'd like to dig into?",
    ),
]

# Meta / explainer questions — the user is asking the bot to teach or
# self-describe, not pull data. Without this short-circuit, a 3B model
# burns 40-90s trying to write SQL and either invents columns or returns
# a confused REFUSE. Match conservatively: only when the verb signals
# explanation AND no data-words follow. False negative (one wasted LLM
# round-trip) is cheaper than false positive (real data query short-
# circuited to canned reply). Numeric / "how many"/"how much" stay LLM.
_META_QUESTION_RX = re.compile(
    r"^\s*("
    # "how do I/you/we ...", "how to ..."
    r"how\s+(do|can|should|would|to)\s+(i|you|we|one)?"
    r"|how\s+to\b"
    # "what does X mean", "what is meant by", "explain ..."
    r"|what\s+does\s+\S+\s+mean"
    r"|what\s+is\s+meant\s+by"
    r"|what\s+do\s+you\s+mean"
    r"|explain\s+(this|that|it|to me)?"
    r"|tell\s+me\s+(about\s+)?(how|why)"
    # "why is/are/do/did ..."
    r"|why\s+(is|are|do|does|did|should|would)\b"
    # Bare meta words
    r"|meaning\b"
    r"|definition\b"
    r"|define\b"
    r"|clarify\b"
    r")",
    re.I,
)
_META_REPLY = (
    "I answer data questions about your brand, market, inventory, orders, "
    "and sales. Try asking something like \"how many active dispensaries\" "
    "or \"top brands last 30 days\"."
)


# Bot self-identity catcher. Without this the LLM sometimes leaks the
# system-prompt phrasing ("I am a SQL analyst…") into a CHAT reply. Match
# here first and return a friendly canned line.
_BOT_IDENTITY_RX = re.compile(
    r"^\s*(?:hey|hi|hello|ok|so)?\s*"
    r"(?:what(?:'s| is)?\s+(?:your\s+name|this|that)|"
    r"who\s+(?:are\s+you|is\s+this)|"
    r"are\s+you\s+(?:a\s+)?(?:bot|ai|human|assistant|chatbot|llm|model|gpt|gemini)|"
    r"what\s+can\s+you\s+do|what\s+do\s+you\s+do|tell\s+me\s+about\s+yourself|introduce\s+yourself)"
    r"[\s!.?]*$",
    re.I,
)
_BOT_IDENTITY_REPLY = (
    "I am an AI assistant. I answer using the data I have access to — "
    "ask me about your brand, market, inventory, orders, or sales."
)


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

# Log-redaction helper. Replaces SQL string literals with '?' so log lines
# don't carry customer names, brand strings, or other tenant PII that comes
# from the user's question via LIKE / equality filters. Keeps the SQL shape
# fully readable for debugging.
_SQL_LITERAL_RX = re.compile(r"'(?:''|[^'])*'")


def _redact_sql_literals(sql: str) -> str:
    return _SQL_LITERAL_RX.sub("'?'", sql)


def _engine_of_table(table: str) -> str:
    """Tag a table name with its engine. rhize_* lives on MySQL; everything
    else (chatbot_*, complete_market_*, market_*) lives on Postgres. Loose
    by design — the routing pack is the authoritative source elsewhere; this
    helper is only used to filter retry hints so the model is not pushed into
    the route that just got rejected."""
    t = (table or "").lower()
    if t.startswith("rhize_"):
        return "mysql"
    return "pg"


_ISOLATION_COLS = frozenset({"tenantid", "tenant_id", "state"})


def strip_isolation_filters(sql: str) -> str:
    """Remove `tenantid=N`, `tenant_id=N`, `state='X'` predicates from WHERE.
    The prompt forbids them; Gate B (RLS / AST-injected predicate) is the
    real boundary. 3B models still write them, which used to burn a retry
    on guard rejection. Stripping is safer than rejection: the predicate
    would have been redundant with isolation anyway.
    """
    if not sql:
        return sql
    try:
        from sqlglot import exp, parse_one
        tree = parse_one(sql)
    except Exception:
        return sql

    def _is_isolation_eq(node) -> bool:  # type: ignore[no-untyped-def]
        if not isinstance(node, exp.EQ):
            return False
        left = node.this
        if not isinstance(left, exp.Column):
            return False
        return (left.name or "").lower() in _ISOLATION_COLS

    def _transform(node):  # type: ignore[no-untyped-def]
        if not isinstance(node, exp.Where):
            return node
        cond = node.this
        # WHERE may be a single EQ or a tree of AND/ORs. Recursively drop EQs
        # that match isolation cols. If everything drops, remove WHERE entirely.
        def _prune(n):  # type: ignore[no-untyped-def]
            if isinstance(n, exp.And):
                left = _prune(n.this)
                right = _prune(n.expression)
                if left is None:
                    return right
                if right is None:
                    return left
                return exp.And(this=left, expression=right)
            if _is_isolation_eq(n):
                return None
            return n
        pruned = _prune(cond)
        if pruned is None:
            return None  # drop WHERE entirely
        return exp.Where(this=pruned)

    transformed = tree.transform(_transform)
    return transformed.sql()


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
        return f"Your brand is {brand_name}."
    if _DISPLAY_NAME_RX.search(question) and display_name:
        return f"Your account is {display_name}."
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
# Columns where exact-match equality is almost always wrong: free-text user
# data with mixed casing, whitespace, hyphens, suffix codes ("HL-20"), etc.
# Apply on BOTH engines — `productName` / `customerName` are MySQL,
# `brand` / `company` exist on both. The rewrite swaps
# `WHERE col = 'X'` → `WHERE lower(col) LIKE lower('%X%')` so a substring
# query surfaces results without LLM having to remember LIKE.
_FREE_TEXT_COLS = (
    "brand", "company", "category_norm",
    "Brand_Name", "Company_Name", "Product_Name",
    "productName", "customerName", "strain",
)


_FREE_TEXT_COLS_LC = frozenset(c.lower() for c in _FREE_TEXT_COLS)


def rewrite_eq_to_ilike_on_text_cols(sql: str) -> str:
    """Rewrite ``<col> = '<lit>'`` to ``lower(<col>) LIKE lower('%<lit>%')``
    for the columns in ``_FREE_TEXT_COLS``. AST-based via sqlglot — safer
    than the prior regex which could mis-fire on column names embedded in
    function calls or aliases.

    Falls back to returning the input unchanged if parsing fails (rare —
    Gate C already accepted the SQL) so we never break execution over a
    cosmetic rewrite.
    """
    if not sql:
        return sql
    try:
        from sqlglot import exp, parse_one
        tree = parse_one(sql)
    except Exception:
        return sql

    def _transform(node):  # type: ignore[no-untyped-def]
        if not isinstance(node, exp.EQ):
            return node
        left = node.this
        right = node.expression
        # Must be column = string-literal. Bail otherwise (numeric eq, date
        # eq, expr = expr).
        if not isinstance(left, exp.Column) or not isinstance(right, exp.Literal):
            return node
        if not right.is_string:
            return node
        col_name = (left.name or "").lower()
        if col_name not in _FREE_TEXT_COLS_LC:
            return node
        value = right.this or ""
        # Drop pre-escaped wildcards so we don't end up with `%%X%%`.
        value = value.strip("%")
        new_lhs = exp.Lower(this=left.copy())
        new_rhs = exp.Lower(this=exp.Literal.string(f"%{value}%"))
        return exp.Like(this=new_lhs, expression=new_rhs)

    transformed = tree.transform(_transform)
    return transformed.sql()


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

# "which/how many companies have <X>" / "stores carrying <X>" — distinct
# companies on the latest date that have ANY on-shelf qty for entity X.
_COMPANIES_WITH_ENTITY_RX = re.compile(
    r"\b("
    r"(?:how\s+many|which|what|list)\s+(?:compan(?:y|ies)|stores?|dispensar(?:y|ies)|"
    r"partners?|retailers?)\s+(?:has|have|carry|carrying|sell|sells|stock|stocking)"
    r"|stores?\s+carrying"
    r"|compan(?:y|ies)\s+(?:with|stocking|carrying)"
    r")\s+([A-Za-z][A-Za-z0-9' -]{0,80}?)\s*[?.!,;]*\s*$",
    re.I,
)


# "live units of <product>", "stock of <brand>", "quantity of <X>" — user
# wants on-shelf qty per partner company for that specific entity. Always
# routes to rhize_dataset_main (which tracks Today's_Quantity_Total per
# Product_Name × Company_Name × date). Not rhize_live_inventory (own
# warehouse stock — different concept).
#
# Captures the entity name (possibly multi-word, up to 5 tokens before
# the next punctuation or sentence end).
_QTY_OF_ENTITY_RX = re.compile(
    r"\b(?:live\s+units?|units?|stock|quantity|qty)\s+of\s+"
    r"([A-Za-z][A-Za-z0-9' -]{0,80}?)\s*[?.!,;]*\s*$",
    re.I,
)

# "in/what/which unit/size/weight (is/are) <entity>"
# Also bare "in which unit" / "what unit they have" (pronoun → last entity).
# Captures optional entity; if absent, the pronoun-anchor path will fill from history.
_UNIT_OF_ENTITY_RX = re.compile(
    r"\b(?:what|which|in\s+which|in\s+what)\s+"
    r"(?:unit|units|size|sizes|weight|weights|pack(?:\s*size)?)\b"
    r"(?:[\s\S]{0,40}?\b(?:of|for)\s+"
    r"(?P<entity>[A-Za-z][A-Za-z0-9' -]{0,80}?))?"
    r"\s*[?.!,;]*\s*$",
    re.I,
)
# Pronoun follow-up: "in which unit they are present", "what size is it"
_UNIT_PRONOUN_RX = re.compile(
    r"\b(?:what|which|in\s+which|in\s+what)\s+"
    r"(?:unit|units|size|sizes|weight|weights|pack(?:\s*size)?)\b"
    r"[\s\S]*\b(?:it|they|those|these|them)\b",
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


# Intent markers: any of these in the message means the user expressed WHAT
# they want, so the bare-entity clarify gate must not fire. Includes question
# words, metric nouns, verbs, and table-ish nouns. Kept deliberately broad —
# a false negative here just means one clarify prompt too few, while a false
# positive would block a legitimate question behind a clarify.
_INTENT_WORDS_RX = re.compile(
    r"\b(how|what|which|who|whose|when|where|why|do|does|did|is|are|was|were|"
    r"can|could|should|would|will|count|many|much|top|best|worst|show|list|"
    r"give|get|find|search|compare|total|sum|average|avg|min|max|trend|share|"
    r"revenue|sales?|sold|sell|price|prices|pricing|cost|costs|unit|units|"
    r"stock|quantity|qty|inventory|product|products|brand|brands|store|stores|"
    r"company|companies|categor\w*|order|orders|carry|carrying|have|has|had|"
    r"doing|performance|performing|vs|versus|against)\b",
    re.I,
)


def _detect_bare_entity(question: str) -> str | None:
    """Return the entity text when the message is a bare entity name with no
    expressed intent ("31 north", "tea house"), else None. Conservative:
    short messages only, no intent word, no digits-only strings."""
    text = question.strip().strip(" ?!.\"'")
    if not text:
        return None
    words = re.findall(r"[A-Za-z0-9']+", text)
    if not words or len(words) > 5:
        return None
    if _INTENT_WORDS_RX.search(text):
        return None
    # All-numeric ("420") or single stopword — nothing to clarify about.
    if all(w.isdigit() for w in words):
        return None
    if len(words) == 1 and words[0].lower() in _ENTITY_STOPWORDS:
        return None
    return text


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
class PrevTurn:
    """One past turn from the same session, sent by the client.

    The frontend keeps the last N turns in React state and POSTs them in
    each request — server is stateless, so multi-worker uvicorn deploys are
    safe without Redis. ``question`` is the user message; ``answer`` is
    either the bot's natural-language summary, the executed SQL, or both.
    """
    question: str
    answer: str = ""
    sql: str | None = None


@dataclass
class ChatInput:
    tenant_id: int
    states: list[str]
    question: str
    brand_name: str | None = None
    display_name: str | None = None
    session_id: str | None = None
    history: list[PrevTurn] = field(default_factory=list)


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
    # Eval/debug only: SQL the bot actually ran. ChatResult.sql is None for
    # terminal answers (so the UI shows just the prose), but the eval harness
    # still wants to see the query. Populated by _log() from sql_final.
    sql_executed: str | None = None


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
    question = normalize_question(sanitize_question(input.question))

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
                session_id=input.session_id,
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
        # Surface the executed SQL on the result even when ChatResult.sql is
        # cleared for terminal answers — eval harness reads this.
        result.sql_executed = sql_final or result.sql
        return result

    greeting = _match_greeting(question)
    if greeting:
        return _log(ChatResult(kind="chat", message=greeting), "greeting")

    if _BOT_IDENTITY_RX.search(question):
        return _log(ChatResult(kind="chat", message=_BOT_IDENTITY_REPLY), "identity-bot")

    # Meta question short-circuit (#1). Must run AFTER greeting/identity so
    # "how does this work" still gets the help canned line, BEFORE the
    # disambig fast-path so "how to detect it" doesn't fall into LLM hell.
    if _META_QUESTION_RX.search(question):
        return _log(ChatResult(kind="chat", message=_META_REPLY), "meta")

    identity = _match_identity(question, input.brand_name, input.display_name)
    if identity:
        return _log(ChatResult(kind="chat", message=identity), "identity")

    # Bare-entity clarify gate. A message like "31 north" or "tea house"
    # names an entity but carries no intent (no verb, no metric, no
    # question word). Sending it to the LLM produces garbage: the 3B model
    # either guesses a column or parrots the previous answer from session
    # history. Ask the user what they want instead — deterministic, no LLM.
    bare = _detect_bare_entity(question)
    if bare:
        return _log(
            ChatResult(
                kind="clarify",
                message=f'What would you like to know about "{bare}"?',
                options=[
                    ClarifyOption(kind="PRODUCTS", value=f"how many products does {bare} have"),
                    ClarifyOption(kind="UNITS", value=f"live units of {bare}"),
                    ClarifyOption(kind="STORES", value=f"how many companies have {bare}"),
                    ClarifyOption(kind="MARKET", value=f"how is {bare} doing in the market"),
                ],
            ),
            "bare-entity-clarify",
        )

    # "how many companies have X" / "stores carrying X" — distinct companies
    # on latest date with on-shelf qty for entity X. Same routing logic as
    # qty-of-entity but COUNT(DISTINCT Company_Name) instead of group-by.
    companies_match = _COMPANIES_WITH_ENTITY_RX.search(question)
    if companies_match:
        raw_entity = companies_match.group(2).strip(" '\"").strip()
        if raw_entity and len(raw_entity) >= 2 and raw_entity.lower() not in _ENTITY_STOPWORDS:
            safe = raw_entity.replace("'", "''")
            comp_sql = (
                "SELECT Company_Name, "
                "SUM(CAST(NULLIF(`Today's_Quantity_Total`, '') AS DECIMAL(12,2))) AS total_units "
                "FROM rhize_dataset_main "
                f"WHERE (lower(Product_Name) LIKE lower('%{safe}%') "
                f"OR lower(Company_Name) LIKE lower('%{safe}%')) "
                "AND date = (SELECT MAX(date) FROM rhize_dataset_main) "
                "AND `Today's_Quantity_Total` IS NOT NULL "
                "AND `Today's_Quantity_Total` <> '' "
                "GROUP BY Company_Name "
                "HAVING total_units > 0 "
                "ORDER BY total_units DESC "
                "LIMIT 100"
            )
            try:
                verdict = validate_mysql_sql(comp_sql, input.tenant_id)
                if verdict.ok:
                    final_sql = rewrite_eq_to_ilike_on_text_cols(
                        enforce_limit_mysql(verdict.sql, max_rows=settings.default_row_limit)
                    )
                    log.info("[chat] companies-with-entity fast-path: entity=<redacted>")
                    res = await run_readonly_mysql(
                        final_sql,
                        RunMysqlContext(timeout_ms=settings.statement_timeout_ms),
                    )
                    clean = _drop_blank_dimension_rows(res.rows)
                    ans = format_answer(input.question, final_sql, clean)
                    terminal = is_terminal_answer(input.question, clean)
                    return _log(
                        ChatResult(
                            kind="chat" if terminal else "result",
                            message=ans,
                            sql=final_sql,
                            rows=clean,
                            row_count=len(clean),
                        ),
                        "companies-with-entity",
                        engine="mysql",
                        sql_final=final_sql,
                    )
            except Exception as exc:
                log.warning("[chat] companies-with-entity exec failed, falling through: %s", exc)

    # "live units of <entity>" / "stock of <entity>" — explicit on-shelf
    # qty question, always routes to rhize_dataset_main. Bypasses the LLM
    # so the 3B model can't drag it back to rhize_live_inventory (own-
    # warehouse stock — different concept). Same Gate C/D path as the
    # rest, so safety invariants hold.
    qty_of_match = _QTY_OF_ENTITY_RX.search(question)
    if qty_of_match:
        raw_entity = qty_of_match.group(1).strip(" '\"").strip()
        if raw_entity and len(raw_entity) >= 2 and raw_entity.lower() not in _ENTITY_STOPWORDS:
            safe = raw_entity.replace("'", "''")
            qty_sql = (
                "SELECT Company_Name, Product_Name, "
                "SUM(CAST(NULLIF(`Today's_Quantity_Total`, '') AS DECIMAL(12,2))) AS total_units "
                "FROM rhize_dataset_main "
                f"WHERE (lower(Product_Name) LIKE lower('%{safe}%') "
                f"OR lower(Company_Name) LIKE lower('%{safe}%')) "
                "AND date = (SELECT MAX(date) FROM rhize_dataset_main) "
                "AND `Today's_Quantity_Total` IS NOT NULL "
                "AND `Today's_Quantity_Total` <> '' "
                "GROUP BY Company_Name, Product_Name "
                "HAVING total_units > 0 "
                "ORDER BY total_units DESC "
                "LIMIT 50"
            )
            try:
                verdict = validate_mysql_sql(qty_sql, input.tenant_id)
                if verdict.ok:
                    final_sql = rewrite_eq_to_ilike_on_text_cols(
                        enforce_limit_mysql(verdict.sql, max_rows=settings.default_row_limit)
                    )
                    log.info("[chat] qty-of-entity fast-path: entity=<redacted>")
                    res = await run_readonly_mysql(
                        final_sql,
                        RunMysqlContext(timeout_ms=settings.statement_timeout_ms),
                    )
                    clean = _drop_blank_dimension_rows(res.rows)
                    ans = format_answer(input.question, final_sql, clean)
                    terminal = is_terminal_answer(input.question, clean)
                    return _log(
                        ChatResult(
                            kind="chat" if terminal else "result",
                            message=ans,
                            sql=final_sql,
                            rows=clean,
                            row_count=len(clean),
                        ),
                        "qty-of-entity",
                        engine="mysql",
                        sql_final=final_sql,
                    )
            except Exception as exc:
                log.warning("[chat] qty-of-entity exec failed, falling through: %s", exc)

    # "what unit / which size / in which unit" — pack-size pivot question.
    # Bypasses the LLM so a 3B model can't invent "pounds" / "ounces" when
    # the column literally holds enum values like 1g, 3.5g, 7g, 1pk.
    # Entity comes from the question itself, or from last history turn when
    # the user used a pronoun ("they / it / those").
    unit_entity: str | None = None
    m_unit = _UNIT_OF_ENTITY_RX.search(question)
    if m_unit:
        ent = (m_unit.group("entity") or "").strip(" '\"").strip()
        if ent and len(ent) >= 2 and ent.lower() not in _ENTITY_STOPWORDS:
            unit_entity = ent
    if unit_entity is None and _UNIT_PRONOUN_RX.search(question) and input.history:
        # Last turn's question often holds the entity ("the quantity Mellowz have today").
        # Grab the longest capitalized token from it as a heuristic.
        prior = input.history[-1].question or ""
        import re as _re
        cands = _re.findall(r"[A-Z][A-Za-z0-9]{2,40}", prior)
        # Drop common stopword-like tokens that pass the capitalization filter.
        cands = [c for c in cands if c.lower() not in _ENTITY_STOPWORDS]
        if cands:
            unit_entity = max(cands, key=len)
    if unit_entity:
        safe_unit = unit_entity.replace("'", "''")
        unit_sql = (
            "SELECT DISTINCT Unit "
            "FROM rhize_dataset_main "
            f"WHERE (lower(Product_Name) LIKE lower('%{safe_unit}%') "
            f"OR lower(Company_Name) LIKE lower('%{safe_unit}%')) "
            "AND date = (SELECT MAX(date) FROM rhize_dataset_main) "
            "AND Unit IS NOT NULL AND Unit <> '' "
            "ORDER BY Unit "
            "LIMIT 50"
        )
        try:
            verdict = validate_mysql_sql(unit_sql, input.tenant_id)
            if verdict.ok:
                final_sql = rewrite_eq_to_ilike_on_text_cols(
                    enforce_limit_mysql(verdict.sql, max_rows=settings.default_row_limit)
                )
                log.info("[chat] unit-of-entity fast-path: entity=<redacted>")
                res = await run_readonly_mysql(
                    final_sql,
                    RunMysqlContext(timeout_ms=settings.statement_timeout_ms),
                )
                clean = _drop_blank_dimension_rows(res.rows)
                ans = format_answer(input.question, final_sql, clean)
                terminal = is_terminal_answer(input.question, clean)
                return _log(
                    ChatResult(
                        kind="chat" if terminal else "result",
                        message=ans,
                        sql=final_sql,
                        rows=clean,
                        row_count=len(clean),
                    ),
                    "unit-of-entity",
                    engine="mysql",
                    sql_final=final_sql,
                )
        except Exception as exc:
            log.warning("[chat] unit-of-entity exec failed, falling through: %s", exc)

    # Pronoun-anchor fast-path. "how many of them", "show 5 of those" —
    # 3B model can't bind anaphora reliably. Reuse last turn's SQL FROM/
    # WHERE deterministically. Runs the same Gate C/D as everything else.
    anchor = try_pronoun_anchor(question, input.history)
    if anchor is not None:
        try:
            if anchor.dialect == "mysql":
                verdict = validate_mysql_sql(anchor.sql, input.tenant_id)
                if verdict.ok:
                    final_sql = rewrite_eq_to_ilike_on_text_cols(
                        enforce_limit_mysql(verdict.sql, max_rows=settings.default_row_limit)
                    )
                    res = await run_readonly_mysql(
                        final_sql,
                        RunMysqlContext(timeout_ms=settings.statement_timeout_ms),
                    )
                    engine = "mysql"
                else:
                    raise RuntimeError(f"anchor SQL rejected: {verdict.reason}")
            else:
                verdict = validate_sql(anchor.sql)
                if verdict.ok:
                    final_sql = rewrite_eq_to_ilike_on_text_cols(
                        enforce_limit(verdict.sql, max_rows=settings.default_row_limit)
                    )
                    res = await run_readonly(
                        final_sql,
                        RunContext(
                            tenant_id=input.tenant_id,
                            states=input.states,
                            timeout_ms=settings.statement_timeout_ms,
                        ),
                    )
                    engine = "pg"
                else:
                    raise RuntimeError(f"anchor SQL rejected: {verdict.reason}")
            log.info("[chat] pronoun-anchor hit: %s", anchor.explanation)
            clean = _drop_blank_dimension_rows(res.rows)
            ans = format_answer(input.question, final_sql, clean)
            terminal = is_terminal_answer(input.question, clean)
            return _log(
                ChatResult(
                    kind="chat" if terminal else "result",
                    message=ans,
                    sql=final_sql,
                    rows=clean,
                    row_count=len(clean),
                ),
                "pronoun-anchor",
                engine=engine,
                sql_final=final_sql,
            )
        except Exception as exc:
            log.warning("[chat] pronoun-anchor failed, falling through: %s", exc)

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
                enforce_limit(verdict.sql, max_rows=settings.default_row_limit)
            )
            log.info("[chat] fast-path (%s=<redacted>): %s",
                     entity.column,
                     _redact_sql_literals(re.sub(r"\s+", " ", final_sql))[:300])
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
                        sql=final_sql,
                        rows=clean,
                        row_count=len(clean),
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
    # Stage-1 router: deterministic table/engine choice from the routing pack.
    # column_pin (unique column token → table) is the strongest signal — beats
    # everything that follows. route_signal tags ownership via synonyms; used
    # only when column_pin misses. Both are pure-Python regex, sub-millisecond.
    pin = column_pin(question)
    sig = route_signal(question) if pin is None else None
    if pin is not None:
        log.info("[router] column_pin token=%r → table=%s engine=%s",
                 pin.token, pin.table, pin.engine)
    elif sig is not None and sig.matched_tokens:
        log.info("[router] route_signal ownership=%s engine_hint=%s tokens=%s tables=%s",
                 sig.ownership, sig.engine_hint, sig.matched_tokens[:5],
                 sig.candidate_tables[:3])

    def _resolve_dialect() -> str:
        # column_pin is authoritative when present.
        if pin is not None:
            return pin.engine
        # synonyms next.
        if sig is not None and sig.ownership == "own":
            return "mysql"
        if sig is not None and sig.ownership == "market":
            return "postgres"
        # Legacy fallback.
        return "postgres" if _has_market_signal(question) else "mysql"

    if settings.fast_path_enabled:
        fp_dialect = _resolve_dialect()
        log.info("[chat] >> stage=fast-path-lookup dialect=%s threshold=%.3f",
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
        log.info("[chat] OK stage=fast-path-lookup done in %.2fs hit=%s",
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
                    final_sql = rewrite_eq_to_ilike_on_text_cols(
                        enforce_limit_mysql(verdict.sql, max_rows=settings.default_row_limit)
                    )
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
                        enforce_limit(verdict.sql, max_rows=settings.default_row_limit)
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
                        sql=final_sql,
                        rows=clean,
                        row_count=len(clean),
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

    log.info("[chat] >> stage=rag-retrieval start")
    t0 = _time.perf_counter()
    messages: list[ChatMessage] = await build_messages(
        question,
        brand_name=input.brand_name,
        display_name=input.display_name,
        tenant_id=input.tenant_id,
        states=input.states,
        history=input.history,
    )
    log.info("[chat] OK stage=rag-retrieval done in %.2fs (messages=%d)",
             _time.perf_counter() - t0, len(messages))
    last_sql: str | None = None
    last_error = "The query could not be generated or executed."

    for attempt in range(1, MAX_ATTEMPTS + 1):
        log.info("[chat] >> stage=llm-call attempt=%d start", attempt)
        t_llm = _time.perf_counter()
        try:
            reply = await chat_complete(messages)
            log.info("[chat] OK stage=llm-call attempt=%d done in %.2fs (chars=%d)",
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
            # Parrot guard: a prose reply that echoes a prior turn's answer
            # (or a history stub) is the 3B model copying the history block,
            # not answering. Feed it back as a retry instead of showing it.
            chat_text = parsed.chat.strip()
            prior_answers = {
                (getattr(h, "answer", None) or "").strip()
                for h in (input.history or [])
            }
            prior_answers.discard("")
            if chat_text in prior_answers or chat_text == "(answered)":
                last_error = "Reply parroted a prior answer instead of addressing the question."
                messages.append(ChatMessage(role="assistant", content=reply))
                messages.append(build_retry_message(
                    "(parroted prior answer)",
                    "Do not repeat earlier answers. Answer the LAST question only — emit SQL, REFUSE, CLARIFY, or CHAT.",
                ))
                continue
            return _log(ChatResult(kind="chat", message=scrub_llm_prose(parsed.chat)), "none", attempts=attempt)
        if parsed.refusal:
            return _log(ChatResult(kind="refusal", message=scrub_llm_prose(parsed.refusal)), "none", attempts=attempt)
        if parsed.clarify_message:
            return _log(
                ChatResult(
                    kind="clarify",
                    message=scrub_llm_prose(parsed.clarify_message),
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
        # Stage-1 router signals override the legacy heuristic: a column_pin
        # to a postgres table is authoritative ("does this lot have THC" hits
        # MySQL even without a market keyword); a route_signal=='market'
        # tag licenses PG even when the regex misses.
        _market_ok = _has_market_signal(input.question)
        _pin = column_pin(input.question)
        _sig = route_signal(input.question) if _pin is None else None
        if _pin is not None and _pin.engine == "postgres":
            _market_ok = True
        elif _sig is not None and _sig.ownership == "market":
            _market_ok = True
        if route.engine == "pg" and not _market_ok:
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

        # Strip tenant/state isolation predicates before validation. Prompt
        # forbids them; Gate B is the real boundary. Avoids burning a retry
        # on guard rejection when the model writes them anyway.
        sql = strip_isolation_filters(sql)

        if route.engine == "pg":
            verdict = validate_sql(sql)
            if not verdict.ok:
                last_sql = sql
                last_error = verdict.reason
                messages.append(ChatMessage(role="assistant", content=sql))
                messages.append(build_retry_message(sql, f"Rejected by safety check: {verdict.reason}"))
                continue
            final_sql = rewrite_eq_to_ilike_on_text_cols(
                enforce_limit(verdict.sql, max_rows=settings.default_row_limit)
            )
        else:
            verdict = validate_mysql_sql(sql, input.tenant_id)
            if not verdict.ok:
                last_sql = sql
                last_error = verdict.reason
                messages.append(ChatMessage(role="assistant", content=sql))
                messages.append(build_retry_message(sql, f"Rejected by safety check: {verdict.reason}"))
                continue
            final_sql = rewrite_eq_to_ilike_on_text_cols(
                enforce_limit_mysql(verdict.sql, max_rows=settings.default_row_limit)
            )

        # Column existence pre-check — catches hallucinated cols before the
        # DB round-trip. Feed REAL columns back so attempt 2 is informed,
        # not just told "column X doesn't exist". The 3B model often retries
        # the same bad column on a bare DB error.
        col_check = validate_columns(final_sql)
        if not col_check.ok:
            last_sql = final_sql
            last_error = col_check.reason
            log.info("[chat] column pre-check rejected: %s", col_check.reason)
            # Collect every table mentioned in the SQL — both the in-scope
            # FROM tables AND any table where a hint pointed to. When the
            # bad column exists nowhere (no hints), the FROM tables still
            # need their real columns surfaced so the LLM retry has ground
            # truth to work with.
            from sqlglot import exp as _sqlglot_exp, parse_one as _parse_one
            tables_in_play: set[str] = set()
            try:
                _tree = _parse_one(final_sql)
                for t in _tree.find_all(_sqlglot_exp.Table):
                    name = (t.name or "").lower()
                    if name and real_columns_for(name):
                        tables_in_play.add(name)
            except Exception:
                pass
            # Engine-aware hint filter: drop suggestions that point to the
            # OTHER engine's tables. Pushing a MySQL-routed retry toward a
            # Postgres column (or vice-versa) deadlocks the model — the
            # route guard already rejected that direction once. Keep only
            # hints on the SAME engine as `route.engine`. Also drop the
            # cross-engine columns from `col_check.reason`.
            same_engine_suggestions: dict[str, list[str]] = {}
            for bad, hints in (col_check.suggestions or {}).items():
                kept = [h for h in hints if _engine_of_table(h.split(".", 1)[0]) == route.engine]
                same_engine_suggestions[bad] = kept
                for h in kept:
                    tables_in_play.add(h.split(".", 1)[0])
            schema_hint_lines: list[str] = []
            for t in sorted(tables_in_play):
                cols = real_columns_for(t)
                if cols:
                    schema_hint_lines.append(f"{t}: {', '.join(cols)}")
            schema_hint = ("\nReal columns on this engine:\n" + "\n".join(schema_hint_lines)) if schema_hint_lines else ""
            # Rebuild reason from filtered suggestions so the model isn't told
            # "try chatbot_mv_market_daily.brand" after PG was already rejected.
            reason_lines = []
            for c in sorted(same_engine_suggestions.keys()):
                hints = same_engine_suggestions[c]
                if hints:
                    reason_lines.append(f"`{c}` does not exist on the in-scope tables (try: {', '.join(hints)})")
                else:
                    reason_lines.append(f"`{c}` does not exist on any same-engine table — pick a different column from the schema list below")
            engine_reason = "Unknown column(s): " + "; ".join(reason_lines) if reason_lines else col_check.reason
            messages.append(ChatMessage(role="assistant", content=final_sql))
            messages.append(build_retry_message(
                final_sql,
                f"{engine_reason}{schema_hint}",
            ))
            continue

        last_sql = final_sql

        log.info("[chat] question: %s", input.question)
        log.info("[chat] engine:   %s", route.engine)
        log.info("[chat] SQL: %s", _redact_sql_literals(re.sub(r"\s+", " ", final_sql))[:500])

        log.info("[chat] >> stage=db-exec engine=%s start", route.engine)
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
            log.info("[chat] OK stage=db-exec engine=%s done in %.2fs (rows=%d)",
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
                sql=final_sql,
                rows=clean,
                row_count=len(clean),
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

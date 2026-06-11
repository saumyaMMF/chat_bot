"""User-input sanitizer.

The SQL guard catches malicious SQL after the LLM emits it, but a crafted
question can still derail the CHAT/CLARIFY/REFUSE paths or impersonate a
system message inside the few-shot block. Strip the obvious prompt-injection
tells before the question reaches build_messages().

Pure function. Idempotent. No I/O.
"""

from __future__ import annotations

import re

MAX_QUESTION_LEN = 1_000

# Role-marker / control-token leakage. Matches OpenAI-style role prefixes,
# chat-template separators, and our own CHAT:/REFUSE:/CLARIFY: prefixes that
# would otherwise let a user inject a fake assistant turn.
_ROLE_MARKER_RX = re.compile(
    r"(?im)^\s*(system|assistant|user|tool|function)\s*:",
)
_CONTROL_PREFIX_RX = re.compile(
    r"(?im)^\s*(CHAT|REFUSE|CLARIFY)\s*:",
)
_CHATML_RX = re.compile(r"<\|(?:im_start|im_end|endoftext|system|user|assistant)\|>", re.I)
_SEPARATOR_RX = re.compile(r"^[-=*_~]{3,}$", re.M)
_ZERO_WIDTH_RX = re.compile(r"[​-‍﻿⁠]")


# Post-LLM CHAT/CLARIFY/REFUSE scrub. The system prompt tells the model NOT
# to leak internals (table/column/SQL terms) but small models break this rule
# under pressure (anaphora, refusals, "couldn't find" replies). Backstop:
# strip identifiers from any prose-mode reply BEFORE the user sees it.
_TABLE_NAME_RX = re.compile(
    r"`?\b("
    r"rhize_[a-z_]+|"
    r"chatbot_[a-z_]+|"
    r"complete_market_scrapper_dataset"
    r")\b`?",
    re.I,
)
# Match ONLY SQL terms that are unambiguous internals.
# `FROM`/`WHERE`/`JOIN`/`SELECT` are excluded — they're common English words
# (lowercase "from your data", "where you ...") and replacing them mangles
# legit prose. The phrases we keep are either uppercase-tech-y or specific
# enough to never appear as English.
_SQL_TERM_RX = re.compile(
    r"\b("
    r"\bSQL\b|\bSELECT\s+statement|GROUP\s+BY|ORDER\s+BY|"
    r"row-level\s+security|\bRLS\b|pgvector|embeddings?|"
    r"tenant\s*id|tenantid|"
    r"schema|column\s+name|table\s+name|database\s+(schema|column|table)|"
    r"MySQL|PostgreSQL|Postgres"
    r")\b",
    re.I,
)
_SQL_TERM_REPLACE = "data"
_FALLBACK = (
    "I can answer that from your business data, but I can't share the internals. "
    "Try rephrasing your question — e.g. \"top brands last 30 days\" or "
    "\"how many active dispensaries\"."
)


def scrub_llm_prose(text: str) -> str:
    """Strip internal identifiers from a CHAT/CLARIFY/REFUSE reply.

    Conservative: if scrubbing removes too much (>40% of chars), return the
    canned fallback so the user never sees a confused half-sentence."""
    if not text:
        return text
    original_len = len(text)
    cleaned = _TABLE_NAME_RX.sub("data", text)
    cleaned = _SQL_TERM_RX.sub(_SQL_TERM_REPLACE, cleaned)
    # Collapse "data data data" runs left by the substitutions.
    cleaned = re.sub(r"\b(data)(\s+data){2,}\b", "data", cleaned, flags=re.I)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    if not cleaned or len(cleaned) < int(original_len * 0.6):
        return _FALLBACK
    return cleaned


def sanitize_question(raw: str) -> str:
    """Strip prompt-injection markers from user input.

    Bounded, deterministic. Does NOT touch domain terms — the misspelling
    normalizer runs separately. Order matters: zero-width first (they hide
    the markers below), then ChatML tokens, role markers, control prefixes,
    horizontal-rule separators, finally whitespace.
    """
    if not raw:
        return ""
    s = _ZERO_WIDTH_RX.sub("", raw)
    s = _CHATML_RX.sub(" ", s)
    s = _ROLE_MARKER_RX.sub("", s)
    s = _CONTROL_PREFIX_RX.sub("", s)
    s = _SEPARATOR_RX.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > MAX_QUESTION_LEN:
        s = s[:MAX_QUESTION_LEN]
    return s

"""Tests for prompt assembly."""

from __future__ import annotations

import pytest

from app.chatbot import prompt_builder as pb
from app.chatbot import schema_store as ss
from app.chatbot.llm_client import ChatMessage


# ----------------------------- RESTRICTION_RULES -----------------------------

class TestRestrictionRules:
    def test_contains_one_select(self):
        assert "ONE statement" in pb.RESTRICTION_RULES
        assert "SELECT" in pb.RESTRICTION_RULES

    def test_lists_forbidden_keywords(self):
        for kw in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
                   "CREATE", "GRANT", "MERGE", "COPY", "SET"]:
            assert kw in pb.RESTRICTION_RULES

    def test_lists_forbidden_functions(self):
        for fn in ["pg_sleep", "dblink", "lo_import", "set_config",
                   "current_setting", "pg_read_file"]:
            assert fn in pb.RESTRICTION_RULES

    def test_blocks_system_catalogs(self):
        assert "pg_*" in pb.RESTRICTION_RULES
        assert "information_schema" in pb.RESTRICTION_RULES

    def test_no_tenant_or_state_filter(self):
        assert "NEVER add tenant or state filters" in pb.RESTRICTION_RULES
        assert "Row-Level Security" in pb.RESTRICTION_RULES

    def test_reply_format(self):
        assert "CHAT:" in pb.RESTRICTION_RULES
        assert "REFUSE:" in pb.RESTRICTION_RULES


# ----------------------------- static SYSTEM_PROMPT -----------------------------

class TestSystemPrompt:
    def test_embeds_restriction_rules(self):
        assert pb.RESTRICTION_RULES in pb.SYSTEM_PROMPT

    def test_embeds_schema_context(self):
        # schema_context.md mentions the market table.
        assert "complete_market_scrapper_dataset" in pb.SYSTEM_PROMPT
        assert "chatbot_mv_market_daily" in pb.SYSTEM_PROMPT


# ----------------------------- examples loaded -----------------------------

class TestExamplesLoaded:
    def test_at_least_one(self):
        assert len(pb.EXAMPLES) > 0

    def test_includes_refusal(self):
        assert any(e.sql is None and e.refusal for e in pb.EXAMPLES)

    def test_includes_sql(self):
        assert any(e.sql for e in pb.EXAMPLES)


# ----------------------------- build_messages (async, mocked retrieval) -----------------------------

@pytest.fixture
def stub_retrieval(monkeypatch):
    """Force retrieve_top_k to return a fixed, non-empty list so build_messages
    takes the dynamic path without touching the DB / embedding model."""
    sample = [
        ss.SchemaChunk(
            id="table:chatbot_mv_market_daily",
            kind="view",
            table_name="chatbot_mv_market_daily",
            column_name=None,
            data_type=None,
            definition="Daily aggregate view.",
            restrictions="Prefer this view for brand/company/category aggregates.",
            distance=0.05,
        ),
        ss.SchemaChunk(
            id="col:chatbot_mv_market_daily.brand",
            kind="column",
            table_name="chatbot_mv_market_daily",
            column_name="brand",
            data_type="TEXT",
            definition="Brand grouping key.",
            restrictions="Exclude blanks for any GROUP BY brand.",
            distance=0.10,
        ),
    ]

    async def fake(question, k=None):
        return sample

    monkeypatch.setattr(pb, "retrieve_top_k", fake)
    return sample


@pytest.fixture
def stub_retrieval_fails(monkeypatch):
    async def fake(question, k=None):
        raise RuntimeError("no DB")
    monkeypatch.setattr(pb, "retrieve_top_k", fake)


class TestBuildMessagesDynamic:
    async def test_first_is_system(self, stub_retrieval):
        msgs = await pb.build_messages("top brands")
        assert msgs[0].role == "system"
        assert isinstance(msgs[0], ChatMessage)

    async def test_system_contains_restriction_rules(self, stub_retrieval):
        msgs = await pb.build_messages("top brands")
        assert pb.RESTRICTION_RULES in msgs[0].content

    async def test_system_contains_retrieved_chunks(self, stub_retrieval):
        msgs = await pb.build_messages("top brands")
        sys = msgs[0].content
        assert "chatbot_mv_market_daily" in sys
        assert "Daily aggregate view." in sys
        assert "brand" in sys

    async def test_system_surfaces_chunk_restrictions(self, stub_retrieval):
        msgs = await pb.build_messages("top brands")
        sys = msgs[0].content
        assert "ADDITIONAL RESTRICTIONS" in sys
        assert "Exclude blanks for any GROUP BY brand." in sys

    async def test_last_is_user_question(self, stub_retrieval):
        msgs = await pb.build_messages("show me cartridges")
        assert msgs[-1].role == "user"
        assert msgs[-1].content == "show me cartridges"

    async def test_alternating_user_assistant(self, stub_retrieval):
        msgs = await pb.build_messages("any question")
        middle = msgs[1:-1]
        assert len(middle) % 2 == 0
        for i in range(0, len(middle), 2):
            assert middle[i].role == "user"
            assert middle[i + 1].role == "assistant"


class TestBuildMessagesFallback:
    async def test_falls_back_to_static_schema(self, stub_retrieval_fails):
        msgs = await pb.build_messages("top brands")
        sys = msgs[0].content
        # static schema_context.md content present
        assert "complete_market_scrapper_dataset" in sys
        # rules still always-on
        assert pb.RESTRICTION_RULES in sys


# ----------------------------- retry message -----------------------------

class TestBuildRetryMessage:
    def test_includes_error_and_sql(self):
        msg = pb.build_retry_message("SELECT bad FROM t", "column bad does not exist")
        assert msg.role == "user"
        assert "column bad does not exist" in msg.content
        assert "SELECT bad FROM t" in msg.content
        assert "corrected" in msg.content.lower()

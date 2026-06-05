"""Tests for pure helpers in chat_service: extract_sql, canonicalize_sql,
greeting/identity fast-paths, drop_blank_dimension_rows."""

from __future__ import annotations

import pytest

from app.chatbot import chat_service as cs


# ----------------------------- extract_sql -----------------------------

class TestExtractSql:
    def test_chat_prefix(self):
        r = cs.extract_sql("CHAT: Hi there!")
        assert r.chat == "Hi there!"
        assert r.refusal is None and r.sql is None

    def test_chat_prefix_case_insensitive(self):
        r = cs.extract_sql("chat: ok")
        assert r.chat == "ok"

    def test_chat_empty_body_gets_default(self):
        r = cs.extract_sql("CHAT:")
        assert r.chat and "help" in r.chat.lower()

    def test_refuse_prefix(self):
        r = cs.extract_sql("REFUSE: not allowed")
        assert r.refusal == "not allowed"
        assert r.chat is None and r.sql is None

    def test_refuse_empty_body_gets_default(self):
        r = cs.extract_sql("REFUSE:")
        assert r.refusal and "can't help" in r.refusal.lower()

    def test_sql_plain(self):
        r = cs.extract_sql("SELECT 1 FROM t")
        assert r.sql == "SELECT 1 FROM t"
        assert r.chat is None and r.refusal is None

    def test_sql_with_with(self):
        r = cs.extract_sql("WITH t AS (SELECT 1) SELECT * FROM t")
        assert r.sql is not None and r.sql.startswith("WITH")

    def test_sql_fenced(self):
        r = cs.extract_sql("```sql\nSELECT brand FROM chatbot_mv_market_daily\n```")
        assert r.sql == "SELECT brand FROM chatbot_mv_market_daily"

    def test_sql_fenced_plain(self):
        r = cs.extract_sql("```\nSELECT 1\n```")
        assert r.sql == "SELECT 1"

    def test_prose_routes_to_chat(self):
        r = cs.extract_sql("Sure! Here's the answer: 42.")
        assert r.chat and r.chat.startswith("Sure!")
        assert r.sql is None and r.refusal is None

    def test_clarify_basic(self):
        r = cs.extract_sql(
            "CLARIFY: Did you mean a brand or a company?\n"
            "- BRAND: Rimeline\n"
            "- COMPANY: Rimeline"
        )
        assert r.clarify_message and "brand or a company" in r.clarify_message
        assert len(r.clarify_options) == 2
        assert r.clarify_options[0].kind == "BRAND"
        assert r.clarify_options[0].value == "Rimeline"
        assert r.clarify_options[1].kind == "COMPANY"

    def test_clarify_engine_choice(self):
        r = cs.extract_sql(
            "CLARIFY: Whose sales?\n"
            "- MINE: My sales\n"
            "- MARKET: Market sales"
        )
        assert r.clarify_message == "Whose sales?"
        kinds = {o.kind for o in r.clarify_options}
        assert kinds == {"MINE", "MARKET"}


# ----------------------------- canonicalize_sql -----------------------------

class TestCanonicalize:
    def test_fixes_scrapper_typo(self):
        out = cs.canonicalize_sql("SELECT * FROM complete_market_scraper_dataset")
        assert "complete_market_scrapper_dataset" in out

    def test_leaves_correct_name(self):
        sql = "SELECT * FROM complete_market_scrapper_dataset"
        assert cs.canonicalize_sql(sql) == sql

    def test_case_insensitive(self):
        out = cs.canonicalize_sql("SELECT * FROM COMPLETE_MARKET_SCRAPER_DATASET")
        assert "complete_market_scrapper_dataset" in out.lower()


# ----------------------------- greeting fast-path -----------------------------

class TestGreetings:
    @pytest.mark.parametrize(
        "q",
        ["hi", "hello", "hey", "yo", "hiya", "howdy",
         "good morning", "good evening", "Hi!", "HELLO."],
    )
    def test_hello_family(self, q):
        assert cs._match_greeting(q) is not None

    @pytest.mark.parametrize("q", ["thanks", "thank you", "thx", "ty", "cheers", "appreciate it"])
    def test_thanks_family(self, q):
        out = cs._match_greeting(q)
        assert out and "welcome" in out.lower()

    @pytest.mark.parametrize("q", ["help", "what can you do", "how does this work"])
    def test_help_family(self, q):
        out = cs._match_greeting(q)
        assert out is not None

    @pytest.mark.parametrize("q", ["bye", "goodbye", "see ya", "later"])
    def test_bye_family(self, q):
        out = cs._match_greeting(q)
        assert out and "bye" in out.lower()

    @pytest.mark.parametrize("q", ["top brands", "what's the revenue trend", "list cartridges"])
    def test_real_questions_not_matched(self, q):
        assert cs._match_greeting(q) is None


# ----------------------------- identity fast-path -----------------------------

class TestIdentity:
    def test_brand_match(self):
        out = cs._match_identity("what is my brand name", "Acme", None)
        assert out == "Your brand is **Acme**."

    def test_who_am_i(self):
        out = cs._match_identity("who am i", "Acme", None)
        assert out == "Your brand is **Acme**."

    def test_display_match(self):
        out = cs._match_identity("my account name", None, "Acme Cannabis")
        assert out == "Your account is **Acme Cannabis**."

    def test_no_brand_supplied_returns_none(self):
        assert cs._match_identity("what is my brand name", None, None) is None

    def test_unrelated_question(self):
        assert cs._match_identity("top brands", "Acme", "Acme Cannabis") is None


# ----------------------------- drop_blank_dimension_rows -----------------------------

class TestDropBlankDimensionRows:
    def test_empty(self):
        assert cs._drop_blank_dimension_rows([]) == []

    def test_drops_blank_text_first_col(self):
        rows = [
            {"brand": "Acme", "rev": 100},
            {"brand": "", "rev": 50},
            {"brand": None, "rev": 25},
            {"brand": "   ", "rev": 10},
            {"brand": "Beta", "rev": 5},
        ]
        out = cs._drop_blank_dimension_rows(rows)
        assert [r["brand"] for r in out] == ["Acme", "Beta"]

    def test_does_not_drop_when_first_col_numeric(self):
        rows = [{"cnt": 0, "x": "a"}, {"cnt": 5, "x": "b"}]
        out = cs._drop_blank_dimension_rows(rows)
        assert out == rows  # numeric leading col untouched

    def test_preserves_order(self):
        rows = [{"k": "a"}, {"k": "b"}, {"k": "c"}]
        assert cs._drop_blank_dimension_rows(rows) == rows

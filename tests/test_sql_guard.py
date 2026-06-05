"""Gate C tests — port of sqlGuard.test.ts. Pure, no DB."""

from __future__ import annotations

import pytest

from app.chatbot.sql_guard import (
    ALLOWED_TABLES,
    assert_read_only,
    enforce_limit,
    validate_sql,
)


# Sanity: at least one known allow-listed table.
def test_allowlist_contains_market_table():
    assert "complete_market_scrapper_dataset" in ALLOWED_TABLES
    assert "chatbot_mv_market_daily" in ALLOWED_TABLES


# --------------------------- validate_sql: accepts ---------------------------

class TestValidateAccepts:
    def test_simple_select(self):
        r = validate_sql("SELECT brand FROM chatbot_mv_market_daily")
        assert r.ok, r.reason

    def test_with_cte(self):
        sql = (
            "WITH t AS (SELECT brand, revenue FROM chatbot_mv_market_daily) "
            "SELECT brand, SUM(revenue) FROM t GROUP BY brand"
        )
        r = validate_sql(sql)
        assert r.ok, r.reason

    def test_aggregate_with_limit(self):
        r = validate_sql(
            "SELECT brand, SUM(revenue) AS r FROM chatbot_mv_market_daily "
            "GROUP BY brand ORDER BY r DESC LIMIT 10"
        )
        assert r.ok, r.reason

    def test_trailing_semicolon_allowed(self):
        r = validate_sql("SELECT brand FROM chatbot_mv_market_daily;")
        assert r.ok, r.reason

    def test_string_literal_with_keyword(self):
        # "delete" inside a string is fine.
        r = validate_sql(
            "SELECT product_name FROM complete_market_scrapper_dataset "
            "WHERE product_name = 'Delete Me'"
        )
        assert r.ok, r.reason


# --------------------------- validate_sql: rejects ---------------------------

class TestValidateRejects:
    def test_empty(self):
        assert validate_sql("").ok is False
        assert validate_sql("   ").ok is False

    def test_comment_dashdash(self):
        r = validate_sql("SELECT 1 FROM chatbot_mv_market_daily -- evil")
        assert not r.ok
        assert "comment" in r.reason.lower()

    def test_comment_block(self):
        r = validate_sql("SELECT /* hi */ brand FROM chatbot_mv_market_daily")
        assert not r.ok

    def test_statement_stacking(self):
        r = validate_sql(
            "SELECT 1 FROM chatbot_mv_market_daily; DROP TABLE chatbot_mv_market_daily"
        )
        assert not r.ok

    def test_insert(self):
        r = validate_sql("INSERT INTO chatbot_mv_market_daily (brand) VALUES ('x')")
        assert not r.ok

    def test_update(self):
        r = validate_sql("UPDATE chatbot_mv_market_daily SET brand='x'")
        assert not r.ok

    def test_delete(self):
        r = validate_sql("DELETE FROM chatbot_mv_market_daily")
        assert not r.ok

    def test_drop(self):
        r = validate_sql("DROP TABLE chatbot_mv_market_daily")
        assert not r.ok

    def test_set_role(self):
        r = validate_sql("SET ROLE postgres")
        assert not r.ok

    def test_pg_sleep(self):
        r = validate_sql("SELECT pg_sleep(10) FROM chatbot_mv_market_daily")
        assert not r.ok
        assert "pg_sleep" in r.reason.lower()

    def test_current_setting_blocked(self):
        # Bot must not be able to read app.tenant_id / app.states.
        r = validate_sql("SELECT current_setting('app.tenant_id')")
        assert not r.ok

    def test_information_schema(self):
        r = validate_sql("SELECT table_name FROM information_schema.tables")
        assert not r.ok
        assert "system catalog" in r.reason.lower() or "not allowed" in r.reason.lower()

    def test_pg_catalog(self):
        r = validate_sql("SELECT * FROM pg_class")
        assert not r.ok

    def test_table_not_allowlisted(self):
        r = validate_sql("SELECT * FROM rhize_orders")
        assert not r.ok
        assert "not allowed" in r.reason.lower()

    def test_subquery_to_disallowed_table(self):
        r = validate_sql(
            "SELECT brand FROM chatbot_mv_market_daily WHERE brand IN "
            "(SELECT brand FROM rhize_orders)"
        )
        assert not r.ok

    def test_malformed_sql(self):
        r = validate_sql("SELEC brand FROMM chatbot_mv_market_daily")
        assert not r.ok


# --------------------------- assert_read_only ---------------------------

class TestAssertReadOnly:
    def test_passes_select(self):
        assert_read_only("SELECT 1 FROM chatbot_mv_market_daily")

    def test_passes_with(self):
        assert_read_only(
            "WITH t AS (SELECT 1 AS x) SELECT x FROM t"
        )

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            assert_read_only("")

    def test_rejects_insert(self):
        with pytest.raises(ValueError):
            assert_read_only("INSERT INTO x VALUES (1)")

    def test_rejects_stacking(self):
        with pytest.raises(ValueError):
            assert_read_only("SELECT 1; DROP TABLE x")

    def test_rejects_comments(self):
        with pytest.raises(ValueError):
            assert_read_only("SELECT 1 -- hi")

    def test_rejects_pg_sleep(self):
        with pytest.raises(ValueError):
            assert_read_only("SELECT pg_sleep(5)")


# --------------------------- enforce_limit ---------------------------

class TestEnforceLimit:
    def test_appends_when_missing(self):
        out = enforce_limit("SELECT brand FROM chatbot_mv_market_daily")
        assert out.endswith("LIMIT 500")

    def test_respects_existing(self):
        sql = "SELECT brand FROM chatbot_mv_market_daily LIMIT 10"
        assert enforce_limit(sql) == sql

    def test_strips_trailing_semicolon(self):
        out = enforce_limit("SELECT 1 FROM chatbot_mv_market_daily;")
        assert ";" not in out
        assert out.endswith("LIMIT 500")

    def test_custom_max(self):
        out = enforce_limit("SELECT 1 FROM chatbot_mv_market_daily", max_rows=50)
        assert out.endswith("LIMIT 50")

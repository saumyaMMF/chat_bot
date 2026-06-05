"""Tests for the PG vs MySQL engine router."""

from __future__ import annotations

import pytest

from app.chatbot.engine_router import route_engine


def test_pg_table_routes_pg():
    r = route_engine("SELECT * FROM chatbot_mv_market_daily")
    assert r.ok and r.engine == "pg"


def test_mysql_table_routes_mysql():
    r = route_engine("SELECT id FROM rhize_orders")
    assert r.ok and r.engine == "mysql"


def test_cross_engine_join_rejected():
    sql = "SELECT * FROM rhize_orders o JOIN chatbot_mv_market_daily m ON o.id = m.id"
    r = route_engine(sql)
    assert not r.ok
    assert "cross-engine" in r.reason.lower()


def test_unknown_table_rejected():
    r = route_engine("SELECT * FROM some_random_table")
    assert not r.ok
    assert "not allowed" in r.reason.lower()


def test_system_catalog_rejected():
    r = route_engine("SELECT * FROM information_schema.tables")
    assert not r.ok


def test_pg_system_catalog_rejected():
    r = route_engine("SELECT * FROM pg_stat_activity")
    assert not r.ok


def test_cte_alias_not_treated_as_table():
    sql = "WITH x AS (SELECT id FROM rhize_orders) SELECT * FROM x"
    r = route_engine(sql)
    assert r.ok and r.engine == "mysql"


def test_unparseable_rejected():
    r = route_engine("not sql at all just words")
    assert not r.ok


def test_multiple_mysql_tables():
    sql = "SELECT * FROM rhize_orders o JOIN rhize_stores s ON o.storeId = s.id"
    r = route_engine(sql)
    assert r.ok and r.engine == "mysql"
    assert set(r.tables) == {"rhize_orders", "rhize_stores"}

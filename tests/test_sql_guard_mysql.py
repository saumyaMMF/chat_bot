"""Tests for the MySQL guard. Focus on tenant injection + deny patterns."""

from __future__ import annotations

import re

import pytest

from app.chatbot.sql_guard_mysql import (
    ALLOWED_MYSQL_TABLES,
    assert_read_only_mysql,
    enforce_limit_mysql,
    validate_mysql_sql,
)


VALID_TENANT = 1
INVALID_TENANT = 42  # not in CHATBOT_VALID_TENANT_IDS default (1,3,99)


# ---------- allow / pass-through ----------

def test_simple_select_passes_and_injects_tenantid():
    r = validate_mysql_sql("SELECT customerName FROM rhize_orders WHERE status = 'Completed'", VALID_TENANT)
    assert r.ok, r.reason
    assert re.search(r"tenantid\s*=\s*1", r.sql, re.IGNORECASE)
    assert "rhize_orders" in r.sql


def test_join_injects_on_each_table():
    sql = "SELECT o.id, s.name FROM rhize_orders AS o JOIN rhize_stores AS s ON o.storeId = s.id"
    r = validate_mysql_sql(sql, VALID_TENANT)
    assert r.ok, r.reason
    # both aliases must get a tenantid predicate
    assert re.search(r"o\.tenantid\s*=\s*1", r.sql, re.IGNORECASE)
    assert re.search(r"s\.tenantid\s*=\s*1", r.sql, re.IGNORECASE)


def test_existing_where_is_anded_not_replaced():
    sql = "SELECT id FROM rhize_orders WHERE status = 'Completed'"
    r = validate_mysql_sql(sql, VALID_TENANT)
    assert r.ok, r.reason
    assert "status" in r.sql.lower()
    assert re.search(r"tenantid\s*=\s*1", r.sql, re.IGNORECASE)


def test_count_aggregate_passes():
    r = validate_mysql_sql("SELECT COUNT(*) AS n FROM rhize_orders", VALID_TENANT)
    assert r.ok, r.reason
    assert re.search(r"tenantid\s*=\s*1", r.sql, re.IGNORECASE)


# ---------- deny ----------

@pytest.mark.parametrize(
    "sql,fragment",
    [
        ("UPDATE rhize_orders SET status='x'", "select"),
        ("DELETE FROM rhize_orders", "select"),
        ("DROP TABLE rhize_orders", "select"),
        ("INSERT INTO rhize_orders (id) VALUES ('x')", "select"),
    ],
)
def test_non_select_rejected(sql, fragment):
    r = validate_mysql_sql(sql, VALID_TENANT)
    assert not r.ok
    assert fragment in r.reason.lower() or "keyword" in r.reason.lower()


def test_comment_rejected():
    r = validate_mysql_sql("SELECT id FROM rhize_orders -- comment", VALID_TENANT)
    assert not r.ok
    assert "comment" in r.reason.lower()


def test_statement_stacking_rejected():
    r = validate_mysql_sql("SELECT 1 FROM rhize_orders; SELECT 1 FROM rhize_orders", VALID_TENANT)
    assert not r.ok
    assert "single statement" in r.reason.lower()


def test_union_rejected():
    sql = "SELECT id FROM rhize_orders UNION SELECT id FROM rhize_brands"
    r = validate_mysql_sql(sql, VALID_TENANT)
    assert not r.ok


def test_information_schema_rejected():
    r = validate_mysql_sql("SELECT * FROM information_schema.tables", VALID_TENANT)
    assert not r.ok
    assert "information_schema" in r.reason.lower()


def test_mysql_schema_rejected():
    r = validate_mysql_sql("SELECT user FROM mysql.user", VALID_TENANT)
    assert not r.ok


def test_into_outfile_rejected():
    r = validate_mysql_sql("SELECT id FROM rhize_orders INTO OUTFILE '/tmp/x'", VALID_TENANT)
    assert not r.ok


def test_load_file_rejected():
    r = validate_mysql_sql("SELECT LOAD_FILE('/etc/passwd') FROM rhize_orders", VALID_TENANT)
    assert not r.ok


def test_sleep_rejected():
    r = validate_mysql_sql("SELECT SLEEP(10) FROM rhize_orders", VALID_TENANT)
    assert not r.ok


def test_unknown_table_rejected():
    r = validate_mysql_sql("SELECT * FROM not_a_real_table", VALID_TENANT)
    assert not r.ok
    assert "not allowed" in r.reason.lower()


def test_invalid_tenant_rejected():
    r = validate_mysql_sql("SELECT id FROM rhize_orders", INVALID_TENANT)
    assert not r.ok
    assert "tenant" in r.reason.lower()


def test_empty_sql_rejected():
    assert not validate_mysql_sql("", VALID_TENANT).ok
    assert not validate_mysql_sql("   ", VALID_TENANT).ok


# ---------- read-only assertion ----------

def test_assert_read_only_passes_select():
    assert_read_only_mysql("SELECT id FROM rhize_orders WHERE tenantid = 1")


def test_assert_read_only_blocks_update():
    with pytest.raises(ValueError):
        assert_read_only_mysql("UPDATE rhize_orders SET status='x'")


def test_assert_read_only_blocks_comment():
    with pytest.raises(ValueError):
        assert_read_only_mysql("SELECT 1 FROM rhize_orders -- x")


# ---------- enforce_limit ----------

def test_enforce_limit_appends_when_missing():
    out = enforce_limit_mysql("SELECT id FROM rhize_orders")
    assert out.endswith("LIMIT 500")


def test_enforce_limit_preserves_existing():
    out = enforce_limit_mysql("SELECT id FROM rhize_orders LIMIT 10")
    assert out.lower().endswith("limit 10")


# ---------- allow-list sanity ----------

def test_allowed_tables_count():
    assert len(ALLOWED_MYSQL_TABLES) == 10

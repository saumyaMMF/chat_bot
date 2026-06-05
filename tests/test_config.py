"""Tests for the env-driven settings loader."""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture(autouse=True)
def _reset_cache():
    # get_settings is lru_cached. Bust between tests so env changes apply.
    from app import config
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def test_defaults_when_env_missing(monkeypatch):
    for k in [
        "DATABASE_URL_RO",
        "CHATBOT_LLM_BASE_URL",
        "CHATBOT_LLM_MODEL",
        "CHATBOT_LLM_API_KEY",
        "CHATBOT_LLM_TIMEOUT_MS",
        "CHATBOT_TOP_K",
        "CHATBOT_ROW_LIMIT",
        "CHATBOT_STATEMENT_TIMEOUT_MS",
    ]:
        monkeypatch.delenv(k, raising=False)
    # Skip .env file lookup so machine-local .env doesn't pollute.
    monkeypatch.chdir("/")
    from app.config import Settings
    s = Settings(_env_file=None)
    assert s.database_url_ro is None
    assert s.llm_base_url == "http://localhost:11434/v1"
    assert "qwen2.5-coder" in s.llm_model
    assert s.llm_timeout_ms == 55_000
    assert s.row_limit == 500
    assert s.statement_timeout_ms == 5_000


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("DATABASE_URL_RO", "postgres://x:y@h:5432/d")
    monkeypatch.setenv("CHATBOT_LLM_MODEL", "custom-model")
    monkeypatch.setenv("CHATBOT_ROW_LIMIT", "123")
    from app.config import Settings
    s = Settings(_env_file=None)
    assert s.database_url_ro == "postgres://x:y@h:5432/d"
    assert s.llm_model == "custom-model"
    assert s.row_limit == 123

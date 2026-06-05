"""Tests for schema_store: pure load + format helpers.

Retrieval (KNN) requires DB + embedding model — covered by integration tests
gated on DATABASE_URL_RO + Ollama, not here."""

from __future__ import annotations

from app.chatbot import schema_store as ss
from app.chatbot.embed_client import to_pgvector_literal


class TestLoadDefinitions:
    def test_loads_items(self):
        items = ss.load_definitions()
        assert len(items) > 0

    def test_has_table_rows(self):
        items = ss.load_definitions()
        assert any(i.kind in {"table", "view"} for i in items)

    def test_has_column_rows(self):
        items = ss.load_definitions()
        assert any(i.kind == "column" for i in items)

    def test_required_fields(self):
        for i in ss.load_definitions():
            assert i.id and i.kind and i.table_name and i.definition

    def test_market_table_present(self):
        items = ss.load_definitions()
        ids = {i.id for i in items}
        assert "table:complete_market_scrapper_dataset" in ids
        assert "table:chatbot_mv_market_daily" in ids


class TestEmbedText:
    def test_table_embed_text_shape(self):
        items = {i.id: i for i in ss.load_definitions()}
        t = items["table:chatbot_mv_market_daily"]
        text = t.embed_text
        assert "VIEW chatbot_mv_market_daily" in text
        assert "Security-barrier view" in text

    def test_column_embed_text_shape(self):
        items = {i.id: i for i in ss.load_definitions()}
        c = items.get("col:chatbot_mv_market_daily.brand")
        assert c is not None
        text = c.embed_text
        assert "COLUMN chatbot_mv_market_daily.brand" in text
        assert "(TEXT)" in text

    def test_includes_restrictions_when_present(self):
        item = ss.SchemaItem(
            id="x", kind="column", table_name="t", column_name="c",
            data_type="TEXT", definition="d", restrictions="don't do X",
        )
        assert "Restrictions: don't do X" in item.embed_text


class TestFormatChunksForPrompt:
    def test_empty(self):
        assert ss.format_chunks_for_prompt([]).startswith("(no schema")

    def test_tables_before_columns(self):
        chunks = [
            ss.SchemaChunk(id="c1", kind="column", table_name="t",
                           column_name="x", data_type="TEXT",
                           definition="cdef", restrictions="", distance=0.1),
            ss.SchemaChunk(id="t1", kind="table", table_name="t",
                           column_name=None, data_type=None,
                           definition="tdef", restrictions="", distance=0.2),
        ]
        out = ss.format_chunks_for_prompt(chunks)
        # the "### t (TABLE)" header appears before the "### t — columns" header
        assert out.index("### t (TABLE)") < out.index("### t — columns")

    def test_renders_restrict_when_present(self):
        chunks = [
            ss.SchemaChunk(id="t1", kind="table", table_name="t",
                           column_name=None, data_type=None,
                           definition="d", restrictions="no writes",
                           distance=0.0),
        ]
        out = ss.format_chunks_for_prompt(chunks)
        assert "RESTRICT: no writes" in out

    def test_omits_restrict_when_blank(self):
        chunks = [
            ss.SchemaChunk(id="t1", kind="view", table_name="v",
                           column_name=None, data_type=None,
                           definition="d", restrictions="", distance=0.0),
        ]
        out = ss.format_chunks_for_prompt(chunks)
        assert "RESTRICT:" not in out

    def test_column_renders_data_type(self):
        chunks = [
            ss.SchemaChunk(id="c", kind="column", table_name="t",
                           column_name="brand", data_type="TEXT",
                           definition="brand col", restrictions="",
                           distance=0.0),
        ]
        out = ss.format_chunks_for_prompt(chunks)
        assert "- **brand** (TEXT): brand col" in out


class TestCollectRestrictions:
    def test_empty(self):
        assert ss.collect_restrictions([]) == []

    def test_dedupes_and_preserves_order(self):
        chunks = [
            ss.SchemaChunk(id="1", kind="table", table_name="t",
                           column_name=None, data_type=None, definition="d",
                           restrictions="A", distance=0.0),
            ss.SchemaChunk(id="2", kind="column", table_name="t",
                           column_name="x", data_type="TEXT", definition="d",
                           restrictions="A", distance=0.1),
            ss.SchemaChunk(id="3", kind="column", table_name="t",
                           column_name="y", data_type="TEXT", definition="d",
                           restrictions="B", distance=0.2),
        ]
        assert ss.collect_restrictions(chunks) == ["A", "B"]

    def test_skips_empty(self):
        chunks = [
            ss.SchemaChunk(id="1", kind="column", table_name="t",
                           column_name="x", data_type="TEXT", definition="d",
                           restrictions="", distance=0.0),
            ss.SchemaChunk(id="2", kind="column", table_name="t",
                           column_name="y", data_type="TEXT", definition="d",
                           restrictions="   ", distance=0.1),
        ]
        assert ss.collect_restrictions(chunks) == []


class TestPgvectorLiteral:
    def test_format(self):
        assert to_pgvector_literal([1.0, 2.0, 3.5]).startswith("[")
        assert to_pgvector_literal([1.0, 2.0]).endswith("]")
        out = to_pgvector_literal([0.1, 0.2])
        # should round-trip into pg as a text literal
        assert out.count(",") == 1

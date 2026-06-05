-- 006_schema_embeddings.sql
--
-- Schema-RAG store. Each row is one curated piece of schema knowledge — a
-- table description or a column definition + restrictions — embedded with
-- nomic-embed-text (768 dims). At request time the chatbot embeds the user's
-- question, KNN-searches this table, and injects the top-k chunks into the
-- prompt (replacing the static schema_context.md dump).
--
-- Requires the pgvector extension (already provisioned by sql/005_pgvector_examples.sql).
--
-- Ingest is handled by scripts/ingest_schema.py — it reads data/schema_definitions.json,
-- embeds each item, and upserts here.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chatbot_schema_embeddings (
  id            TEXT PRIMARY KEY,
  kind          TEXT NOT NULL,          -- 'table' | 'view' | 'column'
  table_name    TEXT NOT NULL,
  column_name   TEXT,                   -- NULL when kind in ('table','view')
  data_type     TEXT,                   -- NULL for non-column rows
  definition    TEXT NOT NULL,
  restrictions  TEXT NOT NULL DEFAULT '',
  embedding     vector(768) NOT NULL,   -- nomic-embed-text dim
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Cosine-distance ANN index. ivfflat needs ANALYZE after the first load
-- (ingest CLI does it). 100 lists is the right scale for ~10^3 rows.
CREATE INDEX IF NOT EXISTS chatbot_schema_embeddings_emb_idx
  ON chatbot_schema_embeddings
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE INDEX IF NOT EXISTS chatbot_schema_embeddings_table_idx
  ON chatbot_schema_embeddings (table_name);

-- The chatbot_ro role needs SELECT — retrieval runs on the RO pool too,
-- since schema docs are reference data (not tenant-scoped).
GRANT SELECT ON chatbot_schema_embeddings TO chatbot_ro;

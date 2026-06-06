-- ============================================================================
-- Migration 007 — pgvector storage for chatbot fast-path question cache.
--
-- Curated Q->SQL pairs (data/fast_path_questions.json) embedded with
-- nomic-embed-text. At request time the bot embeds the user's question and
-- looks up the nearest neighbour by cosine distance. If similarity is high
-- enough (distance <= CHATBOT_FAST_PATH_DISTANCE_THRESHOLD, default 0.18),
-- the cached SQL is run directly — LLM call is skipped.
--
-- MVP wiring (chat_service): literal pairs only (params=[]). Templated pairs
-- are still embedded so the catalog is complete, but the runtime currently
-- skips any hit whose sql contains `{...}` placeholders.
--
-- Defense in depth: cached SQL still flows through sqlGuard (validate_sql)
-- + RLS / tenantid scope + limit + statement_timeout. This table is a cache,
-- not a trust boundary.
--
-- Idempotent. Apply as table owner. Safe to re-run.
-- ============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chatbot_fast_path_embeddings (
  id            text        PRIMARY KEY,                -- group:index, e.g. "market_categories:003"
  group_name    text        NOT NULL,
  question      text        NOT NULL,
  sql           text,                                   -- NULL when refusal
  refusal       text,                                   -- NULL when SQL
  dialect       text        NOT NULL CHECK (dialect IN ('postgres','mysql','any')),
  params        jsonb       NOT NULL DEFAULT '[]'::jsonb,
  embedding     vector(768) NOT NULL,
  prompt_hash   text        NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fast_path_embedding_cosine
  ON chatbot_fast_path_embeddings
  USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_fast_path_prompt_hash
  ON chatbot_fast_path_embeddings (prompt_hash);

CREATE INDEX IF NOT EXISTS idx_fast_path_dialect
  ON chatbot_fast_path_embeddings (dialect);

GRANT SELECT ON chatbot_fast_path_embeddings TO chatbot_ro;

DO $$
DECLARE
  ext_exists boolean;
  tbl_exists boolean;
BEGIN
  SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') INTO ext_exists;
  SELECT EXISTS (SELECT 1 FROM information_schema.tables
                 WHERE table_schema = 'public' AND table_name = 'chatbot_fast_path_embeddings')
    INTO tbl_exists;

  IF NOT ext_exists THEN RAISE EXCEPTION 'vector extension missing'; END IF;
  IF NOT tbl_exists THEN RAISE EXCEPTION 'chatbot_fast_path_embeddings missing'; END IF;
  RAISE NOTICE 'OK: chatbot_fast_path_embeddings ready';
END
$$;

COMMIT;

-- Rollback:
-- DROP TABLE IF EXISTS chatbot_fast_path_embeddings;

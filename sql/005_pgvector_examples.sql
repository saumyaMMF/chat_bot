-- ============================================================================
-- Migration 005 — pgvector storage for chatbot few-shot example embeddings.
--
-- Enables dynamic top-k example retrieval: at request time, the bot embeds the
-- user's question and pulls the 3-5 most similar examples by cosine distance,
-- instead of stuffing all 25 examples into the prompt every turn. Drops the
-- assembled prompt from ~5400 tokens to ~1500.
--
-- This table holds the embeddings produced offline by
-- scripts/embed-chatbot-examples.ts from chatbot/examples.json. The
-- embeddings come from the nomic-embed-text Ollama model (768 dim).
--
-- Idempotent. Apply as the table owner (doadmin). Safe to re-run.
-- ============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chatbot_example_embeddings (
  id            text        PRIMARY KEY,                -- stable id from examples.json (kebab-case)
  question      text        NOT NULL,
  sql           text,                                   -- NULL when the example is a refusal
  refusal       text,                                   -- NULL when the example is SQL
  expected_kind text        NOT NULL CHECK (expected_kind IN ('result','refusal','chat')),
  embedding     vector(768) NOT NULL,                   -- nomic-embed-text output dim
  prompt_hash   text        NOT NULL,                   -- ties row to a specific examples.json version
  created_at    timestamptz NOT NULL DEFAULT now()
);

-- HNSW index for cosine KNN. Overkill at 25 rows; future-proofs against growth.
-- vector_cosine_ops = cosine distance (use <=> operator on queries).
CREATE INDEX IF NOT EXISTS idx_example_embedding_cosine
  ON chatbot_example_embeddings
  USING hnsw (embedding vector_cosine_ops);

-- Index for stale-row cleanup by prompt_hash mismatch.
CREATE INDEX IF NOT EXISTS idx_example_prompt_hash
  ON chatbot_example_embeddings (prompt_hash);

-- chatbot_ro reads the table to pick top-k. Reference data, not tenant-scoped.
GRANT SELECT ON chatbot_example_embeddings TO chatbot_ro;

-- ── Verification before commit ─────────────────────────────────────────────
DO $$
DECLARE
  ext_exists boolean;
  tbl_exists boolean;
BEGIN
  SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') INTO ext_exists;
  SELECT EXISTS (SELECT 1 FROM information_schema.tables
                 WHERE table_schema = 'public' AND table_name = 'chatbot_example_embeddings')
    INTO tbl_exists;

  IF NOT ext_exists THEN RAISE EXCEPTION 'vector extension missing'; END IF;
  IF NOT tbl_exists THEN RAISE EXCEPTION 'chatbot_example_embeddings missing'; END IF;
  RAISE NOTICE 'OK: vector extension + chatbot_example_embeddings ready';
END
$$;

COMMIT;

-- ── Rollback (manual; run only if reverting) ───────────────────────────────
-- DROP TABLE IF EXISTS chatbot_example_embeddings;
-- DROP EXTENSION IF EXISTS vector;

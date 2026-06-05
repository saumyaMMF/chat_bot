-- ============================================================================
-- Gate A — read-only Postgres role for the NL→SQL chatbot.
-- ============================================================================
-- The chatbot connects ONLY as this role (DATABASE_URL_RO). It can SELECT but
-- never write, so even if the model emits DELETE/DROP the engine rejects it.
--
-- APPLY AS: a superuser / database owner.
-- REVIEW BEFORE RUNNING. Replace the password placeholder.
-- Rollback: see rollback.sql.
--
-- NOTE: set <DBNAME> to the actual database (the app's DATABASE_URL database).
--       The plan refers to it as `rhize_intel`; confirm with `\conninfo`.
-- ============================================================================

\set ON_ERROR_STOP on

-- 1. Create the login role. Use a strong, unique password (NOT the app's).
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'chatbot_ro') THEN
    CREATE ROLE chatbot_ro LOGIN PASSWORD 'REPLACE_WITH_STRONG_PASSWORD';
  ELSE
    RAISE NOTICE 'role chatbot_ro already exists — skipping CREATE';
  END IF;
END
$$;

-- 2. Connect + schema usage.
GRANT CONNECT ON DATABASE :"DBNAME" TO chatbot_ro;   -- run with: psql -v DBNAME=rhize_intel
GRANT USAGE   ON SCHEMA public      TO chatbot_ro;

-- 3. SELECT only — no INSERT/UPDATE/DELETE/TRUNCATE, ever.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO chatbot_ro;

-- 4. Future tables created by the app owner are also SELECT-only for the bot.
--    (Run as the role that OWNS the tables, else this has no effect.)
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO chatbot_ro;

-- 5. Belt-and-suspenders: explicitly revoke write/DDL surface.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER
  ON ALL TABLES IN SCHEMA public FROM chatbot_ro;
REVOKE CREATE ON SCHEMA public FROM chatbot_ro;

-- 6. chatbot_ro must NOT be allowed to bypass Row-Level Security.
--    (Only superusers and BYPASSRLS roles bypass it; ensure neither applies.)
ALTER ROLE chatbot_ro NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE;

-- Verify (run manually as chatbot_ro after applying 002/003):
--   SET ROLE chatbot_ro;
--   INSERT INTO rhize_orders DEFAULT VALUES;   -- must FAIL: permission denied
--   RESET ROLE;

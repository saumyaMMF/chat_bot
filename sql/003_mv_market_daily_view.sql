-- ============================================================================
-- Gate B (cont.) — state isolation for the materialized view mv_market_daily.
-- ============================================================================
-- Postgres CANNOT enable Row-Level Security on a materialized view. So the
-- chatbot must NOT read mv_market_daily directly. Instead it reads a
-- security_barrier view that filters by app.states the same way the base-table
-- RLS policy does.
--
-- CONSEQUENCE: the chatbot allow-list must reference `chatbot_mv_market_daily`
-- (this view), NOT `mv_market_daily`. Two coordinated changes are required:
--   1. sqlGuard.ts ALLOWED_TABLES: replace 'mv_market_daily'
--      with 'chatbot_mv_market_daily'.
--   2. schema_context.md / examples.json: tell the model to use
--      `chatbot_mv_market_daily` for pre-aggregated market reads.
-- (Do NOT grant the bot SELECT on the raw mv_market_daily.)
--
-- APPLY AS: the owner. Assumes mv_market_daily has a `state` column.
-- ============================================================================

\set ON_ERROR_STOP on

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'mv_market_daily'
      AND column_name = 'state'
  ) THEN
    RAISE WARNING
      'mv_market_daily has no state column — chatbot_mv_market_daily view NOT created. Exclude pre-aggregated market reads from the bot.';
    RETURN;
  END IF;

  EXECUTE $v$
    CREATE OR REPLACE VIEW public.chatbot_mv_market_daily
      WITH (security_barrier = true) AS
      SELECT *
      FROM public.mv_market_daily
      WHERE state = ANY (
        string_to_array(NULLIF(current_setting('app.states', true), ''), ',')
      )
  $v$;

  -- Bot can read the filtered view; raw MV stays inaccessible to it.
  EXECUTE 'GRANT SELECT ON public.chatbot_mv_market_daily TO chatbot_ro';
  EXECUTE 'REVOKE SELECT ON public.mv_market_daily FROM chatbot_ro';

  RAISE NOTICE 'OK: chatbot_mv_market_daily security_barrier view created';
END
$$;

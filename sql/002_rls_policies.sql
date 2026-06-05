-- ============================================================================
-- Gate B — Row-Level Security. The real tenant/state isolation wall.
-- ============================================================================
-- Per request the chatbot's connection sets (server-side, from the auth cookie,
-- NEVER from the model):
--     SET LOCAL app.tenant_id = '<tenantId>';
--     SET LOCAL app.states    = 'VT,MA';
-- After that, every row the bot can see is physically filtered by the engine,
-- regardless of what SQL the model wrote.
--
-- This script is COLUMN-AWARE and FAIL-SAFE: for each table it checks that the
-- expected scoping column exists. If it does NOT, the table is left WITHOUT a
-- policy and a WARNING is raised — that table must then be EXCLUDED from the
-- chatbot allow-list (lib/chatbot/sqlGuard.ts ALLOWED_TABLES) until fixed,
-- because it cannot be isolated.
--
-- Materialized view `mv_market_daily` is handled separately in 003 (Postgres
-- does not support RLS on materialized views).
--
-- APPLY AS: the table owner (RLS DDL requires ownership). REVIEW FIRST.
-- Idempotent: safe to re-run (drops+recreates each policy).
-- ============================================================================

\set ON_ERROR_STOP on

-- ── Tenant-scoped tables: isolate by integer `tenantid` column ───────────────
DO $$
DECLARE
  t text;
  tenant_tables text[] := ARRAY[
    'rhize_dataset_main',
    'rhize_dataset_store',
    'rhize_brands',
    'rhize_partner_stores',
    'rhize_orders',
    'rhize_live_inventory',
    'rhize_product_lots',
    'rhize_stores',
    'rhize_strain_info',
    'rhize_sales_actions'
  ];
BEGIN
  FOREACH t IN ARRAY tenant_tables LOOP
    -- table must exist
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'public' AND table_name = t
    ) THEN
      RAISE WARNING 'SKIP %: table does not exist', t;
      CONTINUE;
    END IF;

    -- scoping column must exist, else we cannot isolate it
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema = 'public' AND table_name = t AND column_name = 'tenantid'
    ) THEN
      RAISE WARNING
        'SKIP %: no tenantid column — NOT isolated. EXCLUDE from chatbot allow-list until fixed.',
        t;
      CONTINUE;
    END IF;

    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE public.%I FORCE  ROW LEVEL SECURITY', t);
    EXECUTE format('DROP POLICY IF EXISTS chatbot_tenant_isolation ON public.%I', t);
    -- NULLIF guards against an unset GUC raising; a missing setting yields NULL
    -- which makes the predicate false (fail closed: no rows).
    EXECUTE format($f$
      CREATE POLICY chatbot_tenant_isolation ON public.%I
        FOR SELECT TO chatbot_ro
        USING (tenantid = NULLIF(current_setting('app.tenant_id', true), '')::int)
    $f$, t);

    RAISE NOTICE 'OK %: tenant RLS enabled', t;
  END LOOP;
END
$$;

-- ── State-scoped market base table: isolate by text `state` column ───────────
DO $$
DECLARE
  t text := 'complete_market_scrapper_dataset';
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = t
  ) THEN
    RAISE WARNING 'SKIP %: table does not exist', t;
    RETURN;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = t AND column_name = 'state'
  ) THEN
    RAISE WARNING 'SKIP %: no state column — NOT isolated. EXCLUDE from chatbot allow-list.', t;
    RETURN;
  END IF;

  EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
  EXECUTE format('ALTER TABLE public.%I FORCE  ROW LEVEL SECURITY', t);
  EXECUTE format('DROP POLICY IF EXISTS chatbot_state_isolation ON public.%I', t);
  -- app.states is a comma-separated list, e.g. 'VT,MA'. Empty/unset → no rows.
  EXECUTE format($f$
    CREATE POLICY chatbot_state_isolation ON public.%I
      FOR SELECT TO chatbot_ro
      USING (state = ANY (string_to_array(NULLIF(current_setting('app.states', true), ''), ',')))
  $f$, t);

  RAISE NOTICE 'OK %: state RLS enabled', t;
END
$$;

-- Verify (as chatbot_ro, after setting the GUCs in a transaction):
--   BEGIN;
--   SET LOCAL app.tenant_id = '3';
--   SET LOCAL app.states    = 'MA';
--   SELECT DISTINCT tenantid FROM rhize_orders;                 -- only 3
--   SELECT DISTINCT state    FROM complete_market_scrapper_dataset; -- only MA
--   ROLLBACK;

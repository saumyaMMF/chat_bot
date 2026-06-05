-- ============================================================================
-- Rollback for the chatbot security migration (001–003). Reverses Gate A + B.
-- APPLY AS: the table/role owner. Review before running.
-- ============================================================================

\set ON_ERROR_STOP on

-- 003 — drop the security_barrier view.
DROP VIEW IF EXISTS public.chatbot_mv_market_daily;

-- 002 — drop policies and disable RLS on every table that may have it.
DO $$
DECLARE
  t text;
  all_tables text[] := ARRAY[
    'rhize_dataset_main','rhize_dataset_store','rhize_brands','rhize_partner_stores',
    'rhize_orders','rhize_live_inventory','rhize_product_lots','rhize_stores',
    'rhize_strain_info','rhize_sales_actions','complete_market_scrapper_dataset'
  ];
BEGIN
  FOREACH t IN ARRAY all_tables LOOP
    IF EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'public' AND table_name = t
    ) THEN
      EXECUTE format('DROP POLICY IF EXISTS chatbot_tenant_isolation ON public.%I', t);
      EXECUTE format('DROP POLICY IF EXISTS chatbot_state_isolation  ON public.%I', t);
      EXECUTE format('ALTER TABLE public.%I NO FORCE ROW LEVEL SECURITY', t);
      EXECUTE format('ALTER TABLE public.%I DISABLE  ROW LEVEL SECURITY', t);
    END IF;
  END LOOP;
END
$$;

-- 001 — drop the role. Must revoke its grants first; fails if it owns objects.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'chatbot_ro') THEN
    EXECUTE 'REVOKE ALL ON ALL TABLES IN SCHEMA public FROM chatbot_ro';
    EXECUTE 'REVOKE ALL ON SCHEMA public FROM chatbot_ro';
    EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE SELECT ON TABLES FROM chatbot_ro';
    EXECUTE 'DROP ROLE chatbot_ro';
  END IF;
END
$$;

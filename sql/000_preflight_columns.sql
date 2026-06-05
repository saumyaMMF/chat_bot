-- ============================================================================
-- Preflight — run FIRST. Read-only. Confirms the scoping columns actually exist
-- on every table the chatbot will touch, so you know which tables RLS can
-- isolate before you apply 001–003.
-- ============================================================================
-- Any tenant table showing has_tenantid = false, or the market table showing
-- has_state = false, CANNOT be isolated and must be removed from the chatbot
-- allow-list (lib/chatbot/sqlGuard.ts ALLOWED_TABLES) until the column is added.
-- ============================================================================

-- Tenant-scoped tables — expect has_tenantid = true for all.
SELECT
  t.tbl AS table_name,
  EXISTS (
    SELECT 1 FROM information_schema.columns c
    WHERE c.table_schema = 'public' AND c.table_name = t.tbl AND c.column_name = 'tenantid'
  ) AS has_tenantid,
  EXISTS (
    SELECT 1 FROM information_schema.tables it
    WHERE it.table_schema = 'public' AND it.table_name = t.tbl
  ) AS table_exists
FROM (VALUES
  ('rhize_dataset_main'), ('rhize_dataset_store'), ('rhize_brands'),
  ('rhize_partner_stores'), ('rhize_orders'), ('rhize_live_inventory'),
  ('rhize_product_lots'), ('rhize_stores'), ('rhize_strain_info'),
  ('rhize_sales_actions')
) AS t(tbl)
ORDER BY has_tenantid, t.tbl;

-- State-scoped market objects — expect has_state = true for both.
SELECT
  t.tbl AS object_name,
  EXISTS (
    SELECT 1 FROM information_schema.columns c
    WHERE c.table_schema = 'public' AND c.table_name = t.tbl AND c.column_name = 'state'
  ) AS has_state
FROM (VALUES
  ('complete_market_scrapper_dataset'), ('mv_market_daily')
) AS t(tbl)
ORDER BY t.tbl;

-- Orphan check — rows that no tenant can see (tenantid IS NULL). Harmless for
-- isolation but flagged in TENANT-ISOLATION-FINDINGS.md.
SELECT 'rhize_dataset_main' AS tbl, count(*) AS null_tenant_rows
  FROM rhize_dataset_main WHERE tenantid IS NULL
UNION ALL
SELECT 'rhize_dataset_store', count(*)
  FROM rhize_dataset_store WHERE tenantid IS NULL;

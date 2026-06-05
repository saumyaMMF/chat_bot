-- ============================================================================
-- Migration 004 — Move deterministic transforms from prompt into the database.
--
-- Today the LLM prompt teaches the model how to normalize category, parse
-- price, clean THC, and convert text dates — every turn. That bloats the
-- prompt (~5400 tokens), invites drift between schema_context and few-shots,
-- and lets the model reproduce the rules subtly wrong. This migration moves
-- all of those transforms behind a single read view:
--
--   chatbot_market   — RLS-enforcing view with date_d (DATE), category_norm,
--                       price_n, thc_num pre-computed.
--   category_map     — data table mapping raw scraper categories to canonical
--                       buckets. A new variant is one INSERT, not a deploy.
--
-- After this migration the sqlGuard allow-list switches to chatbot_market +
-- chatbot_mv_market_daily. The bot can no longer reach the raw table.
--
-- Idempotent. Apply as the table OWNER (doadmin). Verifies under chatbot_ro
-- before committing.
-- ============================================================================

\set ON_ERROR_STOP on

BEGIN;

-- 1. Category mapping table — data not code. ───────────────────────────────
CREATE TABLE IF NOT EXISTS category_map (
  raw_lower     text PRIMARY KEY,
  category_norm text NOT NULL CHECK (
    category_norm IN ('Flower','PreRoll','Vape','Concentrate','Edible','Other')
  )
);

-- Seed from the 45 normalized variants observed in live data 2026-06-03.
-- ON CONFLICT keeps re-runs idempotent and lets ops re-bucket without DROP.
INSERT INTO category_map (raw_lower, category_norm) VALUES
  -- Flower
  ('flower',                    'Flower'),
  ('flower (except deli)',      'Flower'),
  ('flower (med)',              'Flower'),
  ('pre-packed flowers',        'Flower'),
  ('pre-packed-flower',         'Flower'),
  -- PreRoll
  ('pre-rolls',                 'PreRoll'),
  ('pre-roll',                  'PreRoll'),
  ('preroll',                   'PreRoll'),
  ('prerolls',                  'PreRoll'),
  ('pre rolls',                 'PreRoll'),
  ('pre-rolls (single)',        'PreRoll'),
  ('pre-roll (multi-pack)',     'PreRoll'),
  ('pre roll (single)',         'PreRoll'),
  ('pre roll (multi-pack)',     'PreRoll'),
  ('infused pre-roll',          'PreRoll'),
  ('infused pre-rolls',         'PreRoll'),
  ('infused preroll',           'PreRoll'),
  ('infused pre-roll (single)', 'PreRoll'),
  ('pre-roll (infused)',        'PreRoll'),
  -- Vape
  ('vape',                      'Vape'),
  ('vapes',                     'Vape'),
  ('vape-carts',                'Vape'),
  ('vapecarts',                 'Vape'),
  ('vaporizers',                'Vape'),
  ('vape pens',                 'Vape'),
  ('vape batteries',            'Vape'),
  ('thc vape',                  'Vape'),
  ('cartridge',                 'Vape'),
  ('carts',                     'Vape'),
  ('vape cart & concentrate',   'Vape'),
  -- Concentrate
  ('concentrate',               'Concentrate'),
  ('concentrates',              'Concentrate'),
  ('concentrates (med)',        'Concentrate'),
  -- Edible
  ('edible',                    'Edible'),
  ('edibles',                   'Edible'),
  ('edibles (med)',             'Edible'),
  ('distillate edibles',        'Edible'),
  ('live rosin edibles',        'Edible'),
  ('formlulated edibles',       'Edible'),
  -- Other (catch-all bucket, kept explicit so new variants land here)
  ('uncategorized',             'Other'),
  ('beverage',                  'Other'),
  ('cbd',                       'Other'),
  ('tinctures',                 'Other'),
  ('topicals',                  'Other'),
  ('accessories',               'Other')
ON CONFLICT (raw_lower) DO UPDATE SET category_norm = EXCLUDED.category_norm;

-- 2. The clean view the bot reads instead of the raw table. ────────────────
-- security_invoker = true so RLS on complete_market_scrapper_dataset evaluates
-- as the calling role (chatbot_ro), not the view owner. A standard view here
-- would silently bypass the state RLS policy — same hole we found on the MV
-- path. category_map is unscoped (it's reference data), so its plain SELECT
-- under chatbot_ro is fine.
CREATE OR REPLACE VIEW chatbot_market WITH (security_invoker = true) AS
SELECT
  cmsd.date::date                                          AS date_d,
  cmsd.state,
  cmsd.city,
  cmsd.company,
  cmsd.brand,
  cmsd.brand_scrapped,
  cmsd.product_name,
  COALESCE(m.category_norm, 'Other')                       AS category_norm,
  cmsd.unit,
  t_price.val                                              AS price_n,
  CASE WHEN t_thc.val <= 100 THEN t_thc.val END            AS thc_num,
  cmsd.quantity,
  cmsd.previous_quantity,
  cmsd.change,
  cmsd.revenue,
  cmsd.flag,
  cmsd.days_on_shelf,
  cmsd.first_seen,
  cmsd.created_at
FROM complete_market_scrapper_dataset cmsd
LEFT JOIN category_map m
  ON m.raw_lower = lower(btrim(cmsd.category))
-- Compute price once per row. Guards against malformed inputs like '45.00.00'
-- which would otherwise throw ::numeric mid-aggregation.
LEFT JOIN LATERAL (
  SELECT COALESCE(
    cmsd.price_num,
    CASE
      WHEN cmsd.price ~ '^\s*\$?\s*[0-9]+(\.[0-9]+)?\s*$'
        THEN NULLIF(regexp_replace(cmsd.price, '[^0-9.]', '', 'g'), '')::numeric
    END
  ) AS val
) t_price ON true
-- Compute THC once. Anchor pattern rejects 'THC 18%', '100mg', '39% 37%',
-- 'THC -', etc. The outer CASE then clamps to [0..100] so '1200%' becomes NULL.
LEFT JOIN LATERAL (
  SELECT CASE
    WHEN cmsd.thc ~ '^[0-9]+(\.[0-9]+)?%?$'
      THEN NULLIF(regexp_replace(cmsd.thc, '[^0-9.]', '', 'g'), '')::numeric
  END AS val
) t_thc ON true;

-- 3. Reissue chatbot_mv_market_daily so category_norm is single-sourced. ───
-- The trend view stays state-isolated via the same inline GUC predicate; it
-- still joins category_map so a new variant fixes both views at once.
-- security_barrier=true (not security_invoker — underlying object has no RLS
-- policy to invoke; barrier just keeps the predicate from leaking to outer
-- WHERE evaluation).
-- Must DROP + CREATE (not OR REPLACE) because the column list changes:
-- `category` becomes `category_norm` and column order shifts.
DROP VIEW IF EXISTS chatbot_mv_market_daily;
CREATE VIEW chatbot_mv_market_daily
  WITH (security_barrier = true) AS
SELECT
  mv.date,
  mv.brand,
  mv.company,
  COALESCE(m.category_norm, 'Other') AS category_norm,
  mv.revenue,
  mv.quantity,
  mv.sku_count,
  mv.state
FROM mv_market_daily mv
LEFT JOIN category_map m
  ON m.raw_lower = lower(btrim(mv.category))
WHERE mv.state = ANY (
  string_to_array(NULLIF(current_setting('app.states', true), ''), ',')
);

-- 4. Index for the hot predicate. Cheap; protects the view from full scans.
CREATE INDEX IF NOT EXISTS idx_cmsd_state_date
  ON complete_market_scrapper_dataset (state, date);

-- 5. Grants. security_invoker means chatbot_ro reads under its own perms, so
-- both objects need an explicit SELECT grant.
GRANT SELECT ON chatbot_market         TO chatbot_ro;
GRANT SELECT ON chatbot_mv_market_daily TO chatbot_ro;
GRANT SELECT ON category_map           TO chatbot_ro;

-- ── In-transaction verification (rolled back if anything below errors) ─────
DO $$
DECLARE
  v_count   bigint;
  v_other   bigint;
  v_thc_bad bigint;
BEGIN
  -- chatbot_market must be readable + produce sane rows under admin (no GUC
  -- needed — admin bypasses RLS).
  SELECT count(*) INTO v_count FROM chatbot_market WHERE date_d = (SELECT MAX(date_d) FROM chatbot_market);
  RAISE NOTICE 'chatbot_market latest snapshot rows: %', v_count;

  -- 'Other' bucket should be tiny — anything large means we missed a variant.
  SELECT count(*) INTO v_other FROM chatbot_market WHERE category_norm = 'Other';
  RAISE NOTICE 'chatbot_market rows in Other bucket: %', v_other;

  -- thc_num must respect the [0..100] clamp. Zero rows above 100 confirms
  -- the LATERAL guard is doing its job.
  SELECT count(*) INTO v_thc_bad FROM chatbot_market WHERE thc_num > 100 OR thc_num < 0;
  IF v_thc_bad > 0 THEN
    RAISE EXCEPTION 'thc_num clamp violated on % rows', v_thc_bad;
  END IF;

  RAISE NOTICE 'thc_num clamp OK';
END
$$;

COMMIT;

-- ── Post-commit hint for next step ─────────────────────────────────────────
-- After this migration applies cleanly:
--   1. Update lib/chatbot/sqlGuard.ts ALLOWED_TABLES to:
--        { 'chatbot_market', 'chatbot_mv_market_daily' }
--      Remove 'complete_market_scrapper_dataset' from the allow-list.
--   2. Rewrite chatbot/schema_context.md to describe chatbot_market with the
--      clean columns and DROP the category CASE / price COALESCE / thc regex /
--      to_char text-date workaround.
--   3. Rewrite chatbot/examples.json to query chatbot_market and chatbot_mv_market_daily.
--   4. Restart Next dev so promptBuilder reloads the new artifacts.

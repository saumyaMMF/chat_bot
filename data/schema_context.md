# Schema context — PostgreSQL 15, lowercase identifiers

> SCOPE: market/competitor data only. REFUSE for own-data ("my orders / inventory / sales / lots / customers"). "my competitors / the market" = SQL (rank brands by SUM(revenue)).

## Objects (allow-list)

### `complete_market_scrapper_dataset` — one row per (date, state, company, product, unit)

| col | type | notes |
|---|---|---|
| date | TEXT | `YYYY-MM-DD`; sorts chronologically |
| state | VARCHAR | RLS-scoped; do NOT filter manually |
| city, company, brand, brand_scrapped, product_name | TEXT | free-text |
| category | TEXT | 58 variants — always normalize via CASE below |
| unit | TEXT | `1g`, `3.5g`, `7g`, `28g`, `1pk` |
| price | TEXT | inconsistent (`$63.00` or `45`); use `price_n` |
| price_num | DOUBLE | numeric price (15% NULL — use COALESCE below) |
| thc | TEXT | noisy (`24%`, `100mg`, `THC -`, `''`); use `thc_num` cast below |
| quantity, previous_quantity | INT | units listed |
| change | DOUBLE | pre-baked units sold (pack-size normalized) |
| revenue | DOUBLE | `price_num × |change|` — inferred market sell-through, not POS |
| flag | TEXT | `'added'` / `'no change'` / `'removed'` / `NULL` (15%) |
| days_on_shelf | INT | 38% NULL — filter `IS NOT NULL` when sorting/aggregating |
| first_seen, created_at | TIMESTAMP | freshness signals |

### `chatbot_mv_market_daily` (view) — daily aggregates, pre-aggregated per (date, brand, company, category, state)

cols: `date (DATE), category, brand, company, revenue (NUMERIC), quantity, sku_count, state`.

**Use this view whenever the answer aggregates by brand, company, or category** — even for a single day. It is ~480× smaller per day than the base table. Examples that MUST hit this view:
- "top brands" / "top companies" / "top categories" (any window, including today)
- "revenue by brand", "market share", "category mix"
- multi-day trends (range ≤14 days)

Use the base table ONLY for SKU-level questions (price, THC, `flag`, `days_on_shelf`, product names).

## Canonical mapping (use, never raw `category =`)

```sql
CASE
  WHEN lower(category) LIKE '%flower%' OR lower(category) IN ('pre-packed flowers','pre-packed-flower') THEN 'Flower'
  WHEN lower(category) LIKE '%pre%roll%' OR lower(category) IN ('preroll','prerolls') THEN 'PreRoll'
  WHEN lower(category) LIKE '%vape%' OR lower(category) IN ('cartridge','carts','vapecarts','vape-carts','vape pens') THEN 'Vape'
  WHEN lower(category) LIKE '%concentrate%' THEN 'Concentrate'
  WHEN lower(category) LIKE '%edible%' THEN 'Edible'
  ELSE 'Other'
END AS category_norm
```

## Numeric casts

- **Price (use everywhere numeric)**: `COALESCE(price_num, NULLIF(regexp_replace(price,'[^0-9.]','','g'),'')::numeric) AS price_n`
- **THC**: `CASE WHEN thc ~ '^[0-9]+(\.[0-9]+)?%?$' THEN regexp_replace(thc,'[^0-9.]','','g')::numeric END AS thc_num`, then filter `thc_num BETWEEN 0 AND 100`

## Date helpers (base table `date` is TEXT)

- Latest snapshot: `WHERE date = (SELECT MAX(date) FROM complete_market_scrapper_dataset)`
- Last N days: `WHERE date >= to_char(CURRENT_DATE - INTERVAL 'N days', 'YYYY-MM-DD')`
- On `chatbot_mv_market_daily`, `date` is real DATE: `WHERE date >= CURRENT_DATE - INTERVAL '14 days'` works directly.

## Ranking rules

- Default metric = `SUM(revenue)`. "top/best/biggest/leading" with no metric → revenue.
- "top" with no number → `LIMIT 10` (even for singular "the top brand").
- Group by text dimension → exclude blanks: `WHERE brand IS NOT NULL AND brand <> ''`.
- Multi-column distinct: `COUNT(DISTINCT (product_name, brand))` — note parens.

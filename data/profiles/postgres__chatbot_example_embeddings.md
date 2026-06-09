# `chatbot_example_embeddings` (postgres)

- **Schema:** public
- **Rows:** 41
- **Columns:** 8
- **Primary key:** `id`
- **Indexes:** `chatbot_example_embeddings_pkey`(U: id), `idx_example_embedding_cosine`(N: embedding), `idx_example_prompt_hash`(N: prompt_hash)

## Columns

### `id` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 41 · **Distinct:** 41 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, LOW-CARDINALITY (categorical)
- **Range:** min=`ex-001` · max=`ex-041`
- **Length:** min=6 · max=6 · avg=6.0
- **All distinct values (41):** `ex-001`, `ex-002`, `ex-003`, `ex-004`, `ex-005`, `ex-006`, `ex-007`, `ex-008`, `ex-009`, `ex-010`, `ex-011`, `ex-012`, `ex-013`, `ex-014`, `ex-015`, `ex-016`, `ex-017`, `ex-018`, `ex-019`, `ex-020`, `ex-021`, `ex-022`, `ex-023`, `ex-024`, `ex-025`, `ex-026`, `ex-027`, `ex-028`, `ex-029`, `ex-030`, `ex-031`, `ex-032`, `ex-033`, `ex-034`, `ex-035`, `ex-036`, `ex-037`, `ex-038`, `ex-039`, `ex-040`, `ex-041`

### `question` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 41 · **Distinct:** 41 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, LOW-CARDINALITY (categorical)
- **Range:** min=`Average market price per category in the latest snapshot.` · max=`Who is the top brand in the market right now?`
- **Length:** min=16 · max=80 · avg=39.93
- **All distinct values (41):** `Average market price per category in the latest snapshot.`, `Average price by category.`, `Average THC by category in the latest market snapshot.`, `Best categories by revenue this week.`, `Delete all rows from the market table.`, `Fastest-moving SKUs in the market right now.`, `Find competitor Cartridge products priced under 25.`, `How did the market quantity for the Flower category trend over the last 14 days?`, `How many flower products were added to the market today?`, `How many products added in the last 7 days?`, `How many products added today?`, `How much quantity is in the market today?`, `List my wholesale orders that are still pending.`, `Lots expiring in the next 30 days.`, `Low stock items.`, `My partner stores.`, `Open balance total.`, `Open sales actions by priority.`, `Revenue trend across all categories over the last two weeks.`, `Show me market data for every state.`, `Show me my top competitors.`, `THC by strain in product lots.`, `Top 10 customers by revenue last 30 days.`, `Top 10 highest revenue products in the market today.`, `Top 5 competing stores by revenue.`, `Top 5 competitor brands by quantity in the latest market snapshot.`, `Top brands in the market.`, `Total competitor products per category on the latest day.`, `Total orders today.`, `Total quantity by product today.`, `Total revenue by category today.`, `What did I add to my catalog this week?`, `What has been sitting on shelves the longest?`, `What live inventory do I have for Berry Fizz?`, `What's the average price of an eighth right now?`, `Which brands have the most products listed right now?`, `Which products were removed from the market today?`, `Which products were removed today?`, `Who are my competitors?`, `Who is my competitor?`, `Who is the top brand in the market right now?`

### `sql` — text

- **Declared type:** `text`
- **Nullable:** True · **Null %:** 4.88%
- **Rows:** 41 · **Distinct:** 35 (89.74% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`SELECT AVG(price_n) AS avg_price FROM chatbot_market WHERE unit = '3.5g' AND …` · max=`WITH t AS (SELECT CASE WHEN lower(category) LIKE '%flower%' OR lower(category…`
- **Length:** min=70 · max=715 · avg=211.28
- **All distinct values (35):** `SELECT AVG(price_n) AS avg_price FROM chatbot_market WHERE unit = '3.5g' AND …`, `SELECT brand, SUM(quantity) AS total_qty FROM chatbot_mv_market_daily WHERE d…`, `SELECT brand, SUM(revenue) AS total_revenue FROM chatbot_mv_market_daily WHER…`, `SELECT brand, SUM(sku_count) AS product_count FROM chatbot_mv_market_daily WH…`, `SELECT CASE WHEN lower(category) LIKE '%flower%' OR lower(category) IN ('pre-…`, `SELECT Category, AVG(CAST(REGEXP_REPLACE(Price, '[^0-9.]', '') AS DECIMAL(10,…`, `SELECT category_norm, AVG(price_n) AS avg_price FROM chatbot_market WHERE dat…`, `SELECT category_norm, AVG(thc_num) AS avg_thc FROM chatbot_market WHERE date_…`, `SELECT Category, SUM(CAST(REGEXP_REPLACE(Revenue, '[^0-9.]', '') AS DECIMAL(1…`, `SELECT company, SUM(revenue) AS total_revenue FROM chatbot_mv_market_daily WH…`, `SELECT COUNT(*) AS added_count FROM chatbot_market WHERE category_norm = 'Flo…`, `SELECT COUNT(*) AS added_count FROM rhize_dataset_main WHERE Flag = 'Added' A…`, `SELECT COUNT(*) AS added_count FROM rhize_dataset_main WHERE Flag = 'Added' A…`, `SELECT COUNT(*) AS n FROM rhize_orders WHERE DATE(date) = CURRENT_DATE`, `SELECT customerName, category, priority, description, status FROM rhize_sales…`, `SELECT customerName, SUM(subtotal) AS rev FROM rhize_orders WHERE date >= DAT…`, `SELECT date, customerName, productName, qty, subtotal FROM rhize_orders WHERE…`, `SELECT date, SUM(quantity) AS total_qty FROM chatbot_mv_market_daily WHERE (l…`, `SELECT date, SUM(revenue) AS rev FROM chatbot_mv_market_daily WHERE date >= C…`, `SELECT name, city, tier FROM rhize_stores WHERE isPartner = 1 ORDER BY name L…`, `SELECT product_name, brand, company, category_norm FROM chatbot_market WHERE …`, `SELECT product_name, brand, company, days_on_shelf FROM chatbot_market WHERE …`, `SELECT product_name, brand, company, days_on_shelf FROM chatbot_market WHERE …`, `SELECT product_name, brand, company, price_n FROM chatbot_market WHERE catego…`, `SELECT product_name, brand, SUM(revenue) AS total_revenue FROM chatbot_market…`, `SELECT Product_Name, Company_Name, Category, date FROM rhize_dataset_main WHE…`, `SELECT Product_Name, Company_Name, Category, Flag, date FROM rhize_dataset_ma…`, `SELECT productName, current_qty FROM rhize_live_inventory WHERE current_qty <…`, `SELECT productName, lotNumber, current_qty, remaining, updatedAt FROM rhize_l…`, `SELECT Product_Name, SUM(CAST(REGEXP_REPLACE(`Today's_Quantity_Total`, '[^0-9…`, `SELECT strain, AVG(thc) AS avg_thc, COUNT(*) AS n_lots FROM rhize_product_lot…`, `SELECT strain, lotNumber, expirationDate FROM rhize_product_lots WHERE expira…`, `SELECT SUM(CAST(REGEXP_REPLACE(`Today's_Quantity_Total`, '[^0-9.]', '') AS DE…`, `SELECT SUM(openBalance) AS open_total FROM rhize_orders WHERE status <> 'Comp…`, `WITH t AS (SELECT CASE WHEN lower(category) LIKE '%flower%' OR lower(category…`

### `refusal` — text

- **Declared type:** `text`
- **Nullable:** True · **Null %:** 95.12%
- **Rows:** 41 · **Distinct:** 2 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, LOW-CARDINALITY (categorical)
- **Range:** min=`I can only access your licensed state(s). I can't query other states.` · max=`I'm read-only and can't delete or change any data. I can show you market data…`
- **Length:** min=69 · max=100 · avg=84.5
- **All distinct values (2):** `I can only access your licensed state(s). I can't query other states.`, `I'm read-only and can't delete or change any data. I can show you market data…`

### `expected_kind` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 41 · **Distinct:** 2 (4.88% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`refusal` · max=`result`
- **Length:** min=6 · max=7 · avg=6.05
- **All distinct values (2):** `refusal`, `result`

### `embedding` — unknown

- **Declared type:** `USER-DEFINED (vector)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 41 · **Distinct:** 41 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, LOW-CARDINALITY (categorical)
- **Length:** min=9442 · max=9536 · avg=9497.39

### `prompt_hash` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 41 · **Distinct:** 41 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, LOW-CARDINALITY (categorical)
- **Range:** min=`0698da1a91b7` · max=`f565b73e96be`
- **Length:** min=12 · max=12 · avg=12.0
- **All distinct values (41):** `0698da1a91b7`, `0cb88514aca3`, `160c0022b57a`, `17ce128a5c65`, `22514bf1d1fb`, `286ca0531e92`, `367e99bd5c99`, `369dda4369b0`, `41d971c34a1b`, `41dcdcfe63aa`, `47a487dfc9ee`, `486a5c4f0ff8`, `5494bc873443`, `55fb25dac606`, `5626c6ba4b46`, `56f587a8935b`, `59b069eda37e`, `5e41a9ea1071`, `709cdb9cbf89`, `7459e9eb3e1c`, `74999b018b07`, `8312827c4f67`, `95360c9c37dc`, `a03bee8c233f`, `a3f17d09224a`, `a8071c8370b3`, `ac7919e3308d`, `af525cbff315`, `b3264b975023`, `b3cb99ff7468`, `b8887ed055fe`, `b8d66b1bfa00`, `bd36b4a5c672`, `c443b4d078db`, `c893e6c5a531`, `cc510fe9fafa`, `dde405ebe556`, `e599b47a7fb2`, `eff83a880c2a`, `f4483e43a3e8`, `f565b73e96be`

### `created_at` — datetime

- **Declared type:** `timestamp with time zone (timestamptz)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 41 · **Distinct:** 41 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, LOW-CARDINALITY (categorical)
- **Range:** min=`2026-06-06 10:09:55.309074+00:00` · max=`2026-06-06 13:05:20.815833+00:00`
- **Length:** min=28 · max=29 · avg=28.88
- **Pattern hints:** datetime-string
- **All distinct values (41):** `2026-06-06 10:09:55.309074+00:00`, `2026-06-06 10:09:56.076513+00:00`, `2026-06-06 10:09:56.675353+00:00`, `2026-06-06 10:09:57.227624+00:00`, `2026-06-06 10:09:57.776478+00:00`, `2026-06-06 10:09:58.332990+00:00`, `2026-06-06 10:09:58.892711+00:00`, `2026-06-06 10:09:59.444957+00:00`, `2026-06-06 10:10:00.094553+00:00`, `2026-06-06 10:10:00.673216+00:00`, `2026-06-06 10:10:01.250260+00:00`, `2026-06-06 10:10:01.844576+00:00`, `2026-06-06 10:10:02.464078+00:00`, `2026-06-06 11:27:30.325644+00:00`, `2026-06-06 11:27:30.939676+00:00`, `2026-06-06 11:27:31.551633+00:00`, `2026-06-06 11:27:32.191476+00:00`, `2026-06-06 11:27:32.902189+00:00`, `2026-06-06 11:27:33.535334+00:00`, `2026-06-06 11:27:34.221330+00:00`, `2026-06-06 11:27:34.819722+00:00`, `2026-06-06 11:27:35.424742+00:00`, `2026-06-06 11:27:36.030509+00:00`, `2026-06-06 11:27:36.685763+00:00`, `2026-06-06 11:27:37.297362+00:00`, `2026-06-06 11:27:37.893335+00:00`, `2026-06-06 11:27:38.496990+00:00`, `2026-06-06 11:27:39.097873+00:00`, `2026-06-06 11:27:39.697985+00:00`, `2026-06-06 11:27:40.292430+00:00`, `2026-06-06 11:27:40.934685+00:00`, `2026-06-06 11:27:41.528387+00:00`, `2026-06-06 11:27:42.118559+00:00`, `2026-06-06 11:27:42.755543+00:00`, `2026-06-06 11:27:43.346118+00:00`, `2026-06-06 11:27:43.948514+00:00`, `2026-06-06 11:27:44.536564+00:00`, `2026-06-06 13:05:19.133802+00:00`, `2026-06-06 13:05:19.725527+00:00`, `2026-06-06 13:05:20.266329+00:00`, `2026-06-06 13:05:20.815833+00:00`

## Sample rows

| id | question | sql | refusal | expected_kind | embedding | prompt_hash | created_at |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ex-001 | Top brands in the market. | SELECT brand, SUM(revenue) AS total_revenue FROM chatbot_mv_market_daily WHER… | — | result | [-0.050061308,0.044473667,-0.21601546,0.022658296,0.023509426,0.034818072,-0.… | 5626c6ba4b46 | 2026-06-06 10:09:55.309074+00:00 |
| ex-002 | Who is my competitor? | SELECT brand, SUM(revenue) AS total_revenue FROM chatbot_mv_market_daily WHER… | — | result | [-0.048789665,0.0036360293,-0.17648575,0.017216627,0.016152224,0.034573056,-0… | 160c0022b57a | 2026-06-06 10:09:56.076513+00:00 |
| ex-003 | Who are my competitors? | SELECT brand, SUM(revenue) AS total_revenue FROM chatbot_mv_market_daily WHER… | — | result | [-0.039968546,-0.0041262195,-0.1833276,0.014002034,0.029410554,0.024837792,0.… | ac7919e3308d | 2026-06-06 10:09:56.675353+00:00 |
| ex-004 | Show me my top competitors. | SELECT brand, SUM(revenue) AS total_revenue FROM chatbot_mv_market_daily WHER… | — | result | [-0.04280328,-0.0073584504,-0.18487704,0.034383252,0.021284372,-0.01648737,0.… | 8312827c4f67 | 2026-06-06 10:09:57.227624+00:00 |
| ex-005 | Top 5 competing stores by revenue. | SELECT company, SUM(revenue) AS total_revenue FROM chatbot_mv_market_daily WH… | — | result | [-0.040602893,0.06396976,-0.21744719,0.018565642,-0.009217505,-0.031431586,0.… | b8d66b1bfa00 | 2026-06-06 10:09:57.776478+00:00 |

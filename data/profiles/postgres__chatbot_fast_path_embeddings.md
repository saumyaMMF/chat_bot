# `chatbot_fast_path_embeddings` (postgres)

- **Schema:** public
- **Rows:** 83
- **Columns:** 11
- **Primary key:** `id`
- **Indexes:** `chatbot_fast_path_embeddings_pkey`(U: id), `idx_fast_path_dialect`(N: dialect), `idx_fast_path_embedding_cosine`(N: embedding), `idx_fast_path_prompt_hash`(N: prompt_hash)

## Columns

### `id` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 83 · **Distinct:** 83 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE
- **Range:** min=`market_categories:001` · max=`tenant_catalog:021`
- **Length:** min=12 · max=29 · avg=17.86
- **All distinct values (83):** `market_categories:001`, `market_categories:002`, `market_categories:003`, `market_categories:004`, `market_categories:005`, `market_categories:006`, `market_companies_stores:001`, `market_companies_stores:002`, `market_companies_stores:003`, `market_companies_stores:004`, `market_competitors_brands:001`, `market_competitors_brands:002`, `market_competitors_brands:003`, `market_competitors_brands:004`, `market_competitors_brands:005`, `market_competitors_brands:006`, `market_skus:001`, `market_skus:002`, `market_skus:003`, `market_skus:004`, `market_skus:005`, `market_skus:006`, `market_skus:007`, `market_skus:008`, `market_skus:009`, `market_skus:010`, `market_totals:001`, `market_totals:002`, `market_totals:003`, `market_totals:004`, `market_totals:005`, `market_trends:001`, `market_trends:002`, `market_trends:003`, `market_trends:004`, `ops_inventory:001`, `ops_inventory:002`, `ops_inventory:003`, `ops_inventory:004`, `ops_lots:001`, `ops_lots:002`, `ops_lots:003`, `ops_lots:004`, `ops_orders:001`, `ops_orders:002`, `ops_orders:003`, `ops_orders:004`, `ops_orders:005`, `ops_orders:006`, `ops_orders:007`, `ops_orders:008`, `ops_sales_actions:001`, `ops_sales_actions:002`, `ops_sales_actions:003`, `ops_stores:001`, `ops_stores:002`, `ops_stores:003`, `refusals:001`, `refusals:002`, `refusals:003`, `refusals:004`, `refusals:005`, `tenant_catalog:001`, `tenant_catalog:002`, `tenant_catalog:003`, `tenant_catalog:004`, `tenant_catalog:005`, `tenant_catalog:006`, `tenant_catalog:007`, `tenant_catalog:008`, `tenant_catalog:009`, `tenant_catalog:010`, `tenant_catalog:011`, `tenant_catalog:012`, `tenant_catalog:013`, `tenant_catalog:014`, `tenant_catalog:015`, `tenant_catalog:016`, `tenant_catalog:017`, `tenant_catalog:018`, `tenant_catalog:019`, `tenant_catalog:020`, `tenant_catalog:021`

### `group_name` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 83 · **Distinct:** 13 (15.66% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`market_categories` · max=`tenant_catalog`
- **Length:** min=8 · max=25 · avg=13.86
- **All distinct values (13):** `market_categories`, `market_companies_stores`, `market_competitors_brands`, `market_skus`, `market_totals`, `market_trends`, `ops_inventory`, `ops_lots`, `ops_orders`, `ops_sales_actions`, `ops_stores`, `refusals`, `tenant_catalog`

### `question` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 83 · **Distinct:** 83 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE
- **Range:** min=`already expired lots` · max=`which stores carry brand {BRAND}`
- **Length:** min=15 · max=44 · avg=29.65
- **All distinct values (83):** `already expired lots`, `average market price per category today`, `average price by category`, `average price by category today`, `average price of 1g vape`, `average price of eighth`, `average price per category`, `average revenue by category`, `average thc by category today`, `average thc by strain in lots`, `best categories by revenue {WINDOW}`, `best selling products by quantity {WINDOW}`, `brands with most skus listed`, `{CATEGORY} quantity trend {WINDOW}`, `category revenue share today`, `cheapest eighth on shelf today`, `count of partner stores`, `customers with open balance over 1000`, `delete all rows from market table`, `discontinued products`, `drop the rhize orders table`, `fastest moving skus right now`, `highest thc {CATEGORY} products`, `highest thc strains in inventory`, `how is brand {BRAND} doing`, `how many distinct brands today`, `how many distinct stores today`, `how many products added in the last 7 days`, `how many products added today`, `how many products added to market today`, `how many products listed today`, `how many products removed today`, `how many units do I have listed today`, `how much quantity today`, `list pending wholesale orders`, `list products with no change today`, `live inventory for product {BRAND}`, `lots expiring next 30 days`, `low stock items`, `market share by brand today`, `my partner stores`, `new brands entering market last 30 days`, `open balance total`, `open sales actions by priority`, `orders by status this month`, `out of stock items`, `partner stores by city`, `products with no change today`, `quantity per product today`, `revenue for brand {BRAND} {WINDOW}`, `revenue from completed orders {WINDOW}`, `revenue trend {WINDOW}`, `sales actions completed last 30 days`, `sales actions due this week`, `show another tenants orders`, `show market data for every state`, `sku count per category today`, `stores with widest brand assortment`, `top brands in store {COMPANY}`, `top {N} brands by units {WINDOW}`, `top {N} brands {WINDOW}`, `top {N} {CATEGORY} brands {WINDOW}`, `top {N} customers by revenue {WINDOW}`, `top {N} highest revenue products today`, `top {N} stores {WINDOW}`, `total inventory on hand by product`, `total market revenue today`, `total market revenue {WINDOW}`, `total orders today`, `total quantity in the market today`, `total revenue by category today`, `unchanged products`, `update order status`, `weekly revenue by category last 4 weeks`, `what did I add to my catalog this week`, `what has been sitting on shelves longest`, `what products didn't change`, `what products were added today`, `what products were added to market today`, `what products were removed from market today`, `what products were removed today`, `what's new in my catalog`, `which stores carry brand {BRAND}`

### `sql` — text

- **Declared type:** `text`
- **Nullable:** True · **Null %:** 6.02%
- **Rows:** 83 · **Distinct:** 71 (91.03% of non-null)
- **Range:** min=`SELECT AVG(price_n) AS avg_price FROM chatbot_market WHERE category_norm = 'V…` · max=`SELECT SUM(subtotal) AS rev FROM rhize_orders WHERE {WINDOW_SQL_MYSQL} AND st…`
- **Length:** min=58 · max=307 · avg=172.38
- **All distinct values (71):** `SELECT AVG(price_n) AS avg_price FROM chatbot_market WHERE category_norm = 'V…`, `SELECT AVG(price_n) AS avg_price FROM chatbot_market WHERE unit = '3.5g' AND …`, `SELECT brand, MIN(date) AS first_seen FROM chatbot_mv_market_daily WHERE bran…`, `SELECT brand, SUM(quantity) AS total_qty FROM chatbot_mv_market_daily WHERE {…`, `SELECT brand, SUM(revenue) AS rev FROM chatbot_mv_market_daily WHERE category…`, `SELECT brand, SUM(revenue) AS rev FROM chatbot_mv_market_daily WHERE lower(co…`, `SELECT brand, SUM(revenue) AS rev, ROUND(100.0 * SUM(revenue) / NULLIF(SUM(SU…`, `SELECT brand, SUM(revenue) AS total_revenue FROM chatbot_mv_market_daily WHER…`, `SELECT brand, SUM(sku_count) AS skus FROM chatbot_mv_market_daily WHERE date …`, `SELECT Category, AVG(CAST(REGEXP_REPLACE(Price, '[^0-9.]', '') AS DECIMAL(10,…`, `SELECT Category, AVG(CAST(REGEXP_REPLACE(Revenue, '[^0-9.]', '') AS DECIMAL(1…`, `SELECT category_norm, AVG(price_n) AS avg_price FROM chatbot_market WHERE dat…`, `SELECT category_norm, AVG(thc_num) AS avg_thc FROM chatbot_market WHERE date_…`, `SELECT category_norm, SUM(revenue) AS rev FROM chatbot_mv_market_daily WHERE …`, `SELECT category_norm, SUM(revenue) AS rev, ROUND(100.0 * SUM(revenue) / NULLI…`, `SELECT category_norm, SUM(sku_count) AS skus FROM chatbot_mv_market_daily WHE…`, `SELECT Category, SUM(CAST(REGEXP_REPLACE(Revenue, '[^0-9.]', '') AS DECIMAL(1…`, `SELECT city, COUNT(*) AS n FROM rhize_stores WHERE isPartner = 1 GROUP BY cit…`, `SELECT company, COUNT(DISTINCT brand) AS brands FROM chatbot_mv_market_daily …`, `SELECT company, SUM(revenue) AS rev FROM chatbot_mv_market_daily WHERE lower(…`, `SELECT company, SUM(revenue) AS total_revenue FROM chatbot_mv_market_daily WH…`, `SELECT COUNT(*) AS added_count FROM chatbot_market WHERE flag = 'added' AND d…`, `SELECT COUNT(*) AS added_count FROM rhize_dataset_main WHERE Flag = 'Added' A…`, `SELECT COUNT(*) AS added_count FROM rhize_dataset_main WHERE Flag = 'Added' A…`, `SELECT COUNT(*) AS n FROM chatbot_market WHERE date_d = (SELECT MAX(date_d) F…`, `SELECT COUNT(*) AS n FROM rhize_orders WHERE DATE(date) = CURRENT_DATE`, `SELECT COUNT(*) AS n FROM rhize_sales_actions WHERE status = 'Done' AND updat…`, `SELECT COUNT(*) AS n FROM rhize_stores WHERE isPartner = 1`, `SELECT COUNT(*) AS no_change_count FROM rhize_dataset_main WHERE Flag = 'No C…`, `SELECT COUNT(*) AS removed_count FROM rhize_dataset_main WHERE Flag = 'Remove…`, `SELECT COUNT(DISTINCT brand) AS brands FROM chatbot_market WHERE date_d = (SE…`, `SELECT COUNT(DISTINCT company) AS stores FROM chatbot_market WHERE date_d = (…`, `SELECT customerName, category, priority, description, dueDate FROM rhize_sale…`, `SELECT customerName, category, priority, description, status FROM rhize_sales…`, `SELECT customerName, SUM(openBalance) AS open_total FROM rhize_orders WHERE s…`, `SELECT customerName, SUM(subtotal) AS rev FROM rhize_orders WHERE {WINDOW_SQL…`, `SELECT date, customerName, productName, qty, subtotal, status FROM rhize_orde…`, `SELECT date, SUM(quantity) AS qty FROM chatbot_mv_market_daily WHERE category…`, `SELECT date, SUM(revenue) AS rev FROM chatbot_mv_market_daily WHERE {WINDOW_S…`, `SELECT date, SUM(revenue) AS rev, SUM(quantity) AS qty FROM chatbot_mv_market…`, `SELECT date_trunc('week', date)::date AS wk, category_norm, SUM(revenue) AS r…`, `SELECT name, city, tier FROM rhize_stores WHERE isPartner = 1 ORDER BY name L…`, `SELECT product_name, brand, company, category_norm FROM chatbot_market WHERE …`, `SELECT product_name, brand, company, category_norm, price_n FROM chatbot_mark…`, `SELECT product_name, brand, company, days_on_shelf FROM chatbot_market WHERE …`, `SELECT product_name, brand, company, days_on_shelf FROM chatbot_market WHERE …`, `SELECT product_name, brand, company, price_n FROM chatbot_market WHERE unit =…`, `SELECT product_name, brand, company, thc_num, price_n FROM chatbot_market WHE…`, `SELECT product_name, brand, SUM(revenue) AS rev FROM chatbot_market WHERE dat…`, `SELECT Product_Name, Company_Name, Category, date FROM rhize_dataset_main WHE…`, `SELECT Product_Name, Company_Name, Category, date FROM rhize_dataset_main WHE…`, `SELECT Product_Name, Company_Name, Category, date FROM rhize_dataset_main WHE…`, `SELECT Product_Name, Company_Name, Category, date FROM rhize_dataset_main WHE…`, `SELECT Product_Name, Company_Name, Category, date FROM rhize_dataset_main WHE…`, `SELECT productName, lotNumber, current_qty FROM rhize_live_inventory WHERE cu…`, `SELECT productName, lotNumber, current_qty FROM rhize_live_inventory WHERE cu…`, `SELECT productName, lotNumber, current_qty, remaining, updatedAt FROM rhize_l…`, `SELECT Product_Name, SUM(CAST(REGEXP_REPLACE(`Today's_Quantity_Total`, '[^0-9…`, `SELECT productName, SUM(current_qty) AS qty FROM rhize_live_inventory GROUP B…`, `SELECT productName, SUM(qty) AS qty, SUM(subtotal) AS rev FROM rhize_orders W…`, `SELECT status, COUNT(*) AS n, SUM(subtotal) AS rev FROM rhize_orders WHERE da…`, `SELECT strain, AVG(thc) AS avg_thc, COUNT(*) AS n_lots FROM rhize_product_lot…`, `SELECT strain, lotNumber, expirationDate FROM rhize_product_lots WHERE expira…`, `SELECT strain, lotNumber, expirationDate FROM rhize_product_lots WHERE expira…`, `SELECT strain, lotNumber, thc FROM rhize_product_lots WHERE thc IS NOT NULL O…`, `SELECT SUM(CAST(REGEXP_REPLACE(`Today's_Quantity_Total`, '[^0-9.]', '') AS DE…`, `SELECT SUM(openBalance) AS open_total FROM rhize_orders WHERE status <> 'Comp…`, `SELECT SUM(revenue) AS rev FROM chatbot_mv_market_daily WHERE lower(brand) LI…`, `SELECT SUM(revenue) AS rev FROM chatbot_mv_market_daily WHERE {WINDOW_SQL}`, `SELECT SUM(revenue) AS total_sales_today FROM chatbot_mv_market_daily WHERE d…`, `SELECT SUM(subtotal) AS rev FROM rhize_orders WHERE {WINDOW_SQL_MYSQL} AND st…`

### `refusal` — text

- **Declared type:** `text`
- **Nullable:** True · **Null %:** 93.98%
- **Rows:** 83 · **Distinct:** 5 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, LOW-CARDINALITY (categorical)
- **Range:** min=`Cross-tenant access is blocked. Can only show your own data.` · max=`Read-only access. No DDL allowed.`
- **Length:** min=33 · max=72 · avg=58.0
- **All distinct values (5):** `Cross-tenant access is blocked. Can only show your own data.`, `Only licensed state(s) are accessible. Other states are blocked.`, `Read-only access. Can't delete or change data. Can run a SELECT instead.`, `Read-only access. Can't modify orders. Can list them instead.`, `Read-only access. No DDL allowed.`

### `dialect` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 83 · **Distinct:** 3 (3.61% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`any` · max=`postgres`
- **Length:** min=3 · max=8 · avg=6.14
- **All distinct values (3):** `any`, `mysql`, `postgres`

### `params` — json

- **Declared type:** `jsonb`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 83 · **Distinct:** 10 (12.05% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Length:** min=2 · max=27 · avg=4.37

### `embedding` — unknown

- **Declared type:** `USER-DEFINED (vector)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 83 · **Distinct:** 83 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE
- **Length:** min=9451 · max=9544 · avg=9498.66

### `prompt_hash` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 83 · **Distinct:** 83 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE
- **Range:** min=`01496b8f1269` · max=`fd72ca5a5c1a`
- **Length:** min=12 · max=12 · avg=12.0
- **All distinct values (83):** `01496b8f1269`, `0347d27b94f6`, `064a8ebadfa8`, `0953ec9becc0`, `09f03940b769`, `0ee0d725ef8c`, `12d2eb0802e1`, `131c2e25ad11`, `1536e77074a0`, `19d09ab84f56`, `19f455a7f441`, `1a60bb2e6786`, `20c854ec638b`, `2710c9977a06`, `2df8ad529526`, `2e199c19d925`, `310430e7e4b6`, `32eda9b07a6c`, `353f313229a6`, `36dd1c507e07`, `3914abe9b0a0`, `3bb480f7ade0`, `3e0eee377d72`, `40c16a739286`, `441d51bf017e`, `467f1d813942`, `511bfc8d8249`, `5448a73b15a8`, `581315ecb1c4`, `58bfedfcce9f`, `5c00b3f6cc6e`, `6142c11ffec1`, `6189dc370dca`, `64a3c670b02a`, `67bab9d9a257`, `68ef640a128d`, `6a1897225268`, `6a63c32d5a2e`, `6e1fb584c508`, `6fe6c8025b9c`, `7053af2b8585`, `765f70f1bf84`, `76ea587e4bc7`, `7a902f315164`, `80b76768aa35`, `84ac1a5faada`, `8557aeb339d4`, `8de00a753567`, `8ec57172a4c0`, `923e2a8021c6`, `944eb166fc5e`, `94505b825967`, `951e64090a8a`, `9a7fd71cde3d`, `a9986484305f`, `abd3cda8e62e`, `b2cec291ac95`, `b573412d9790`, `b701a79e090b`, `b77206c5b4d7`, `c49190f268a2`, `c659f158bbbd`, `c9fbe948059c`, `ccf57416e265`, `ce8d0cce1503`, `cf67c916d8a0`, `d2e47d5bbcc6`, `d30e297e65a3`, `d3cb07b2dd1b`, `d573cd900d2c`, `d717fa9f43ff`, `d7322e1eae11`, `d94e548ea70f`, `e00ee8327080`, `e3aa8834caea`, `e442ea53ad0f`, `e6a5e9c0c3bb`, `ea38a389dc6b`, `ed65b3ded1a1`, `ed75f1d26a46`, `f3d45c7b36d6`, `fcac509476d7`, `fd72ca5a5c1a`

### `created_at` — datetime

- **Declared type:** `timestamp with time zone (timestamptz)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 83 · **Distinct:** 83 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE
- **Range:** min=`2026-06-06 09:23:36.147331+00:00` · max=`2026-06-06 13:04:26.039607+00:00`
- **Length:** min=27 · max=29 · avg=28.89
- **Pattern hints:** datetime-string
- **All distinct values (83):** `2026-06-06 09:23:36.147331+00:00`, `2026-06-06 09:23:36.903001+00:00`, `2026-06-06 09:23:37.652356+00:00`, `2026-06-06 09:23:38.382800+00:00`, `2026-06-06 09:23:39.125825+00:00`, `2026-06-06 09:23:39.872121+00:00`, `2026-06-06 09:23:40.605862+00:00`, `2026-06-06 09:23:41.342371+00:00`, `2026-06-06 09:23:42.090373+00:00`, `2026-06-06 09:23:42.838956+00:00`, `2026-06-06 09:23:43.580926+00:00`, `2026-06-06 09:23:44.315557+00:00`, `2026-06-06 09:23:45.038729+00:00`, `2026-06-06 09:23:45.767558+00:00`, `2026-06-06 09:23:46.506068+00:00`, `2026-06-06 09:23:47.243497+00:00`, `2026-06-06 09:23:47.975764+00:00`, `2026-06-06 09:23:48.704274+00:00`, `2026-06-06 09:23:49.441183+00:00`, `2026-06-06 09:23:50.192074+00:00`, `2026-06-06 09:23:53.148366+00:00`, `2026-06-06 09:23:53.879379+00:00`, `2026-06-06 09:23:54.671204+00:00`, `2026-06-06 09:23:55.417277+00:00`, `2026-06-06 09:23:56.167782+00:00`, `2026-06-06 09:23:56.949286+00:00`, `2026-06-06 09:23:57.674868+00:00`, `2026-06-06 09:23:58.420640+00:00`, `2026-06-06 09:23:59.210997+00:00`, `2026-06-06 09:23:59.947996+00:00`, `2026-06-06 09:24:00.687499+00:00`, `2026-06-06 09:24:01.588305+00:00`, `2026-06-06 09:24:02.336970+00:00`, `2026-06-06 09:24:03.115648+00:00`, `2026-06-06 09:24:03.893655+00:00`, `2026-06-06 09:24:04.647908+00:00`, `2026-06-06 09:24:05.379933+00:00`, `2026-06-06 09:24:06.127344+00:00`, `2026-06-06 09:24:06.858703+00:00`, `2026-06-06 09:24:07.611748+00:00`, `2026-06-06 09:24:08.420112+00:00`, `2026-06-06 09:24:09.156653+00:00`, `2026-06-06 09:24:09.919396+00:00`, `2026-06-06 09:24:10.688488+00:00`, `2026-06-06 09:24:11.444757+00:00`, `2026-06-06 09:24:12.240110+00:00`, `2026-06-06 09:24:13.018705+00:00`, `2026-06-06 09:24:13.751229+00:00`, `2026-06-06 09:24:14.504179+00:00`, `2026-06-06 09:24:15.235390+00:00`, `2026-06-06 09:24:15.973860+00:00`, `2026-06-06 09:24:16.718688+00:00`, `2026-06-06 09:24:17.530403+00:00`, `2026-06-06 09:24:18.255444+00:00`, `2026-06-06 09:24:19.006046+00:00`, `2026-06-06 09:24:19.754406+00:00`, `2026-06-06 09:24:20.494894+00:00`, `2026-06-06 09:24:21.228973+00:00`, `2026-06-06 09:24:21.965882+00:00`, `2026-06-06 10:12:47.908972+00:00`, `2026-06-06 10:12:48.509936+00:00`, `2026-06-06 10:12:49.083532+00:00`, `2026-06-06 10:12:52.765096+00:00`, `2026-06-06 10:12:53.331818+00:00`, `2026-06-06 10:12:53.893623+00:00`, `2026-06-06 10:12:54.510086+00:00`, `2026-06-06 10:12:55.082606+00:00`, `2026-06-06 10:12:55.648157+00:00`, `2026-06-06 10:12:56.215761+00:00`, `2026-06-06 10:12:56.777610+00:00`, `2026-06-06 10:42:04.616417+00:00`, `2026-06-06 10:42:05.374118+00:00`, `2026-06-06 10:42:05.946495+00:00`, `2026-06-06 10:42:06.523589+00:00`, `2026-06-06 13:04:21.715042+00:00`, `2026-06-06 13:04:22.287487+00:00`, `2026-06-06 13:04:22.844207+00:00`, `2026-06-06 13:04:23.386462+00:00`, `2026-06-06 13:04:23.919046+00:00`, `2026-06-06 13:04:24.449050+00:00`, `2026-06-06 13:04:24.977079+00:00`, `2026-06-06 13:04:25.506586+00:00`, `2026-06-06 13:04:26.039607+00:00`

### `updated_at` — datetime

- **Declared type:** `timestamp with time zone (timestamptz)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 83 · **Distinct:** 83 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE
- **Range:** min=`2026-06-06 09:23:36.147331+00:00` · max=`2026-06-06 11:27:13.108908+00:00`
- **Length:** min=27 · max=29 · avg=28.89
- **Pattern hints:** datetime-string
- **All distinct values (83):** `2026-06-06 09:23:36.147331+00:00`, `2026-06-06 09:23:36.903001+00:00`, `2026-06-06 09:23:37.652356+00:00`, `2026-06-06 09:23:38.382800+00:00`, `2026-06-06 09:23:39.125825+00:00`, `2026-06-06 09:23:39.872121+00:00`, `2026-06-06 09:23:40.605862+00:00`, `2026-06-06 09:23:41.342371+00:00`, `2026-06-06 09:23:42.090373+00:00`, `2026-06-06 09:23:42.838956+00:00`, `2026-06-06 09:23:43.580926+00:00`, `2026-06-06 09:23:44.315557+00:00`, `2026-06-06 09:23:45.038729+00:00`, `2026-06-06 09:23:45.767558+00:00`, `2026-06-06 09:23:46.506068+00:00`, `2026-06-06 09:23:47.243497+00:00`, `2026-06-06 09:23:47.975764+00:00`, `2026-06-06 09:23:48.704274+00:00`, `2026-06-06 09:23:49.441183+00:00`, `2026-06-06 09:23:50.192074+00:00`, `2026-06-06 09:23:50.909702+00:00`, `2026-06-06 09:23:51.654391+00:00`, `2026-06-06 09:23:52.418121+00:00`, `2026-06-06 09:23:53.148366+00:00`, `2026-06-06 09:23:53.879379+00:00`, `2026-06-06 09:23:54.671204+00:00`, `2026-06-06 09:23:55.417277+00:00`, `2026-06-06 09:23:56.167782+00:00`, `2026-06-06 09:23:56.949286+00:00`, `2026-06-06 09:23:57.674868+00:00`, `2026-06-06 09:23:58.420640+00:00`, `2026-06-06 09:23:59.210997+00:00`, `2026-06-06 09:23:59.947996+00:00`, `2026-06-06 09:24:00.687499+00:00`, `2026-06-06 09:24:01.588305+00:00`, `2026-06-06 09:24:02.336970+00:00`, `2026-06-06 09:24:03.115648+00:00`, `2026-06-06 09:24:03.893655+00:00`, `2026-06-06 09:24:04.647908+00:00`, `2026-06-06 09:24:05.379933+00:00`, `2026-06-06 09:24:06.127344+00:00`, `2026-06-06 09:24:06.858703+00:00`, `2026-06-06 09:24:07.611748+00:00`, `2026-06-06 09:24:08.420112+00:00`, `2026-06-06 09:24:09.156653+00:00`, `2026-06-06 09:24:09.919396+00:00`, `2026-06-06 09:24:10.688488+00:00`, `2026-06-06 09:24:11.444757+00:00`, `2026-06-06 09:24:12.240110+00:00`, `2026-06-06 09:24:13.018705+00:00`, `2026-06-06 09:24:13.751229+00:00`, `2026-06-06 09:24:14.504179+00:00`, `2026-06-06 09:24:15.235390+00:00`, `2026-06-06 09:24:15.973860+00:00`, `2026-06-06 09:24:16.718688+00:00`, `2026-06-06 09:24:17.530403+00:00`, `2026-06-06 09:24:18.255444+00:00`, `2026-06-06 09:24:19.006046+00:00`, `2026-06-06 09:24:19.754406+00:00`, `2026-06-06 09:24:20.494894+00:00`, `2026-06-06 09:24:21.228973+00:00`, `2026-06-06 09:24:21.965882+00:00`, `2026-06-06 10:12:52.765096+00:00`, `2026-06-06 10:12:53.331818+00:00`, `2026-06-06 10:12:53.893623+00:00`, `2026-06-06 10:12:54.510086+00:00`, `2026-06-06 10:12:55.082606+00:00`, `2026-06-06 10:12:55.648157+00:00`, `2026-06-06 10:12:56.215761+00:00`, `2026-06-06 10:12:56.777610+00:00`, `2026-06-06 10:42:04.616417+00:00`, `2026-06-06 10:42:05.374118+00:00`, `2026-06-06 10:42:05.946495+00:00`, `2026-06-06 10:42:06.523589+00:00`, `2026-06-06 11:07:00.143622+00:00`, `2026-06-06 11:07:00.974723+00:00`, `2026-06-06 11:07:01.532502+00:00`, `2026-06-06 11:07:02.148053+00:00`, `2026-06-06 11:27:10.408501+00:00`, `2026-06-06 11:27:11.473939+00:00`, `2026-06-06 11:27:12.012870+00:00`, `2026-06-06 11:27:12.559576+00:00`, `2026-06-06 11:27:13.108908+00:00`

## Sample rows

| id | group_name | question | sql | refusal | dialect | params | embedding | prompt_hash | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| market_competitors_brands:001 | market_competitors_brands | top {N} brands {WINDOW} | SELECT brand, SUM(revenue) AS total_revenue FROM chatbot_mv_market_daily WHER… | — | postgres | ["N", "WINDOW"] | [-0.09271356,0.021152467,-0.21568759,0.0037639851,-0.012967693,-0.03070794,0.… | d94e548ea70f | 2026-06-06 09:23:36.147331+00:00 | 2026-06-06 09:23:36.147331+00:00 |
| market_competitors_brands:002 | market_competitors_brands | top {N} brands by units {WINDOW} | SELECT brand, SUM(quantity) AS total_qty FROM chatbot_mv_market_daily WHERE {… | — | postgres | ["N", "WINDOW"] | [-0.07554042,0.047906034,-0.21909371,-0.00266822,0.009231897,-0.043423627,0.0… | c49190f268a2 | 2026-06-06 09:23:36.903001+00:00 | 2026-06-06 09:23:36.903001+00:00 |
| market_competitors_brands:003 | market_competitors_brands | brands with most skus listed | SELECT brand, SUM(sku_count) AS skus FROM chatbot_mv_market_daily WHERE date … | — | postgres | [] | [-0.07053357,0.067929216,-0.20218629,0.032352973,-0.0133621,-0.027006656,-0.0… | b701a79e090b | 2026-06-06 09:23:37.652356+00:00 | 2026-06-06 09:23:37.652356+00:00 |
| market_competitors_brands:004 | market_competitors_brands | market share by brand today | SELECT brand, SUM(revenue) AS rev, ROUND(100.0 * SUM(revenue) / NULLIF(SUM(SU… | — | postgres | [] | [-0.037053417,0.041344486,-0.19834968,-0.015046676,0.051583596,0.0163315,-0.0… | 0347d27b94f6 | 2026-06-06 09:23:38.382800+00:00 | 2026-06-06 09:23:38.382800+00:00 |
| market_competitors_brands:005 | market_competitors_brands | how is brand {BRAND} doing | SELECT date, SUM(revenue) AS rev, SUM(quantity) AS qty FROM chatbot_mv_market… | — | postgres | ["BRAND"] | [-0.06345693,0.0040837433,-0.17773974,-0.004340101,0.04639285,0.01668355,-0.0… | ccf57416e265 | 2026-06-06 09:23:39.125825+00:00 | 2026-06-06 09:23:39.125825+00:00 |

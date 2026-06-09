# LLM-Optimized Schema Specification
## Rhize SaaS Platform — Multi-Tenant Cannabis Analytics

> **Dialect**: PostgreSQL (market tables) + MySQL (tenant ops tables)
> **Version**: 2.0 — validated against live database screenshots
> **Access**: Read-only. All writes are forbidden.
> **Tenancy**: All `rhize_*` MySQL tables are auto-scoped by `tenantid` (INT) via middleware injection. Never write `tenantid` in a query. Never filter `state` manually — RLS handles it on PostgreSQL market tables.
> **Purpose**: Natural language → accurate read-only SQL for market intelligence and own-business analytics.

---

## 1. SCHEMA OVERVIEW

### Two Data Universes — Never Mix Them

| Universe | Tables | Dialect | What it Represents |
|---|---|---|---|
| **Market / Competitor** | `complete_market_scrapper_dataset`, `chatbot_mv_market_daily` | PostgreSQL | Scraped competitor market data, NOT own business |
| **Tenant / Own Business** | All `rhize_*` tables + `Rhize_sales_data` | MySQL | The user's own orders, inventory, products, brands, stores, CRM |
| **Infrastructure / RAG** | `chatbot_example_embeddings`, `chatbot_schema_embeddings` | Postgres | Internal chatbot/system tables — NEVER query for business answers |

> ⚠️ **CRITICAL**: `complete_market_scrapper_dataset.revenue` = inferred market sell-through (competitor). `rhize_dataset_main.Revenue` = the tenant's OWN revenue. These are completely different metrics. Never aggregate them together.

> ⚠️ **`tenantid` is INT** across all MySQL tables — not VARCHAR. Auto-injected by middleware; never write it in queries.

> ⚠️ **View name**: The market daily view is queried as `chatbot_mv_market_daily` in production. This is a security_barrier wrapper over the raw `mv_market_daily` materialized view — the bot's RO role has SELECT on the wrapper only, NOT the raw view. Never query `mv_market_daily` directly.

---

## 2. TABLE DEFINITIONS

---

### TABLE: `complete_market_scrapper_dataset`

| Attribute | Value |
|---|---|
| **Kind** | Base fact table (PostgreSQL) |
| **Purpose** | Raw scraped competitor/market listings |
| **Data Grain** | One row per (date, state, company, product, unit) per scrape run |
| **Scrape Frequency** | ~4 times per day — same SKU appears multiple times daily |
| **Deduplication Rule** | Use `WHERE date = (SELECT MAX(date) FROM complete_market_scrapper_dataset)` for latest snapshot. For daily aggregates, prefer `chatbot_mv_market_daily` |
| **RLS** | State is auto-filtered. Never add `WHERE state = ...` |
| **Use When** | SKU-level detail needed: `product_name`, `price`, `thc`, `flag`, `days_on_shelf` |
| **Avoid When** | Aggregating by brand/company/category — use `chatbot_mv_market_daily` (~480x smaller) |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `date` | TEXT | No | ISO `YYYY-MM-DD` string | ⚠️ Text, not DATE. Use `to_char()` for date arithmetic. Latest: `WHERE date = (SELECT MAX(date) FROM complete_market_scrapper_dataset)`. Last N days: `WHERE date >= to_char(CURRENT_DATE - INTERVAL 'N days', 'YYYY-MM-DD')` |
| `state` | VARCHAR | No | US state code (VT, MA, etc.) | ⚠️ RLS-scoped. Never filter manually |
| `brand` | TEXT | Yes | Brand name (free-text) | Always filter: `brand IS NOT NULL AND brand <> ''` when grouping |
| `company` | TEXT | Yes | Retailer/dispensary name | Always filter: `company IS NOT NULL AND company <> ''` when grouping |
| `category` | TEXT | Yes | Raw product category — 58 variants | ⚠️ ALWAYS normalize. Preferred: `JOIN category_map ON lower(category) = raw_lower`. Fallback: inline CASE block (see §4). NEVER write `category = 'Flower'` |
| `product_name` | TEXT | Yes | SKU display name | Filter blanks when ranking. Only available in base table (not in view) |
| `unit` | TEXT | Yes | Pack size: `1g`, `3.5g`, `7g`, `28g`, `1pk` | Use for weight/size filtering |
| `price` | TEXT | Yes | Raw displayed price (`$63.00` or `45`) | ⚠️ Inconsistent format. Never use directly for math |
| `price_num` | DOUBLE PRECISION | Yes (~15% NULL) | Cleaned numeric price | Always use: `COALESCE(price_num, NULLIF(regexp_replace(price,'[^0-9.]','','g'),'')::numeric)`. Filter `> 0` before averaging |
| `thc` | TEXT | Yes | THC content — noisy (`24%`, `100mg`, `THC -`, `''`) | ⚠️ Must cast: `CASE WHEN thc ~ '^[0-9]+(\.[0-9]+)?%?$' THEN regexp_replace(thc,'[^0-9.]','','g')::numeric END AS thc_num` then filter `thc_num BETWEEN 0 AND 100` |
| `quantity` | INTEGER | Yes | Units listed on scrape day | Used in sell-through calculations |
| `previous_quantity` | INTEGER | Yes | Quantity from previous scrape | Used to derive sell-through delta |
| `change` | DOUBLE PRECISION | Yes | Pre-baked units sold (pack-size normalized) | Use for sell-through. Represents `quantity - previous_quantity` |
| `revenue` | DOUBLE PRECISION | Yes | `price_num × |change|` — inferred market sell-through | ⚠️ NOT POS revenue. Competitor/market metric. Default ranking metric for top/best/biggest market queries |
| `flag` | TEXT | Yes (~15% NULL) | `added` / `no change` / `removed` | Use `flag = 'added'` for new products, `flag = 'removed'` for dropped |
| `days_on_shelf` | INTEGER | Yes (~38% NULL) | Days since first seen | Always `WHERE days_on_shelf IS NOT NULL` when sorting/aggregating. ASC = fastest moving; DESC = stale |
| `first_seen` | TIMESTAMP | Yes | First scrape timestamp for the SKU | Use for new product analysis |
| `created_at` | TIMESTAMP | No | Row ingestion timestamp | Not the business date — use `date` for business logic |

---

### TABLE: `chatbot_mv_market_daily`

| Attribute | Value |
|---|---|
| **Kind** | Security-barrier view over materialized view (PostgreSQL) |
| **Wraps** | Raw materialized view `mv_market_daily` (RO role has no access to the raw view) |
| **Purpose** | Pre-aggregated market data — compressed daily snapshot |
| **Data Grain** | One row per (date, brand, company, category, state) per day |
| **Relative Size** | ~480x smaller than base table per day |
| **RLS** | State is auto-filtered. Never add `WHERE state = ...` |
| **Use When** | Top brands, top companies, category mix, market share, multi-day trends, any GROUP BY brand/company/category |
| **Avoid When** | SKU-level detail needed (`product_name`, individual `thc`, `flag`, `days_on_shelf`) |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `date` | DATE | No | Real DATE type — arithmetic works directly | `WHERE date >= CURRENT_DATE - INTERVAL '14 days'` |
| `brand` | TEXT | Yes | Brand grouping key | Filter: `brand IS NOT NULL AND brand <> ''` |
| `company` | TEXT | Yes | Retailer grouping key | Filter: `company IS NOT NULL AND company <> ''` |
| `category` | TEXT | Yes | Same 58 raw variants as base table | ⚠️ ALWAYS normalize via `category_map` join or CASE block |
| `revenue` | NUMERIC | Yes | Daily sum of base revenue per grouping | Default ranking metric for market aggregates |
| `quantity` | NUMERIC | Yes | Daily sum of base quantity | |
| `sku_count` | SMALLINT | Yes | Distinct SKUs per grouping | Use `SUM(sku_count)` when grouping by brand for "most products listed" |
| `state` | TEXT | No | US state code | RLS-scoped. Never filter manually |

---

### TABLE: `category_map`

| Attribute | Value |
|---|---|
| **Kind** | Lookup table (PostgreSQL) |
| **Purpose** | Maps raw category strings to normalized category labels |
| **Data Grain** | One row per raw category variant |
| **Use When** | Normalizing `category` in market tables — preferred over inline CASE block |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `raw_lower` | TEXT | No | Lowercased raw category string | Join: `lower(category) = raw_lower` |
| `category_norm` | TEXT | No | Normalized label: `Flower`, `PreRoll`, `Vape`, `Concentrate`, `Edible`, `Other` | Use this as the display/group-by value |

**Preferred join pattern:**
```sql
JOIN category_map cm ON lower(t.category) = cm.raw_lower
```
Use `LEFT JOIN` + `COALESCE(cm.category_norm, 'Other')` if unmatched rows are possible.

---

### TABLE: `rhize_orders`

| Attribute | Value |
|---|---|
| **Kind** | MySQL tenant operational table |
| **Purpose** | User's own product order history |
| **Data Grain** | One row per order line item |
| **Tenancy** | `tenantid` (INT) auto-injected by middleware |
| **Use When** | Own orders, customer revenue, sales by product, open balances, AR |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `id` | VARCHAR(36) | No | Order line primary key (cuid) | |
| `date` | DATETIME | No | Order date | Direct MySQL date arithmetic: `WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)` |
| `orderNumber` | INT | Yes | Sequential order number | Use for grouping all lines of one order |
| `storeId` | VARCHAR(36) | Yes | Store reference ID | Join to `rhize_stores.id` if needed |
| `customerName` | VARCHAR(255) | Yes | Retail store name on the order | Use `lower(customerName) LIKE lower('%X%')` for partial match. Group by for top customers |
| `productName` | VARCHAR(500) | Yes | Product ordered | |
| `productType` | VARCHAR(255) | Yes | Product category type (Cart, Preroll, etc.) | |
| `qty` | DOUBLE | Yes | Units sold on this line | |
| `variant` | VARCHAR(100) | Yes | Pack size variant (e.g. `0.5g`, `1g`) | |
| `lotNumber` | VARCHAR(100) | Yes | Lot reference | Can join to `rhize_product_lots.lotNumber` |
| `unitPrice` | DOUBLE | Yes | Per-unit price | |
| `subtotal` | DOUBLE | Yes | Line revenue (`qty × unitPrice`) | `SUM(subtotal)` for total revenue. Combine `WHERE status = 'Completed'` for realized revenue |
| `status` | VARCHAR(50) | No | `'Completed'` / `'Pending'` / `'Cancelled'` | Always filter status for revenue vs. open orders |
| `deliveryDate` | DATETIME | Yes | Delivery date | Filter for delivery timeline queries |
| `paymentType` | VARCHAR(100) | Yes | Payment method | |
| `openBalance` | DOUBLE | Yes | Unpaid balance per line | `SUM(openBalance)` for total AR. Filter `status <> 'Completed'` for outstanding |
| `updatedAt` | TIMESTAMP | Yes | Last update timestamp | |
| `uid` | VARCHAR(100) | Yes | Short unique display ID (e.g. `C6OEGT`) | |
| `createdAt` | DATETIME | Yes | Record creation timestamp | |
| `tenantid` | INT | No | Tenant identifier | ⚠️ Auto-injected. Never write in query |
| `brand_id` | VARCHAR(36) | Yes | Brand reference | ⚠️ Do NOT scope by `brand_id` — collides cross-tenant |

---

### TABLE: `rhize_live_inventory`

| Attribute | Value |
|---|---|
| **Kind** | MySQL tenant operational table |
| **Purpose** | Current on-hand inventory snapshot |
| **Data Grain** | One row per (productName, tenant) |
| **Tenancy** | `tenantid` (INT) auto-injected |
| **Snapshot** | Latest only — no historical inventory data |
| **Use When** | Low stock queries, what's in stock, on-hand units by product |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `id` | VARCHAR(36) | No | Inventory row primary key | |
| `productName` | VARCHAR(500) | No | Product name | Unique per (productName, tenant) |
| `strain` | VARCHAR(255) | Yes | Strain name | |
| `productType` | VARCHAR(255) | Yes | Product type (Trim, Flower Bulk, Waste, etc.) | |
| `lotNumber` | VARCHAR(100) | Yes | Lot number reference | Join to `rhize_product_lots.lotNumber` |
| `current_qty` | DOUBLE | Yes | On-hand units | Low stock: `WHERE current_qty < N`. Order `ASC` for lowest first |
| `pending` | DOUBLE | Yes | Reserved/pending units | |
| `remaining` | DOUBLE | Yes | Available-to-sell (`current_qty - pending`) | ⚠️ Always use `remaining` not `current_qty` for sellable stock |
| `lbs` | DOUBLE | Yes | Weight in pounds | Often NULL — check before using |
| `updatedAt` | DATETIME | No | Last snapshot update | |
| `tenantid` | INT | No | Tenant identifier | Auto-injected |
| `brand_id` | VARCHAR(36) | Yes | Brand reference | |

---

### TABLE: `rhize_product_lots`

| Attribute | Value |
|---|---|
| **Kind** | MySQL tenant operational table |
| **Purpose** | Lot tracking and lab result metadata |
| **Data Grain** | One row per (lotNumber, tenant) |
| **Tenancy** | `tenantid` (INT) auto-injected |
| **Use When** | THC by strain, expiring lots, lot metadata, lab results |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `id` | VARCHAR(36) | No | Lot primary key | |
| `strain` | VARCHAR(255) | No | Strain name | Join to `rhize_strain_info.strain`. Group by for `AVG(thc)` |
| `lotNumber` | VARCHAR(255) | No | Lot identifier | Join key to `rhize_live_inventory.lotNumber` |
| `productType` | VARCHAR(255) | Yes | Product type | |
| `internalLotId` | VARCHAR(100) | Yes | Internal lot reference | |
| `ccbLotNumber` | VARCHAR(100) | Yes | Regulatory lot number | |
| `thc` | DOUBLE | Yes | THC percentage — already numeric | ⚠️ Different from market `thc` (TEXT). Always `WHERE thc IS NOT NULL` when averaging. No cast needed |
| `tac` | DOUBLE | Yes | Total active cannabinoids | |
| `terps` | DOUBLE | Yes | Terpene percentage | |
| `expirationDate` | DATETIME | Yes | Lot expiry date | Expiring soon: `WHERE expirationDate BETWEEN CURRENT_DATE AND DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY)` |
| `createdAt` | DATETIME | Yes | Record creation timestamp | |
| `updatedAt` | DATETIME | Yes | Last update timestamp | |
| `tenantid` | INT | No | Tenant identifier | Auto-injected |
| `brand_id` | VARCHAR(36) | Yes | Brand reference | |

---

### TABLE: `rhize_brands`

| Attribute | Value |
|---|---|
| **Kind** | MySQL tenant operational table |
| **Purpose** | Brand registry — own brand + competitor catalog |
| **Data Grain** | One row per (tenantid, name) — unique |
| **Tenancy** | `tenantid` (INT) auto-injected |
| **Use When** | Identifying own brand, listing brand catalog |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `id` | VARCHAR(36) | No | Brand primary key (cuid) | |
| `name` | VARCHAR(255) | No | Brand name | Unique per (tenantid, name) |
| `isRhize` | TINYINT(1) | No | `1` = user's OWN brand, `0` = competitor brand in catalog | For "my brand" / "own brand" queries: `WHERE isRhize = 1` |
| `createdAt` | DATETIME | No | Brand creation timestamp | |
| `tenantid` | INT | No | Tenant identifier | Auto-injected |

---

### TABLE: `rhize_stores`

| Attribute | Value |
|---|---|
| **Kind** | MySQL tenant operational table |
| **Purpose** | Retail store / account registry |
| **Data Grain** | One row per store per tenant |
| **Tenancy** | `tenantid` (INT) auto-injected |
| **Use When** | Partner stores, retail accounts, store directory |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `id` | VARCHAR(36) | No | Store primary key | |
| `slug` | VARCHAR(255) | Yes | URL slug | |
| `name` | VARCHAR(255) | No | Store name | |
| `licenseNumber` | VARCHAR(255) | Yes | Regulatory license | Often NULL in data |
| `address` | VARCHAR(500) | Yes | Street address | Often NULL in data |
| `city` | VARCHAR(255) | Yes | Store city | |
| `phone` | VARCHAR(100) | Yes | Contact phone | Often NULL in data |
| `contactName` | VARCHAR(255) | Yes | Contact person | Often NULL in data |
| `isPartner` | TINYINT(1) | No | `1` = partner store | For "partner stores": `WHERE isPartner = 1` |
| `tier` | VARCHAR(10) | Yes | Account tier/level | Often NULL in data |
| `createdAt` | DATETIME | No | Record creation timestamp | |
| `updatedAt` | DATETIME | No | Last update timestamp | |
| `tenantid` | INT | No | Tenant identifier | Auto-injected |
| `brand_id` | VARCHAR(36) | Yes | Brand reference | |

---

### TABLE: `rhize_partner_stores`

| Attribute | Value |
|---|---|
| **Kind** | MySQL tenant operational table |
| **Purpose** | Partner store roster (minimal version) |
| **Data Grain** | One row per partner customer per tenant |
| **Tenancy** | `tenantid` (INT) auto-injected |
| **Use When** | Simple partner customer name list only. For richer data use `rhize_stores WHERE isPartner = 1` |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `id` | BIGINT UNSIGNED | No | Auto-increment primary key | |
| `customer_name` | TEXT | No | Partner store name | |
| `created_at` | TIMESTAMP | No | Record creation | |
| `updated_at` | TIMESTAMP | No | Last update | |
| `tenantid` | INT | No | Tenant identifier | Auto-injected |
| `brand_id` | VARCHAR(36) | Yes | Brand reference | |

---

### TABLE: `rhize_strain_info`

| Attribute | Value |
|---|---|
| **Kind** | MySQL tenant operational table |
| **Purpose** | Strain genetics and flavor metadata |
| **Data Grain** | One row per strain per tenant |
| **Tenancy** | `tenantid` (INT) auto-injected |
| **Use When** | Strain genetics, flavor profiles, effect tags |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `id` | VARCHAR(36) | No | Primary key | |
| `strain` | VARCHAR(255) | No | Strain name — join key | Join to `rhize_product_lots.strain`, `rhize_live_inventory.strain` |
| `effectTag` | VARCHAR(100) | Yes | Effect: `RELAX`, `ENERGIZE`, `HYBRID`, `HYBRID-Energy` | |
| `genetics1` | VARCHAR(255) | Yes | Parent genetics 1 | |
| `genetics2` | VARCHAR(255) | Yes | Parent genetics 2 | |
| `breeder` | VARCHAR(255) | Yes | Breeder name | |
| `flavor1` | VARCHAR(100) | Yes | Primary flavor | |
| `flavor2` | VARCHAR(100) | Yes | Secondary flavor | |
| `flavor3` | VARCHAR(100) | Yes | Tertiary flavor | |
| `createdAt` | DATETIME | No | Record creation timestamp | |
| `updatedAt` | DATETIME | No | Last update timestamp | |
| `tenantid` | INT | No | Tenant identifier | Auto-injected |
| `brand_id` | VARCHAR(36) | Yes | Brand reference | |

---

### TABLE: `rhize_sales_actions`

| Attribute | Value |
|---|---|
| **Kind** | MySQL tenant CRM table |
| **Purpose** | Sales action queue / CRM follow-up tasks |
| **Data Grain** | One row per sales action per tenant |
| **Tenancy** | `tenantid` (INT) auto-injected |
| **Use When** | Open tasks, CRM queue, follow-ups, sales pipeline |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `id` | VARCHAR(36) | No | Primary key | |
| `customerName` | VARCHAR(255) | Yes | Target customer/store name | |
| `category` | VARCHAR(100) | No | Action category: `MARKET`, `OUTREACH`, etc. | |
| `priority` | INT | No | `1` = highest priority | `ORDER BY priority ASC` for most urgent first |
| `description` | TEXT | Yes | Action description | |
| `status` | VARCHAR(50) | No | `'New'` / `'In Progress'` / `'Done'` | Open queue: `WHERE status <> 'Done'` |
| `notes` | TEXT | Yes | Free-text notes | |
| `offerSent` | TINYINT(1) | Yes | Whether offer was sent (`0` = no) | |
| `lastUpdated` | DATETIME | Yes | Last status update | |
| `createdAt` | DATETIME | No | Record creation timestamp | |
| `tenantid` | INT | No | Tenant identifier | Auto-injected |
| `brand_id` | VARCHAR(36) | Yes | Brand reference | |

---

### TABLE: `rhize_dataset_main`

| Attribute | Value |
|---|---|
| **Kind** | MySQL tenant sales aggregate table — legacy |
| **Purpose** | Tenant's OWN daily sales/revenue summary |
| **Data Grain** | One row per (Product_Name, date, tenant) approx. |
| **Tenancy** | `tenantid` (INT) auto-injected |
| **Legacy Warning** | All numeric columns stored as TEXT — must CAST to DECIMAL for any math |
| **Use When** | "My revenue", "my sales", daily totals, own top products, own product flags |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `id` | BIGINT | No | Row primary key | |
| `Company_Name` | TEXT | Yes | Store/company name | |
| `Product_Name` | TEXT | Yes | Product name | |
| `Category` | TEXT | Yes | Product category | |
| `Type` | TEXT | Yes | Product type | |
| `Days` | TEXT | Yes | Days metric | Cast before math |
| `Flag` | TEXT | Yes | `'Added'` / `'Removed'` / `'No Change'` | Today's new SKUs: `WHERE Flag = 'Added' AND date = (SELECT MAX(date)...)` |
| `Unit` | TEXT | Yes | Pack size | |
| `Price` | TEXT | Yes | Unit price — stored as TEXT | ⚠️ Always `CAST(Price AS DECIMAL(10,2))` for math |
| `Discount_Price_Data` | TEXT | Yes | Discount price | Cast before math |
| `` `Today's_Quantity_Total` `` | TEXT | Yes | Today's quantity | ⚠️ Backtick required. Cast before math |
| `` `1d` `` | TEXT | Yes | 1-day quantity change | ⚠️ Backtick required. Cast before math |
| `` `3d` `` | TEXT | Yes | 3-day quantity change | ⚠️ Backtick required. Cast before math |
| `` `7d` `` | TEXT | Yes | 7-day quantity change | ⚠️ Backtick required. Cast before math |
| `` `14d` `` | TEXT | Yes | 14-day quantity change | ⚠️ Backtick required. Cast before math |
| `THC` | TEXT | Yes | THC percentage as text | Cast before math |
| `SKU` | TEXT | Yes | SKU identifier | |
| `Change` | TEXT | Yes | Units change | Cast before math |
| `Revenue` | TEXT | Yes | Daily revenue — OWN business ONLY | ⚠️ Always `CAST(Revenue AS DECIMAL(10,2))`. This is tenant's OWN revenue — NOT market revenue |
| `date` | TEXT | No | `YYYY-MM-DD` — text not DATE | Last 7d: `WHERE date >= DATE_FORMAT(CURRENT_DATE - INTERVAL 7 DAY, '%Y-%m-%d')`. Latest: `WHERE date = (SELECT MAX(date) FROM rhize_dataset_main)` |
| `created_at` | TIMESTAMP | Yes | Row ingestion timestamp | |
| `tenantid` | INT | No | Tenant identifier | Auto-injected |
| `brand_id` | VARCHAR(36) | Yes | Brand reference | |

---

### TABLE: `rhize_dataset_store`

| Attribute | Value |
|---|---|
| **Kind** | MySQL tenant per-store table |
| **Purpose** | Per-store breakdown of tenant's products |
| **Data Grain** | One row per (date, Product_Name, Company_Name) per tenant |
| **Tenancy** | `tenantid` (INT) auto-injected |
| **Use When** | Store-level product breakdown |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `id` | INT | No | Row primary key | |
| `date` | TEXT | No | `YYYY-MM-DD` text | Same date rules as `rhize_dataset_main`: use `DATE_FORMAT` for arithmetic |
| `Product_Name` | TEXT | Yes | Product name | |
| `Category` | TEXT | Yes | Product category | |
| `Type` | TEXT | Yes | Product type | |
| `Company_Name` | TEXT | Yes | Store name | |
| `SKU` | TEXT | Yes | SKU identifier | |
| `created_at` | TIMESTAMP | Yes | Row ingestion timestamp | |
| `tenantid` | INT | No | Tenant identifier | Auto-injected |
| `brand_id` | VARCHAR(36) | Yes | Brand reference | |

---

### TABLE: `Rhize_sales_data`

| Attribute | Value |
|---|---|
| **Kind** | MySQL tenant sales flat table — Google Sheets sync target |
| **Purpose** | Flat export/snapshot of sales data synced from Google Sheets |
| **Data Grain** | One row per order line item (similar to `rhize_orders` but all TEXT) |
| **Tenancy** | No visible `tenantid` — scope may be implied by sync source |
| **Legacy Warning** | All numeric/date columns stored as TEXT — must CAST before math |
| **Use When** | Only when `rhize_orders` does not have the required data. Prefer `rhize_orders` for order queries |
| **Avoid When** | General order queries — use `rhize_orders` (proper types, tenant-scoped) |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `id` | INT | No | Row primary key | |
| `date` | TEXT | Yes | Order date as text | Cast: `STR_TO_DATE(date, '%Y-%m-%d')` for arithmetic |
| `order_id` | TEXT | Yes | Order identifier | |
| `customer` | TEXT | Yes | Customer/store name | Note: column name is `customer` not `customerName` — different from `rhize_orders` |
| `product_name` | TEXT | Yes | Product name | Note: snake_case unlike `rhize_orders.productName` |
| `product_type` | TEXT | Yes | Product type | |
| `qty` | TEXT | Yes | Units sold — stored as TEXT | ⚠️ Cast: `CAST(qty AS DECIMAL(10,2))` |
| `variant` | TEXT | Yes | Pack size variant | |
| `lot_id` | TEXT | Yes | Lot reference | Note: `lot_id` not `lotNumber` — different from `rhize_orders` |
| `unit_price` | TEXT | Yes | Per-unit price as TEXT | ⚠️ Cast: `CAST(unit_price AS DECIMAL(10,2))` |
| `subtotal` | TEXT | Yes | Line revenue as TEXT | ⚠️ Cast: `CAST(subtotal AS DECIMAL(10,2))` |
| `status` | TEXT | Yes | Order status | |
| `delivery_date` | TEXT | Yes | Delivery date as text | |
| `payment_date` | TEXT | Yes | Payment date as text | |
| `payment_type` | TEXT | Yes | Payment method | |
| `open_balance` | TEXT | Yes | Unpaid balance as text | ⚠️ Cast before math |
| `uid` | TEXT | Yes | Short display ID | |
| `created_at` | TIMESTAMP | Yes | Row ingestion timestamp | |

---

### TABLE: `rhize_user_states`

| Attribute | Value |
|---|---|
| **Kind** | MySQL lookup table |
| **Purpose** | Maps tenants to their US state(s) — drives RLS on PostgreSQL market tables |
| **Data Grain** | One row per (tenantid, state_key) |
| **Use When** | Understanding which state(s) a tenant operates in. Not typically queried directly in business queries |

#### Columns

| Column | Type | Nullable | Business Definition | Usage Notes |
|---|---|---|---|---|
| `id` | BIGINT | No | Primary key | |
| `tenantid` | INTEGER | No | Tenant identifier | References tenant |
| `state_key` | TEXT | No | US state code (VT, MA, etc.) | Maps tenant to state for RLS |

---

### TABLES: `chatbot_example_embeddings` + `chatbot_schema_embeddings` *(RAG Infrastructure — Never Query for Business Data)*

These are internal chatbot infrastructure tables in PostgreSQL.

- `chatbot_example_embeddings` — stores example question → SQL pairs with vector embeddings for RAG retrieval
- `chatbot_schema_embeddings` — stores the schema spec chunks with vector embeddings (the source of the schema RAG your chatbot uses)

> ⚠️ **LLM MUST NEVER query these tables to answer business questions.** They are the chatbot's own memory store. If a user asks about "embeddings" or "schema", that is not a signal to query these tables.

---

## 3. RELATIONSHIP MAP

```
MARKET DATA (PostgreSQL — never join to MySQL rhize_* tables)
──────────────────────────────────────────────────────────────
complete_market_scrapper_dataset
    │  category normalization
    ├──(JOIN lower(category) = raw_lower)──► category_map
    │  aggregate for brand/company/category
    └──────────────────────────────────────► chatbot_mv_market_daily
                                             (pre-aggregated view)


TENANT OPS DATA (MySQL — tenantid INT, always auto-injected)
─────────────────────────────────────────────────────────────
rhize_brands ──(isRhize=1)──► own brand identity

rhize_orders
    ├──(customerName ≈ name)──────────────► rhize_stores
    ├──(lotNumber)────────────────────────► rhize_product_lots
    └──(storeId = id)─────────────────────► rhize_stores

rhize_live_inventory
    ├──(lotNumber)────────────────────────► rhize_product_lots
    └──(strain)───────────────────────────► rhize_strain_info

rhize_product_lots
    └──(strain)───────────────────────────► rhize_strain_info

rhize_dataset_main ──── own daily sales aggregates (standalone)
rhize_dataset_store ─── per-store product breakdown (standalone)
rhize_partner_stores ── minimal partner list (standalone)
rhize_sales_actions ─── CRM queue (standalone)

Rhize_sales_data ─────── Google Sheets sync of orders (standalone)

rhize_user_states ──(tenantid)──► tenant → state mapping (RLS context)
```

### Join Reference Table

| From Table | To Table | Join Columns | Cardinality | Notes |
|---|---|---|---|---|
| `complete_market_scrapper_dataset` | `category_map` | `lower(category) = raw_lower` | Many-to-one | Preferred over inline CASE |
| `chatbot_mv_market_daily` | `category_map` | `lower(category) = raw_lower` | Many-to-one | Use LEFT JOIN + COALESCE |
| `rhize_live_inventory` | `rhize_product_lots` | `lotNumber` | Many-to-one | Lot metadata |
| `rhize_live_inventory` | `rhize_strain_info` | `strain` | Many-to-one | Strain metadata |
| `rhize_product_lots` | `rhize_strain_info` | `strain` | Many-to-one | Strain genetics |
| `rhize_orders` | `rhize_stores` | `customerName` ≈ `name` | Many-to-one | Loose text join — use `lower()` |
| `rhize_orders` | `rhize_stores` | `storeId = id` | Many-to-one | Exact join if storeId not NULL |
| `rhize_orders` | `rhize_product_lots` | `lotNumber` | Many-to-one | Lot metadata on orders |
| `rhize_dataset_store` | `rhize_stores` | `Company_Name` ≈ `name` | Many-to-one | Loose text join |

> ⚠️ **Never join PostgreSQL market tables to MySQL rhize_* tables** — different databases, different dialects.

---

## 4. BUSINESS METRICS

### Category Normalization

**Preferred method — JOIN category_map (PostgreSQL):**
```sql
LEFT JOIN category_map cm ON lower(t.category) = cm.raw_lower
-- Use: COALESCE(cm.category_norm, 'Other') AS category_norm
```

**Fallback CASE block (use only if category_map join is not available):**
```sql
CASE
  WHEN lower(category) LIKE '%flower%'
    OR lower(category) IN ('pre-packed flowers','pre-packed-flower') THEN 'Flower'
  WHEN lower(category) LIKE '%pre%roll%'
    OR lower(category) IN ('preroll','prerolls')                    THEN 'PreRoll'
  WHEN lower(category) LIKE '%vape%'
    OR lower(category) IN ('cartridge','carts','vapecarts','vape-carts','vape pens') THEN 'Vape'
  WHEN lower(category) LIKE '%concentrate%'                         THEN 'Concentrate'
  WHEN lower(category) LIKE '%edible%'                             THEN 'Edible'
  ELSE 'Other'
END AS category_norm
```
> Never write `WHERE category = 'Flower'` under any circumstances.

---

### Metric Definitions

| Metric | Source Table | Formula | Aggregation | Constraints |
|---|---|---|---|---|
| **Market Revenue** | `complete_market_scrapper_dataset` | `price_num × |change|` (pre-baked as `revenue`) | `SUM(revenue)` | Competitor/market only — NOT own revenue |
| **Market Revenue (view)** | `chatbot_mv_market_daily` | Pre-aggregated | `SUM(revenue)` | Preferred for brand/category aggregates |
| **Effective Market Price** | `complete_market_scrapper_dataset` | `COALESCE(price_num, NULLIF(regexp_replace(price,'[^0-9.]','','g'),'')::numeric)` | `AVG(price_n) WHERE price_n > 0` | Always use COALESCE fallback |
| **Market THC** | `complete_market_scrapper_dataset` | Cast via CASE (see §2) | `AVG(thc_num) WHERE thc_num BETWEEN 0 AND 100` | Must cast TEXT first |
| **Sell-Through Units** | `complete_market_scrapper_dataset` | `SUM(change)` | `SUM` | Pre-pack-normalized |
| **Market Share** | `chatbot_mv_market_daily` | `SUM(revenue) / SUM(SUM(revenue)) OVER ()` | Window function | Group by brand or company |
| **SKU Count** | `chatbot_mv_market_daily` | `SUM(sku_count)` | `SUM` | For "most products listed" |
| **Days on Shelf** | `complete_market_scrapper_dataset` | `days_on_shelf` | `AVG / ORDER BY` | Always `WHERE days_on_shelf IS NOT NULL` |
| **Own Revenue (aggregate)** | `rhize_dataset_main` | `CAST(Revenue AS DECIMAL(10,2))` | `SUM(...)` | Own business only. Cast required |
| **Own Revenue (orders)** | `rhize_orders` | `SUM(subtotal)` | `SUM` | Always `WHERE status = 'Completed'` |
| **Outstanding AR** | `rhize_orders` | `SUM(openBalance)` | `SUM` | Filter `status <> 'Completed'` |
| **Available Inventory** | `rhize_live_inventory` | `remaining` = `current_qty - pending` | `SUM(remaining)` | Use `remaining` not `current_qty` |
| **Low Stock** | `rhize_live_inventory` | `WHERE remaining < N` | Filter | Threshold N is context-dependent |
| **Expiring Lots (30d)** | `rhize_product_lots` | `WHERE expirationDate BETWEEN CURRENT_DATE AND DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY)` | Filter | Adjust interval as needed |
| **Own THC** | `rhize_product_lots` | `thc` (already DOUBLE) | `AVG(thc) WHERE thc IS NOT NULL` | No cast needed |
| **Open CRM Tasks** | `rhize_sales_actions` | `WHERE status <> 'Done'` | `COUNT(*)` | Order by `priority ASC` |

---

## 5. QUERY GENERATION RULES

### Rule 1 — Identify data universe first
Before writing any query, determine:
- Question about **market/competitors**? → PostgreSQL market tables
- Question about **own business**? → MySQL `rhize_*` tables
- Never mix both in a single query

### Rule 2 — Table selection for market queries
```
Need SKU-level detail (product_name, thc, flag, days_on_shelf, individual price)?
  → complete_market_scrapper_dataset  [PostgreSQL]

Need brand/company/category aggregates, trends, market share, SKU counts?
  → chatbot_mv_market_daily  [PostgreSQL — 480x smaller, always prefer]
```

### Rule 3 — Always deduplicate the base scraper table
The base table is scraped ~4x/day. For "today's" or "current" data:
```sql
WHERE date = (SELECT MAX(date) FROM complete_market_scrapper_dataset)
```
For time-series, use `chatbot_mv_market_daily` which is already daily-deduplicated.

### Rule 4 — Never filter state manually
Both market tables use PostgreSQL RLS. State is auto-scoped. Never add `WHERE state = 'MA'`.

### Rule 5 — Never write tenantid
All `rhize_*` MySQL tables have `tenantid` (INT) auto-injected by middleware. Never write `WHERE tenantid = ...`.

### Rule 6 — Category normalization is mandatory
Every query filtering or grouping by category on PostgreSQL tables MUST normalize. Preferred: `JOIN category_map`. Fallback: full CASE block. Never write raw category literals like `category = 'Flower'`.

### Rule 7 — Date type awareness by table

| Table | Date Column | Type | Correct Arithmetic |
|---|---|---|---|
| `complete_market_scrapper_dataset` | `date` | TEXT | `to_char(CURRENT_DATE - INTERVAL 'N days', 'YYYY-MM-DD')` |
| `chatbot_mv_market_daily` | `date` | DATE | Direct: `CURRENT_DATE - INTERVAL 'N days'` |
| `rhize_orders` | `date` | DATETIME | `DATE_SUB(CURRENT_DATE, INTERVAL N DAY)` |
| `rhize_dataset_main` | `date` | TEXT | `DATE_FORMAT(CURRENT_DATE - INTERVAL N DAY, '%Y-%m-%d')` |
| `rhize_dataset_store` | `date` | TEXT | `DATE_FORMAT(CURRENT_DATE - INTERVAL N DAY, '%Y-%m-%d')` |
| `Rhize_sales_data` | `date` | TEXT | `DATE_FORMAT` or `STR_TO_DATE` |
| `rhize_product_lots` | `expirationDate` | DATETIME | Direct MySQL date functions |

### Rule 8 — Cast TEXT numerics in legacy tables
`rhize_dataset_main` and `Rhize_sales_data` store all numerics as TEXT:
- `CAST(Revenue AS DECIMAL(10,2))`
- `CAST(Price AS DECIMAL(10,2))`
- `CAST(subtotal AS DECIMAL(10,2))` ← in Rhize_sales_data
- Backtick digit-starting column names: `` CAST(`1d` AS DECIMAL(10,2)) ``

### Rule 9 — Use `remaining` not `current_qty` for sellable inventory
`remaining = current_qty - pending`. Always use `remaining` for available-to-sell queries.

### Rule 10 — Blank filters for free-text brand/company
```sql
WHERE brand IS NOT NULL AND brand <> ''
-- same for company
```

### Rule 11 — Revenue = "Completed" orders only
```sql
WHERE status = 'Completed'   -- for realized revenue
WHERE status <> 'Completed'  -- for open AR
```

### Rule 12 — Own brand identification
```sql
FROM rhize_brands WHERE isRhize = 1
```

### Rule 13 — Partner stores
```sql
FROM rhize_stores WHERE isPartner = 1  -- richer: city, phone, tier
-- or
FROM rhize_partner_stores              -- minimal: customer_name only
```

### Rule 14 — CRM open queue
```sql
WHERE status <> 'Done'
ORDER BY priority ASC
```

### Rule 15 — Price safety for market data
```sql
COALESCE(price_num, NULLIF(regexp_replace(price,'[^0-9.]','','g'),'')::numeric) AS price_n
-- Always filter: WHERE price_n > 0
```

### Rule 16 — THC safety for market data
```sql
CASE WHEN thc ~ '^[0-9]+(\.[0-9]+)?%?$'
  THEN regexp_replace(thc,'[^0-9.]','','g')::numeric
END AS thc_num
-- Then: WHERE thc_num BETWEEN 0 AND 100
```

### Rule 17 — days_on_shelf null safety
```sql
WHERE days_on_shelf IS NOT NULL
-- Always include when sorting or aggregating
```

### Rule 18 — Never scope by brand_id in rhize_orders
`brand_id` in `rhize_orders` can collide cross-tenant. Use brand name for brand-level filtering.

### Rule 19 — Prefer rhize_orders over Rhize_sales_data
`rhize_orders` has proper data types, tenant scoping, and richer columns. Use `Rhize_sales_data` only when `rhize_orders` is missing required fields.

### Rule 20 — Never query infrastructure tables for business answers
`chatbot_example_embeddings`, `chatbot_schema_embeddings` are internal RAG infrastructure tables. No business query should ever reference them. `rhize_sync_log` is a tenant-owned audit log — not used by the chatbot for analytics; do not query it.

---

## 6. COMMON QUERY PATTERNS

### Top N brands by market revenue (last 30 days)
```sql
-- PostgreSQL — use the view
SELECT brand, SUM(revenue) AS total_revenue
FROM chatbot_mv_market_daily
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
  AND brand IS NOT NULL AND brand <> ''
GROUP BY brand
ORDER BY total_revenue DESC
LIMIT 10;
```

### Top SKUs by market sell-through (latest snapshot)
```sql
-- PostgreSQL — use base table for SKU detail
SELECT product_name, brand,
       COALESCE(cm.category_norm, 'Other') AS category_norm,
       SUM(change) AS units_sold, SUM(revenue) AS revenue
FROM complete_market_scrapper_dataset t
LEFT JOIN category_map cm ON lower(t.category) = cm.raw_lower
WHERE date = (SELECT MAX(date) FROM complete_market_scrapper_dataset)
  AND product_name IS NOT NULL AND product_name <> ''
GROUP BY product_name, brand, category_norm
ORDER BY revenue DESC
LIMIT 10;
```

### Own revenue last 7 days
```sql
-- MySQL
SELECT date, SUM(CAST(Revenue AS DECIMAL(10,2))) AS daily_revenue
FROM rhize_dataset_main
WHERE date >= DATE_FORMAT(CURRENT_DATE - INTERVAL 7 DAY, '%Y-%m-%d')
GROUP BY date
ORDER BY date DESC;
```

### Top customers by own revenue (completed orders)
```sql
-- MySQL
SELECT customerName,
       SUM(subtotal) AS total_revenue,
       COUNT(DISTINCT orderNumber) AS order_count
FROM rhize_orders
WHERE status = 'Completed'
GROUP BY customerName
ORDER BY total_revenue DESC
LIMIT 10;
```

### Low stock products
```sql
-- MySQL
SELECT productName, strain, productType, current_qty, remaining
FROM rhize_live_inventory
WHERE remaining < 10
ORDER BY remaining ASC;
```

### Lots expiring in 30 days
```sql
-- MySQL
SELECT lotNumber, strain, thc, tac, expirationDate
FROM rhize_product_lots
WHERE expirationDate BETWEEN CURRENT_DATE AND DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY)
  AND thc IS NOT NULL
ORDER BY expirationDate ASC;
```

### New products added today (market)
```sql
-- PostgreSQL
SELECT product_name, brand, company,
       COALESCE(cm.category_norm, 'Other') AS category_norm,
       price_num
FROM complete_market_scrapper_dataset t
LEFT JOIN category_map cm ON lower(t.category) = cm.raw_lower
WHERE date = (SELECT MAX(date) FROM complete_market_scrapper_dataset)
  AND flag = 'added'
ORDER BY brand;
```

### Market category mix (normalized, last 30 days)
```sql
-- PostgreSQL — use view + category_map
SELECT COALESCE(cm.category_norm, 'Other') AS category_norm,
       SUM(revenue) AS total_revenue
FROM chatbot_mv_market_daily t
LEFT JOIN category_map cm ON lower(t.category) = cm.raw_lower
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY category_norm
ORDER BY total_revenue DESC;
```

### Open CRM sales actions
```sql
-- MySQL
SELECT customerName, category, priority, description, status, lastUpdated
FROM rhize_sales_actions
WHERE status <> 'Done'
ORDER BY priority ASC, lastUpdated DESC;
```

---

## 7. OPTIMIZATION NOTES

1. **Always prefer `chatbot_mv_market_daily` over `complete_market_scrapper_dataset`** for any non-SKU-level query. The view is ~480x smaller per day.
2. **The base scraper table has ~4 rows per SKU per day.** Any query without a `MAX(date)` anchor will multiply row counts and inflate all aggregates.
3. **`category_map` JOIN is preferred over the inline CASE block** — it's maintainable, consistent, and shorter in generated SQL.
4. **`rhize_dataset_main` and `Rhize_sales_data` are legacy tables** — all numerics as TEXT. Budget extra CAST overhead. Prefer `rhize_orders` for order-level queries.
5. **`rhize_live_inventory` has no history** — it is always the latest snapshot. Never attempt trend/time-series queries against it.
6. **String joins** (`customerName` / `name`, `Company_Name` / `name`) are loose text matches — use `lower()` on both sides to avoid missed joins.
7. **`days_on_shelf` is 38% NULL** — always filter `IS NOT NULL` before sorting or aggregating.
8. **`price_num` is ~15% NULL** — always use the COALESCE fallback when computing price-based metrics.
9. **`rhize_user_states`** maps tenants to states and is the source of truth for RLS scoping — not typically queried directly in business SQL.

---

## 8. AMBIGUITIES & WARNINGS

| # | Ambiguity | Resolution |
|---|---|---|
| 1 | `revenue` in `complete_market_scrapper_dataset`/`chatbot_mv_market_daily` vs `Revenue` in `rhize_dataset_main` | Market revenue = competitor sell-through. `rhize_dataset_main.Revenue` = own business. NEVER aggregate together |
| 2 | `thc` in `complete_market_scrapper_dataset` (TEXT, noisy) vs `rhize_product_lots.thc` (DOUBLE, clean) | Always cast market `thc`. Own lots `thc` is already numeric — no cast needed |
| 3 | `category` has 58 raw variants in market tables | Always normalize via `category_map` JOIN or CASE block. Never use raw category literals |
| 4 | `date` column types differ across tables | TEXT in scrapper + `rhize_dataset_main` + `rhize_dataset_store` + `Rhize_sales_data`. DATE in `chatbot_mv_market_daily`. DATETIME in `rhize_orders` + `rhize_product_lots`. See Rule 7 |
| 5 | `company` in market tables vs `Company_Name` in `rhize_dataset_main` | Market: retailer/dispensary. Rhize: own business store. Do not join these |
| 6 | `rhize_brands` mixes own brand (`isRhize=1`) and competitor brands (`isRhize=0`) | Always filter `isRhize` before using brand name |
| 7 | `brand_id` in `rhize_orders` collides cross-tenant | Never scope order queries by `brand_id` |
| 8 | `rhize_stores` vs `rhize_partner_stores` both track partner stores | `rhize_stores WHERE isPartner=1` is richer. Use `rhize_partner_stores` only for minimal name list |
| 9 | Base scraper table has 4 rows per SKU per day | Always anchor on `MAX(date)` for point-in-time. Use `chatbot_mv_market_daily` for time-series |
| 10 | Digit-leading column names in `rhize_dataset_main` | Must backtick: `` `1d` ``, `` `3d` ``, `` `7d` ``, `` `14d` ``, `` `Today's_Quantity_Total` ``. Must cast to DECIMAL |
| 11 | PostgreSQL vs MySQL syntax | Market tables → PostgreSQL (`to_char`, `INTERVAL 'N days'`, `regexp_replace`, `::numeric`). Rhize tables → MySQL (`DATE_FORMAT`, `DATE_SUB`, `DATE_ADD`, `INTERVAL N DAY`, `CAST AS DECIMAL`) |
| 12 | `Rhize_sales_data` vs `rhize_orders` — overlapping purpose | `rhize_orders` is authoritative (proper types, tenant-scoped). `Rhize_sales_data` is a Google Sheets sync with all-TEXT columns. Prefer `rhize_orders` |
| 13 | `customer` (in `Rhize_sales_data`) vs `customerName` (in `rhize_orders`) | Different column names for the same concept. Do not join directly without aliasing |
| 14 | `chatbot_mv_market_daily` (wrapper) vs `mv_market_daily` (raw) | Bot must query `chatbot_mv_market_daily` — RO role has no SELECT on raw `mv_market_daily` |
| 15 | `sku_count` in `chatbot_mv_market_daily` is SMALLINT not INTEGER | Use `SUM(sku_count)` — SMALLINT max is 32767 per row, but aggregated total may exceed that |

---

## 9. FINAL LLM QUERY DECISION TREE

```
User asks a question
        │
        ▼
Is it about competitors / the market / what other brands are doing?
        │                                         │
       YES                                        NO ──────────────────────────────────────────────────────┐
        │                                                                                                   │
        ▼                                                                                                   ▼
Need SKU detail?                                                               Is it about own orders / revenue?
(product_name, individual thc,                                                   → rhize_orders (proper types)
 individual price, flag, days_on_shelf)                                          → rhize_dataset_main (legacy daily aggregate)
        │                                                                        → Rhize_sales_data (Sheets sync, last resort)
       YES              NO
        │                │                                                     Is it about own inventory?
        ▼                ▼                                                        → rhize_live_inventory
  complete_market_   chatbot_mv_market_daily
  scrapper_dataset   (480x smaller,                                            Is it about lots / THC / expiry / lab results?
  + category_map     always prefer)                                              → rhize_product_lots
  JOIN               + category_map
                     JOIN                                                      Is it about strains / genetics / flavors?
                                                                                 → rhize_strain_info

                                                                               Is it about stores / partners?
                                                                                 → rhize_stores WHERE isPartner=1 (rich)
                                                                                 → rhize_partner_stores (name only)

                                                                               Is it about own brand identity / "my brand"?
                                                                                 → rhize_brands WHERE isRhize = 1

                                                                               Is it about sales tasks / CRM / follow-ups?
                                                                                 → rhize_sales_actions

                                                                               Is it about per-store product breakdown?
                                                                                 → rhize_dataset_store

                                                                               ⛔ Is it about embeddings / sync / system?
                                                                                 → DO NOT QUERY — infrastructure tables only
```

---

*Schema version: 2.0 | Validated against: 27 live database screenshots | Generated for: Rhize SaaS Multi-Tenant Cannabis Analytics Platform | Dialects: PostgreSQL + MySQL*

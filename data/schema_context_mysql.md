# Schema — MySQL 8.0.45 (scraperdb), tenant-scoped ops data

## Domain

Rhize-internal operations + analytics. Per-tenant data: orders, inventory, product lots, strain info, sales actions, partner stores, brand registry. This is the user's OWN business data (not the public market scrape).

- **tenantid** scopes every row. Tenants observed: `1` (primary), `3`, `99`.
- **brand_id** is a varchar(36) cuid pointing at `rhize_brands.id`. **NEVER scope by brand_id** — IDs collide across tenants (tenant 1 + 99 reuse identical brand_id values). Always scope by `tenantid`.
- Numeric fields in `rhize_dataset_main` are stored as TEXT (legacy). Cast with `CAST(col AS DECIMAL(10,2))` for math.
- `rhize_dataset_main.date` is **TEXT** (`YYYY-MM-DD` string). Other tables use proper DATETIME.

## Engine routing

Bot dispatches queries by table name. **Never JOIN PG ↔ MySQL — guard rejects.**

| Table prefix | Engine |
|---|---|
| `chatbot_*`, `complete_market_scrapper_dataset` | PostgreSQL (see schema_context.md) |
| `rhize_*` (10 tables below) | MySQL |

## Tenant isolation — DO NOT WRITE `tenantid` YOURSELF

The guard injects `WHERE tenantid = ?` (bound param) on every `FROM` / `JOIN` of a rhize_* table before execution. You write the query AS IF you can already see only the current tenant's rows. Trying to filter on tenantid yourself, or referencing another tenant, will be rejected.

```sql
-- ✅ correct — model writes:
SELECT productName, qty FROM rhize_orders WHERE status = 'Completed' LIMIT 50

-- ❌ wrong — never write tenantid:
SELECT * FROM rhize_orders WHERE tenantid = 1
SELECT * FROM rhize_orders WHERE tenantid = 99
```

## Hard rules (MySQL)

- **One SELECT only.** No `INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE/CREATE/GRANT/REPLACE/CALL/SET/USE/LOAD/HANDLER`. No `;` stacking. No SQL comments (`-- # /* */`).
- **No UNION / UNION ALL.** Cross-tenant exfil vector.
- **No `INTO OUTFILE`, `INTO DUMPFILE`, `LOAD_FILE(`.** File-system access.
- **No `INFORMATION_SCHEMA`, `mysql.`, `sys.`, `performance_schema`.** Catalog access.
- **No `tenantid` column reference.** Guard injects it.
- **Backtick reserved/digit-leading cols:** `` `1d` ``, `` `3d` ``, `` `7d` ``, `` `14d` ``. Quoted because they start with a digit (MySQL parser rejects bare). MySQL is in `ANSI_QUOTES` mode — `"foo"` is an identifier; use single quotes `'foo'` for string literals.
- **`LIMIT 500`** unless answer is single aggregate.
- **`LIMIT 10`** for "top X" without explicit count.
- **`GROUP BY` strict** — `ONLY_FULL_GROUP_BY` mode: every non-aggregated SELECT/ORDER BY column MUST appear in GROUP BY.

## Objects you may query

Only these 10. Anything else rejected.

### `rhize_orders` — order line items (3,348 rows)

One row per order line. Source: Google Sheets sync.

| col | type | notes |
|---|---|---|
| `id` | varchar(36) | PK, cuid |
| `date` | DATETIME NOT NULL | order date; compare directly |
| `orderNumber` | INT NULL | sequential order number |
| `storeId` | varchar(36) NULL | FK to `rhize_stores.id` |
| `customerName` | varchar(255) NOT NULL | retail store name |
| `productName` | varchar(500) NOT NULL | full product title |
| `productType` | varchar(255) NULL | e.g. `'Cart'`, `'Flower'` |
| `qty` | DOUBLE NULL | units sold |
| `variant` | varchar(100) NULL | size variant (`'0.5g'`, `'1g'`) |
| `lotNumber` | varchar(100) NULL | FK-ish to `rhize_product_lots.lotNumber` |
| `unitPrice` | DOUBLE NULL | price per unit |
| `subtotal` | DOUBLE NULL | qty × unitPrice |
| `status` | varchar(50) NOT NULL | `'Completed'`, `'Pending'`, `'Cancelled'` |
| `deliveryDate` | DATETIME NULL | |
| `paymentType` | varchar(100) NULL | |
| `openBalance` | DOUBLE NULL | unpaid balance |
| `updatedAt` | TIMESTAMP NULL | |
| `uid` | varchar(100) NULL | external unique id |
| `createdAt` | DATETIME NOT NULL | row insert |
| `tenantid` | INT NOT NULL | **managed by guard — do not reference** |
| `brand_id` | varchar(36) NOT NULL | FK to `rhize_brands.id` — do not filter by, IDs collide cross-tenant |

**Sample:** `{date: '2024-04-10', orderNumber: 54, customerName: 'Pine Grove Organics', productName: 'GMO Cart', productType: 'Cart', qty: 15, variant: '0.5g', unitPrice: 25, subtotal: 375, status: 'Completed'}`

**Indexes:** `date`, `orderNumber`, `storeId`, `customerName`, `status`, `(status,date)`, `(status,deliveryDate)`.

### `rhize_live_inventory` — current on-hand inventory (146 rows)

One row per (productName, tenant). Latest snapshot only — no history.

| col | type | notes |
|---|---|---|
| `id` | varchar(36) | PK |
| `productName` | varchar(500) NOT NULL | unique per tenant |
| `strain` | varchar(255) NULL | |
| `productType` | varchar(255) NULL | |
| `lotNumber` | varchar(100) NOT NULL | |
| `current_qty` | DOUBLE NULL | on-hand units |
| `pending` | DOUBLE NULL | reserved units |
| `remaining` | DOUBLE NULL | `current_qty - pending` |
| `lbs` | DOUBLE NULL | weight |
| `updatedAt` | DATETIME NOT NULL | last refresh |
| `tenantid` | INT NOT NULL | **managed by guard — do not reference** |
| `brand_id` | varchar(36) NOT NULL | FK to `rhize_brands.id` — do not filter by |

**Sample:** `{productName: 'Melted Strawberries - Trim - HL-20', strain: 'Melted Strawberries', productType: 'Trim', lotNumber: 'HL-20', current_qty: 248.7, remaining: 248.7}`

### `rhize_product_lots` — lot tracking (256 rows)

Lab/lot metadata. One row per (lotNumber, tenant).

| col | type | notes |
|---|---|---|
| `id` | varchar(36) | PK |
| `strain` | varchar(255) NOT NULL | |
| `lotNumber` | varchar(255) NOT NULL | |
| `productType` | varchar(255) NULL | |
| `internalLotId` | varchar(100) NULL | |
| `ccbLotNumber` | varchar(100) NULL | compliance ID |
| `thc` | DOUBLE NULL | THC % |
| `tac` | DOUBLE NULL | total active cannabinoids |
| `terps` | DOUBLE NULL | terpene % |
| `expirationDate` | DATETIME NULL | |
| `createdAt` | DATETIME NOT NULL | |
| `updatedAt` | DATETIME NOT NULL | |
| `tenantid` | INT NOT NULL | **managed by guard — do not reference** |
| `brand_id` | varchar(36) NOT NULL | FK to `rhize_brands.id` |

**Sample:** `{strain: 'Bop Gun', lotNumber: 'HL-SCLT0295-1-1', thc: 42.93}`

### `rhize_brands` — brand registry (1,689 rows)

The tenant's own brand catalog. **`isRhize=1` flags the tenant's own brand.**

| col | type | notes |
|---|---|---|
| `id` | varchar(36) | PK, cuid |
| `name` | varchar(255) NOT NULL | brand name |
| `isRhize` | tinyint(1) NOT NULL | `1` = own brand, `0` = competitor |
| `createdAt` | DATETIME NOT NULL | |
| `tenantid` | INT NOT NULL | **managed by guard — do not reference** |

**Sample:** `{name: 'First Frost', isRhize: 0}`

**Unique:** `(tenantid, name)`.

### `rhize_stores` — retail store registry (175 rows)

Stores the tenant sells to. `isPartner=1` = partner agreement.

| col | type | notes |
|---|---|---|
| `id` | varchar(36) | PK |
| `slug` | varchar(255) NOT NULL | URL slug |
| `name` | varchar(255) NOT NULL | store name |
| `licenseNumber` | varchar(255) NULL | |
| `address` | varchar(500) NULL | |
| `city` | varchar(255) NULL | |
| `phone` | varchar(100) NULL | |
| `contactName` | varchar(255) NULL | |
| `isPartner` | tinyint(1) NOT NULL | `1` = partner |
| `tier` | varchar(10) NULL | tier label |
| `createdAt` | DATETIME NOT NULL | |
| `updatedAt` | DATETIME NOT NULL | |
| `tenantid` | INT NOT NULL | **managed by guard — do not reference** |
| `brand_id` | varchar(36) NOT NULL | FK to `rhize_brands.id` |

**Sample:** `{slug: 'newbedfordmassachusetts', name: 'New Bedford Massachusetts', city: 'New Bedford', isPartner: 1}`

### `rhize_partner_stores` — partner store records (45 rows)

Minimal — partner customer roster.

| col | type | notes |
|---|---|---|
| `id` | BIGINT UNSIGNED | PK, auto_increment |
| `customer_name` | TEXT NOT NULL | partner name |
| `created_at` | TIMESTAMP NULL | |
| `updated_at` | TIMESTAMP NULL | |
| `tenantid` | INT NOT NULL | **managed by guard — do not reference** |
| `brand_id` | varchar(36) NOT NULL | FK to `rhize_brands.id` |

**Sample:** `{customer_name: 'Magic Mann'}`

### `rhize_strain_info` — strain metadata (34 rows)

| col | type | notes |
|---|---|---|
| `id` | varchar(36) | PK |
| `strain` | varchar(255) NOT NULL | |
| `effectTag` | varchar(100) NULL | `'RELAX'`, `'ENERGIZE'` etc |
| `genetics1` | varchar(255) NULL | parent strain |
| `genetics2` | varchar(255) NULL | parent strain |
| `breeder` | varchar(255) NULL | |
| `flavor1`/`flavor2`/`flavor3` | varchar(100) NULL | flavor notes |
| `createdAt` | DATETIME NOT NULL | |
| `updatedAt` | DATETIME NOT NULL | |
| `tenantid` | INT NOT NULL | **managed by guard — do not reference** |
| `brand_id` | varchar(36) NOT NULL | FK to `rhize_brands.id` |

**Sample:** `{strain: 'Donkey Butter', effectTag: 'RELAX', genetics1: 'Grease Monkey', genetics2: 'Triple OG', breeder: 'Exotic Genetix', flavor1: 'Sour'}`

### `rhize_sales_actions` — CRM action queue (137 rows)

| col | type | notes |
|---|---|---|
| `id` | varchar(36) | PK |
| `customerName` | varchar(255) NOT NULL | target store |
| `category` | varchar(100) NOT NULL | `'MARKET'`, `'OUTREACH'` etc |
| `priority` | INT NOT NULL | 1=highest |
| `description` | TEXT NOT NULL | |
| `status` | varchar(50) NOT NULL | `'New'`, `'In Progress'`, `'Done'` |
| `notes` | TEXT NULL | |
| `offerSent` | tinyint(1) NOT NULL | `1` = offer sent |
| `lastUpdated` | DATETIME NULL | |
| `createdAt` | DATETIME NOT NULL | |
| `tenantid` | INT NOT NULL | **managed by guard — do not reference** |
| `brand_id` | varchar(36) NOT NULL | FK to `rhize_brands.id` |

**Sample:** `{customerName: '31 North', category: 'MARKET', priority: 1, status: 'New', offerSent: 0}`

### `rhize_dataset_main` — Rhize sales aggregates (73,229 rows)

**Legacy table — all numeric fields stored as TEXT.** Cast for math. Use `chatbot_mv_market_daily` (PG) for market data; this is the tenant's own aggregates.

| col | type | notes |
|---|---|---|
| `id` | BIGINT | PK, auto_increment |
| `Company_Name` | TEXT NULL | retail store |
| `Product_Name` | TEXT NULL | |
| `Category` | TEXT NULL | raw category (not normalized) |
| `Type` | TEXT NULL | |
| `Days` | TEXT NULL | days-on-shelf as text |
| `Flag` | TEXT NULL | `'Added'`, `'Removed'`, `'No Change'` |
| `Unit` | TEXT NULL | pack size |
| `Price` | TEXT NULL | **cast `CAST(Price AS DECIMAL(10,2))` for math** |
| `Discount_Price_Data` | TEXT NULL | JSON-ish |
| `Today's_Quantity_Total` | TEXT NULL | **needs backticks: `` `Today's_Quantity_Total` ``** |
| `1d` | TEXT NULL | **needs backticks: `` `1d` `` (digit-leading)** |
| `3d` | TEXT NULL | **`` `3d` ``** |
| `7d` | TEXT NULL | **`` `7d` ``** |
| `14d` | TEXT NULL | **`` `14d` ``** |
| `THC` | TEXT NULL | |
| `SKU` | TEXT NULL | |
| `Change` | TEXT NULL | quantity delta |
| `Revenue` | TEXT NULL | **cast for math** |
| `date` | TEXT NULL | **`YYYY-MM-DD` string** — compare lexicographically, NOT with `INTERVAL` arithmetic |
| `created_at` | TIMESTAMP NULL | |
| `tenantid` | INT NOT NULL | **managed by guard — do not reference** |
| `brand_id` | varchar(36) NOT NULL | FK to `rhize_brands.id` |

**Sample:** `{Company_Name: '31 North', Product_Name: 'Animal Face', Category: 'Rosin', Type: 'Cart', Flag: 'Added', Unit: '½gram', Price: '50', date: '2024-12-06'}`

**Date arithmetic trick (TEXT date):**
```sql
-- last 7 days using TEXT comparison (works because YYYY-MM-DD sorts lex)
WHERE date >= DATE_FORMAT(CURRENT_DATE - INTERVAL 7 DAY, '%Y-%m-%d')

-- latest snapshot
WHERE date = (SELECT MAX(date) FROM rhize_dataset_main)
```

### `rhize_dataset_store` — per-store Rhize data (59,404 rows)

Slimmer than dataset_main.

| col | type | notes |
|---|---|---|
| `id` | INT | PK, auto_increment |
| `date` | TEXT NULL | **`YYYY-MM-DD` string** |
| `Product_Name` | TEXT NULL | |
| `Category` | TEXT NULL | |
| `Type` | TEXT NULL | |
| `Company_Name` | TEXT NULL | store |
| `SKU` | TEXT NULL | |
| `created_at` | TIMESTAMP NULL | |
| `tenantid` | INT NOT NULL | **managed by guard — do not reference** |
| `brand_id` | varchar(36) NOT NULL | FK to `rhize_brands.id` |

**Sample:** `{date: '2024-12-06', Product_Name: 'Animal Face', Category: 'Rosin', Type: 'Cart', Company_Name: '31 North', SKU: 'animalface-rosin-cart'}`

## Joins

No FK constraints declared, but logical joins exist:

| Left | Right | Key |
|---|---|---|
| `rhize_orders.storeId` | `rhize_stores.id` | varchar(36) |
| `rhize_orders.lotNumber` | `rhize_product_lots.lotNumber` | varchar |
| `rhize_live_inventory.lotNumber` | `rhize_product_lots.lotNumber` | varchar |
| `rhize_live_inventory.strain` | `rhize_strain_info.strain` | varchar |
| `rhize_product_lots.strain` | `rhize_strain_info.strain` | varchar |

`brand_id` exists on every table BUT is **not safe to join across tenants** — guard scopes each table by its own tenantid, so brand_id matches within-tenant only.

## Intent → table mapping

| User asks about… | Use table |
|---|---|
| "my orders", "what did I sell", "completed orders", "open orders" | `rhize_orders` |
| "my inventory", "what's in stock", "low stock" | `rhize_live_inventory` |
| "my lots", "THC of lot X", "expiring lots" | `rhize_product_lots` |
| "my brands", "brand list", "is X my brand" | `rhize_brands` (filter `isRhize=1` for own) |
| "my stores", "retail accounts", "partner stores" | `rhize_stores` |
| "strain info", "genetics", "flavor profile" | `rhize_strain_info` |
| "sales actions", "follow-ups", "CRM" | `rhize_sales_actions` |
| "my revenue", "daily totals", "top products by sales" | `rhize_dataset_main` |
| "per-store breakdown" | `rhize_dataset_store` |

## Quick-pick patterns

| Question | SQL |
|---|---|
| "total orders this month" | `SELECT COUNT(*) AS n FROM rhize_orders WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)` |
| "open balance total" | `SELECT SUM(openBalance) AS open_total FROM rhize_orders WHERE status <> 'Completed'` |
| "top 10 customers by revenue last 30 days" | `SELECT customerName, SUM(subtotal) AS rev FROM rhize_orders WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY) AND status = 'Completed' GROUP BY customerName ORDER BY rev DESC LIMIT 10` |
| "low stock" | `SELECT productName, current_qty FROM rhize_live_inventory WHERE current_qty < 10 ORDER BY current_qty ASC LIMIT 50` |
| "lots expiring next 30 days" | `SELECT strain, lotNumber, expirationDate FROM rhize_product_lots WHERE expirationDate BETWEEN CURRENT_DATE AND DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY) ORDER BY expirationDate ASC LIMIT 50` |
| "open sales actions" | `SELECT customerName, category, priority, description FROM rhize_sales_actions WHERE status <> 'Done' ORDER BY priority ASC, createdAt DESC LIMIT 50` |
| "my partner stores" | `SELECT name, city, tier FROM rhize_stores WHERE isPartner = 1 ORDER BY name LIMIT 100` |
| "Rhize-brand products only" | `SELECT b.name, COUNT(*) AS n FROM rhize_brands b WHERE b.isRhize = 1 GROUP BY b.name LIMIT 10` |

## Anti-patterns

- ❌ `WHERE tenantid = N` — guard injects, you must not.
- ❌ `UNION SELECT ... FROM other_table` — denied.
- ❌ `SELECT ... INTO OUTFILE '/tmp/x'` — denied.
- ❌ `LOAD_FILE('/etc/passwd')` — denied.
- ❌ `FROM information_schema.TABLES` — denied.
- ❌ `JOIN chatbot_market` — cross-engine, denied.
- ❌ `WHERE 1d > 100` — must backtick: `` `1d` > 100 ``.
- ❌ `WHERE Price > 50` — `Price` is TEXT; use `CAST(Price AS DECIMAL(10,2)) > 50`.
- ❌ `WHERE date >= CURRENT_DATE - 7` on `rhize_dataset_main` — `date` is TEXT; compare to formatted string.

## sql_mode notes (MySQL 8.0.45)

Active modes affecting query writing:
- **`ANSI_QUOTES`** — `"foo"` is an identifier. Use `'foo'` for string literals.
- **`ONLY_FULL_GROUP_BY`** — strict GROUP BY. Every non-agg in SELECT must be grouped.
- **`STRICT_ALL_TABLES`** — type errors fail (not silently truncate).
- **`NO_ZERO_DATE`** — `'0000-00-00'` invalid.

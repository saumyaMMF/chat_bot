"""One-shot helper: append MySQL rhize_* table + column entries to
data/schema_definitions.json. Idempotent — skips ids already present.

Run once:
    uv run python -m scripts._seed_mysql_schema

Then ingest into pgvector:
    uv run python -m scripts.ingest_schema
"""

from __future__ import annotations

import json
from pathlib import Path


DEF_PATH = Path(__file__).resolve().parents[1] / "data" / "schema_definitions.json"


# Table-level entries.
TABLES = [
    ("rhize_orders", "table",
     "MySQL tenant ops table — one row per order line item. Columns include "
     "date (DATETIME), customerName, productName, qty, unitPrice, subtotal, "
     "status ('Completed'|'Pending'|'Cancelled'), openBalance, brand_id, "
     "tenantid. Use for: open orders, completed orders, customer revenue, "
     "sales by product. The user's OWN orders.",
     "Tenant predicate is auto-injected — never write tenantid yourself. "
     "Do NOT scope by brand_id (collides cross-tenant). Use ANSI single-quotes "
     "for strings."),
    ("rhize_live_inventory", "table",
     "MySQL tenant ops table — current on-hand inventory snapshot. One row per "
     "(productName, tenant). Columns: productName, strain, productType, "
     "lotNumber, current_qty, pending, remaining, lbs, updatedAt, tenantid. "
     "Use for: low stock, what's in stock, on-hand units by product.",
     "Tenant predicate is auto-injected. Latest snapshot only — no history."),
    ("rhize_product_lots", "table",
     "MySQL tenant ops table — lot tracking. One row per (lotNumber, tenant). "
     "Columns: strain, lotNumber, thc, tac, terps, expirationDate, "
     "internalLotId, ccbLotNumber, tenantid. Use for: THC by strain, "
     "expiring lots, lot metadata.",
     "Tenant predicate is auto-injected."),
    ("rhize_brands", "table",
     "MySQL tenant brand registry. Columns: id (cuid), name, isRhize "
     "(tinyint — 1 = the user's OWN brand, 0 = competitor brand in their "
     "catalog), createdAt, tenantid. Use for: the tenant's own brand "
     "(isRhize=1), brand catalog list. Unique on (tenantid, name).",
     "Tenant predicate is auto-injected. For the user's OWN brand identity "
     "filter `WHERE isRhize = 1`."),
    ("rhize_stores", "table",
     "MySQL tenant store registry — retail stores the tenant sells to. "
     "Columns: name, slug, licenseNumber, address, city, phone, "
     "contactName, isPartner (tinyint — 1 = partner agreement), tier, "
     "tenantid. Use for: partner stores, retail accounts, store directory.",
     "Tenant predicate is auto-injected."),
    ("rhize_partner_stores", "table",
     "MySQL tenant partner store roster (minimal). Columns: customer_name, "
     "created_at, updated_at, tenantid. Use for: partner customer list.",
     "Tenant predicate is auto-injected."),
    ("rhize_strain_info", "table",
     "MySQL tenant strain metadata. Columns: strain, effectTag (RELAX, "
     "ENERGIZE, etc), genetics1, genetics2, breeder, flavor1/2/3, "
     "tenantid. Use for: strain genetics, flavor profile, effect tags.",
     "Tenant predicate is auto-injected."),
    ("rhize_sales_actions", "table",
     "MySQL tenant CRM action queue. Columns: customerName, category "
     "(MARKET, OUTREACH, etc), priority (int, 1=highest), description, "
     "status (New, In Progress, Done), notes, offerSent, lastUpdated, "
     "tenantid. Use for: open sales actions, follow-ups, CRM queue.",
     "Tenant predicate is auto-injected."),
    ("rhize_dataset_main", "table",
     "MySQL tenant sales aggregate table — the tenant's OWN sales / "
     "revenue data. Legacy: all numeric columns stored as TEXT — must "
     "CAST(col AS DECIMAL(10,2)) for math. Columns: Company_Name, "
     "Product_Name, Category, Type, Days, Flag (Added/Removed/No Change), "
     "Unit, Price, Discount_Price_Data, `Today's_Quantity_Total`, `1d`, "
     "`3d`, `7d`, `14d`, THC, SKU, Change, Revenue, date (TEXT "
     "YYYY-MM-DD), tenantid, brand_id. Use for: 'my revenue', 'my "
     "sales', daily totals, top products by tenant.",
     "Tenant predicate is auto-injected. Backtick digit-leading columns "
     "(`1d`, `3d`, `7d`, `14d`, `Today's_Quantity_Total`). Cast Price / "
     "Revenue to DECIMAL for math. `date` is TEXT — compare lexicographically "
     "or DATE_FORMAT a date-arithmetic expression."),
    ("rhize_dataset_store", "table",
     "MySQL tenant per-store data (slimmer than dataset_main). Columns: "
     "date (TEXT), Product_Name, Category, Type, Company_Name (store), "
     "SKU, tenantid, brand_id. Use for: per-store breakdown of the "
     "tenant's products.",
     "Tenant predicate is auto-injected. `date` is TEXT YYYY-MM-DD."),
]


# Column-level entries — only the most-asked ones per table. Keeps the embed
# count manageable while letting KNN match common phrasings.
COLUMNS = [
    # rhize_orders
    ("rhize_orders", "status", "VARCHAR",
     "Order status: 'Completed', 'Pending', 'Cancelled'. Common filters: "
     "WHERE status = 'Completed' (revenue), WHERE status <> 'Completed' (open).",
     ""),
    ("rhize_orders", "date", "DATETIME",
     "Order date. Compare directly to CURRENT_DATE / DATE_SUB(...). "
     "Last 30 days: WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY).",
     ""),
    ("rhize_orders", "customerName", "VARCHAR",
     "Retail store name on the order. Use lower(customerName) LIKE lower('%X%') "
     "for case-insensitive partial match. Group by customerName for "
     "top-customers-by-revenue queries.",
     ""),
    ("rhize_orders", "subtotal", "DOUBLE",
     "Line revenue (qty × unitPrice). SUM(subtotal) for total revenue. "
     "Combine with WHERE status = 'Completed' for realized revenue.",
     ""),
    ("rhize_orders", "openBalance", "DOUBLE",
     "Unpaid balance per line. SUM(openBalance) for total AR. Usually "
     "filter status <> 'Completed' for outstanding.",
     ""),
    ("rhize_orders", "qty", "DOUBLE",
     "Units sold on this line.",
     ""),
    # rhize_live_inventory
    ("rhize_live_inventory", "current_qty", "DOUBLE",
     "On-hand units. Low stock: WHERE current_qty < N. ORDER BY current_qty ASC.",
     ""),
    ("rhize_live_inventory", "productName", "VARCHAR",
     "Product name. Unique per (productName, tenant).",
     ""),
    ("rhize_live_inventory", "remaining", "DOUBLE",
     "current_qty - pending. Available-to-sell units.",
     ""),
    # rhize_product_lots
    ("rhize_product_lots", "thc", "DOUBLE",
     "THC percentage. Already numeric (no cast needed). NULL-safe: "
     "WHERE thc IS NOT NULL when averaging.",
     ""),
    ("rhize_product_lots", "expirationDate", "DATETIME",
     "Lot expiry. Expiring soon: WHERE expirationDate BETWEEN CURRENT_DATE "
     "AND DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY).",
     ""),
    ("rhize_product_lots", "strain", "VARCHAR",
     "Strain name. Aggregates: AVG(thc) GROUP BY strain.",
     ""),
    # rhize_brands
    ("rhize_brands", "isRhize", "TINYINT",
     "Flag: 1 = the user's OWN brand, 0 = competitor in their catalog. "
     "For 'my brand' / 'my own brand' questions filter WHERE isRhize = 1.",
     ""),
    ("rhize_brands", "name", "VARCHAR",
     "Brand name. Unique per (tenantid, name).",
     ""),
    # rhize_stores
    ("rhize_stores", "isPartner", "TINYINT",
     "Flag: 1 = partner store. For 'my partner stores' filter WHERE isPartner = 1.",
     ""),
    ("rhize_stores", "city", "VARCHAR",
     "Store city.",
     ""),
    # rhize_sales_actions
    ("rhize_sales_actions", "status", "VARCHAR",
     "'New', 'In Progress', 'Done'. Open queue: WHERE status <> 'Done'.",
     ""),
    ("rhize_sales_actions", "priority", "INT",
     "1 = highest. ORDER BY priority ASC.",
     ""),
    # rhize_dataset_main
    ("rhize_dataset_main", "Revenue", "TEXT",
     "Daily revenue, stored as TEXT. ALWAYS cast: "
     "CAST(Revenue AS DECIMAL(10,2)). SUM(CAST(Revenue AS DECIMAL(10,2))) "
     "for totals. This is the tenant's OWN revenue.",
     "Cast to DECIMAL(10,2) for any math."),
    ("rhize_dataset_main", "Price", "TEXT",
     "Unit price, stored as TEXT. Cast: CAST(Price AS DECIMAL(10,2)).",
     "Cast to DECIMAL(10,2) for any math."),
    ("rhize_dataset_main", "date", "TEXT",
     "YYYY-MM-DD string. Compare as text (sorts chronologically). "
     "Last 7 days: WHERE date >= DATE_FORMAT(CURRENT_DATE - INTERVAL 7 DAY, "
     "'%Y-%m-%d'). Latest: WHERE date = (SELECT MAX(date) FROM rhize_dataset_main).",
     "Text not DATE — use DATE_FORMAT for date arithmetic comparisons."),
    ("rhize_dataset_main", "Flag", "TEXT",
     "'Added', 'Removed', 'No Change'. Today's new SKUs: "
     "WHERE Flag = 'Added' AND date = (SELECT MAX(date)…).",
     ""),
]


def main() -> int:
    raw = json.loads(DEF_PATH.read_text(encoding="utf-8"))
    items = raw.get("items") or []
    existing = {i["id"] for i in items}

    added = 0
    for table, kind, definition, restrictions in TABLES:
        item_id = f"table:{table}"
        if item_id in existing:
            continue
        items.append({
            "id": item_id,
            "kind": kind,
            "table_name": table,
            "definition": definition,
            "restrictions": restrictions,
        })
        added += 1

    for table, col, dt, definition, restrictions in COLUMNS:
        item_id = f"col:{table}.{col}"
        if item_id in existing:
            continue
        items.append({
            "id": item_id,
            "kind": "column",
            "table_name": table,
            "column_name": col,
            "data_type": dt,
            "definition": definition,
            "restrictions": restrictions,
        })
        added += 1

    raw["items"] = items
    # Drop the misleading top-level dialect — definitions now span both engines.
    raw["dialect"] = "mixed"
    DEF_PATH.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"appended {added} entries (total now {len(items)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

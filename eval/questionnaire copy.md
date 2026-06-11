# Chatbot Questionnaire

15 natural-language questions per table. Designed to exercise SQL gen
breadth — counts, lists, filters, joins, aggregates, date arithmetic,
ranking, drill-downs.

---

## 1. rhize_dataset_main  (own daily sales aggregate — TEXT date)

1. what's my total revenue last 7 days
2. top 10 products by revenue last 30 days
3. which products had quantity change yesterday
4. show me products with revenue above 500 today
5. average price by category last week
6. how many SKUs i sold today
7. list newly added products today
8. products removed from my catalog today
9. what's my revenue trend last 14 days
10. top company by revenue last 30 days
11. which products have THC above 25 percent
12. count products by category on latest date
13. show me daily revenue for last 30 days
14. live units of brand Rimeline
15. stock of product Berry Fizz

## 2. rhize_orders  (own order line items — DATETIME date)

1. how many orders today
2. total completed sales last 7 days
3. top 10 customers by revenue last 30 days
4. list pending wholesale orders
5. open balance total
6. orders by status this month
7. customers with open balance over 1000
8. best selling products by quantity last 7 days
9. average order value last 30 days
10. revenue by payment type this month
11. show me orders for customer Joe last 14 days
12. orders count by store last 30 days
13. list cancelled orders this week
14. total delivery this month
15. customers who ordered more than 10 times last 30 days

## 3. rhize_live_inventory  (own warehouse stock)

1. how many products in stock
2. low stock items
3. out of stock products
4. total units on hand by product
5. inventory value by lot
6. which lots have remaining quantity below 5
7. show inventory for strain Dulce De Uva
8. how many flower jars are in stock
9. list all trim inventory
10. products with no movement
11. inventory by productType
12. lots ranked by remaining quantity
13. count lots per product
14. show inventory updated in last 7 days
15. accessories in stock

## 4. rhize_product_lots  (own lot-level inventory + expiration)

1. lots expiring next 30 days
2. lots expiring this week
3. how many lots do i have
4. lots created last 30 days
5. expired lots this month
6. lots by strain
7. count of lots per product
8. lots with quantity under 10
9. lots that expire today
10. show me lot HL-20 details
11. list lots for strain Melted Strawberries
12. lots with the longest shelf life remaining
13. lots not yet shipped
14. recently received lots
15. lots grouped by month of expiration

## 5. rhize_stores  (own retail partner directory)

1. my partner stores
2. count of partner stores
3. partner stores by city
4. list non-partner stores
5. partners by tier
6. stores in California
7. how many partners do i have
8. stores added last 30 days
9. stores with no city set
10. partners ranked by tier
11. count partners by state
12. list inactive stores
13. partner store contacts
14. stores with license number set
15. how many premium tier partners

## 6. rhize_brands  (own brand catalog)

1. what is my brand
2. list my brands
3. how many brands do i own
4. show me my Rhize brand
5. when was my brand created
6. brands updated last 30 days
7. all brand IDs
8. brand by name Rhize
9. is Rhize active
10. how many isRhize brands
11. brand metadata for Rhize
12. brands ordered by createdAt
13. brand count by tenant
14. brand display name
15. brand slug list

## 7. rhize_sales_actions  (own CRM activity log)

1. sales actions last 7 days
2. how many sales actions did i log this month
3. sales actions by type
4. recent customer outreach
5. actions by salesperson last 30 days
6. count actions per store
7. follow-ups due this week
8. completed actions today
9. actions for store Cambridgecannabiscompany
10. high priority actions outstanding
11. notes from sales actions last week
12. action types breakdown this quarter
13. actions created yesterday
14. salespeople activity ranking
15. customers contacted last 30 days

## 8. rhize_strain_info  (own strain catalog)

1. list all strains i carry
2. how many strains do i have
3. strains with THC above 25
4. strains by type indica
5. sativa strains list
6. hybrid strains count
7. strain Dulce De Uva details
8. strains added last 30 days
9. strain count by type
10. strain effects for Berry Fizz
11. flavor profile of Melted Strawberries
12. terpenes in strain GMO
13. strains ranked by THC
14. CBD content per strain
15. strain types breakdown

## 9. rhize_dataset_store  (own per-store daily aggregate — TEXT date)

1. revenue per store last 30 days
2. top store by revenue today
3. store performance trend last 14 days
4. which stores have zero sales today
5. average store revenue this week
6. count active stores yesterday
7. stores by quantity sold last 7 days
8. store ranking by revenue this month
9. daily store revenue last 7 days
10. stores with revenue drop week over week
11. show store Domecity revenue last 14 days
12. store revenue by category last 7 days
13. count distinct stores selling today
14. top 5 stores by quantity today
15. store revenue contribution percent last 30 days

## 10. rhize_partner_stores  (own partner-onboarding pipeline)

1. how many partner stores in pipeline
2. partner stores by status
3. recently onboarded partners
4. partner stores pending approval
5. count partners per state
6. partner stores added last 30 days
7. list rejected partner applications
8. active partner pipeline count
9. partners contacted last 7 days
10. partner store by city
11. show partner Cambridgecannabiscompany details
12. partners with active accounts
13. count by partner status
14. partners updated this month
15. partner ranking by onboarding date

## 11. complete_market_scrapper_dataset  (raw market scrape — TEXT date)

1. skus added to market today
2. products removed from market today
3. longest on-shelf SKU
4. how many SKUs in market today
5. SKU price changes last 7 days
6. products with days_on_shelf above 30
7. unique brands scraped today
8. category distribution of SKUs today
9. top SKUs by price today
10. flagged products this week
11. SKUs available in unit gram
12. show me product Berry Fizz across market
13. count SKUs per company today
14. SKU revenue ranking today
15. discount SKUs today

## 12. chatbot_mv_market_daily  (pre-aggregated market view — DATE)

1. top 5 brands in market last 30 days
2. market share by brand today
3. market share by company today
4. competitor brand revenue last 7 days
5. industry wide category revenue today
6. top stores in market this week
7. category revenue distribution today
8. how is brand Zizzle doing in market
9. company Sweetspot market revenue
10. category preroll market share
11. top 10 brands by quantity last 30 days
12. brand revenue trend last 14 days
13. market total revenue today
14. category flower revenue this week
15. brands with most SKUs listed

## 13. category_map  (Postgres normalization table)

1. how many categories are defined
2. list all canonical categories
3. category mappings count
4. category aliases for Flower
5. mappings updated last 30 days
6. how many aliases per category
7. show me preroll category mappings
8. uncategorized aliases
9. duplicate category names
10. category vape mappings
11. concentrate aliases list
12. edible category mappings
13. mappings created today
14. mappings by canonical category
15. category mappings ordered by usage

## 14. Rhize_sales_data  (legacy own sales — TEXT numerics)

1. legacy sales total last 30 days
2. legacy revenue trend last 14 days
3. top legacy customer by revenue
4. legacy sales count today
5. legacy sales by product last 7 days
6. average legacy order value last 30 days
7. legacy sales by store this month
8. legacy revenue per category last week
9. legacy sales ranked by quantity
10. legacy sales for brand Rhize last 30 days
11. legacy sales not yet completed
12. compare legacy vs current revenue last 30 days
13. legacy data freshness
14. legacy sales daily series
15. legacy sales total this year

## 15. rhize_user_states  (Postgres RLS state-assignment table)

1. how many states am i assigned
2. list my assigned states
3. which states do i have access to
4. count users per state
5. show all state assignments
6. states active for my brand
7. tenants with multiple states
8. recently added state assignments
9. inactive state assignments
10. states without users
11. state assignment changes last 30 days
12. count distinct states overall
13. my state codes
14. state coverage by tenant
15. user count per state

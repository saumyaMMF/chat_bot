# `rhize_partner_stores` (mysql)

- **Schema:** —
- **Rows:** 45
- **Columns:** 6
- **Primary key:** `id`
- **Indexes:** `id`(U: id), `idx_partner_stores_tenantid`(N: tenantid), `PRIMARY`(U: id)

## Columns

### `id` — integer

- **Declared type:** `bigint unsigned`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 45 · **Distinct:** 45 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, LOW-CARDINALITY (categorical), PRIMARY-KEY, AUTO-INCREMENT
- **Range:** min=`1` · max=`315`
- **Length:** min=1 · max=3 · avg=2.13
- **Pattern hints:** integer-as-text
- **All distinct values (45):** `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11`, `12`, `13`, `14`, `15`, `16`, `17`, `18`, `19`, `20`, `21`, `22`, `23`, `24`, `25`, `26`, `27`, `28`, `29`, `30`, `301`, `302`, `303`, `304`, `305`, `306`, `307`, `308`, `309`, `310`, `311`, `312`, `313`, `314`, `315`

### `customer_name` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 45 · **Distinct:** 45 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, LOW-CARDINALITY (categorical)
- **Range:** min=`31 North` · max=`Valleymeade`
- **Length:** min=4 · max=33 · avg=14.82
- **All distinct values (45):** `31 North`, `Cambridge`, `Capital Cannabis Company`, `Cloud 9`, `Demo Dispensary 03`, `Demo Dispensary 10`, `Demo Dispensary 31`, `Demo Dispensary 32`, `Demo Dispensary 33`, `Demo Dispensary 34`, `Demo Dispensary 35`, `Demo Dispensary 36`, `Demo Dispensary 37`, `Demo Dispensary 38`, `Demo Dispensary 39`, `Demo Dispensary 40`, `Demo Dispensary 41`, `Demo Dispensary 42`, `Demo Dispensary 43`, `Domecity`, `FLORA`, `Forbin's Reserve`, `Freedom Flower, LLC`, `Garcia's`, `GMCW`, `Gram Central`, `Higher Elevation`, `Kushies`, `Magic Mann`, `Milton Remedies`, `Mothaplant`, `Mountain Girl`, `Pine Grove Organics`, `Polestar`, `Poultney Cannabis Supply`, `Rimeline`, `Rolling Twenties`, `Something Wicked Cannabis Company`, `Somewhere On The Mountain`, `Sunday Drive`, `Sweet Spot`, `The Bud Stop`, `The Gas Station`, `The Tea House`, `Valleymeade`

### `created_at` — datetime

- **Declared type:** `timestamp`
- **Nullable:** True · **Null %:** 0.0%
- **Rows:** 45 · **Distinct:** 2 (4.44% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`2026-04-10 08:39:44` · max=`2026-06-04 11:10:00`
- **Length:** min=19 · max=19 · avg=19.0
- **Pattern hints:** datetime-string
- **All distinct values (2):** `2026-04-10 08:39:44`, `2026-06-04 11:10:00`

### `updated_at` — datetime

- **Declared type:** `timestamp`
- **Nullable:** True · **Null %:** 0.0%
- **Rows:** 45 · **Distinct:** 2 (4.44% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`2026-04-10 08:39:44` · max=`2026-06-04 11:10:00`
- **Length:** min=19 · max=19 · avg=19.0
- **Pattern hints:** datetime-string
- **All distinct values (2):** `2026-04-10 08:39:44`, `2026-06-04 11:10:00`

### `tenantid` — integer

- **Declared type:** `int`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 45 · **Distinct:** 2 (4.44% of non-null)
- **Flags:** LOW-CARDINALITY (categorical), INDEXED
- **Range:** min=`1` · max=`99`
- **Length:** min=1 · max=2 · avg=1.33
- **Pattern hints:** boolean-token, integer-as-text
- **All distinct values (2):** `1`, `99`

### `brand_id` — text

- **Declared type:** `varchar(36)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 45 · **Distinct:** 2 (4.44% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`ca323241-ef74-425f-aa67-239247ccd0e9` · max=`cmmakqdsn0037qsoig4b4yo9t`
- **Length:** min=25 · max=36 · avg=28.67
- **Pattern hints:** uuid
- **All distinct values (2):** `ca323241-ef74-425f-aa67-239247ccd0e9`, `cmmakqdsn0037qsoig4b4yo9t`

## Sample rows

| id | customer_name | created_at | updated_at | tenantid | brand_id |
| --- | --- | --- | --- | --- | --- |
| 1 | Magic Mann | 2026-04-10 08:39:44 | 2026-04-10 08:39:44 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| 2 | Mountain Girl | 2026-04-10 08:39:44 | 2026-04-10 08:39:44 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| 3 | Cloud 9 | 2026-04-10 08:39:44 | 2026-04-10 08:39:44 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| 4 | FLORA | 2026-04-10 08:39:44 | 2026-04-10 08:39:44 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| 5 | Higher Elevation | 2026-04-10 08:39:44 | 2026-04-10 08:39:44 | 1 | cmmakqdsn0037qsoig4b4yo9t |

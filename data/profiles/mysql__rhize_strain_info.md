# `rhize_strain_info` (mysql)

- **Schema:** —
- **Rows:** 34
- **Columns:** 13
- **Primary key:** `id`
- **Indexes:** `PRIMARY`(U: id), `uq_strain_tenant`(U: strain,tenantid)

## Columns

### `id` — text

- **Declared type:** `varchar(36)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 34 · **Distinct:** 34 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, LOW-CARDINALITY (categorical), PRIMARY-KEY
- **Range:** min=`cmmaje4mq01hrzpoi7uwprrhp` · max=`demo_sn_e40782ebb36657d`
- **Length:** min=23 · max=25 · avg=24.0
- **All distinct values (34):** `cmmaje4mq01hrzpoi7uwprrhp`, `cmmaje4x701hszpoi92vv1628`, `cmmaje55n01htzpoif2cd399t`, `cmmaje5dj01huzpoidmfja4jf`, `cmmaje5mr01hvzpoiccwgfrh1`, `cmmaje5vb01hwzpoii5kpxqop`, `cmmaje63a01hxzpoi38nfyx4y`, `cmmaje6cc01hyzpoigf8in666`, `cmmaje6kv01hzzpoit2p4138j`, `cmmaje6sr01i0zpoi4x70cxzg`, `cmmaje70p01i1zpoitaw4qbmj`, `cmmaje7ag01i2zpoilll7nlcg`, `cmmaje7iz01i3zpoi37lehxcb`, `cmmaje7ri01i4zpoiwmfx023n`, `cmmaje80401i5zpoi2csid1oh`, `cmmaje88l01i6zpoir59c2hs1`, `cmmaje8gi01i7zpoi059o4roc`, `demo_sn_0e62719f2620df9`, `demo_sn_1e675c4b4354a14`, `demo_sn_257e76005cd92c7`, `demo_sn_379742f20b095df`, `demo_sn_42a43347e29a4d2`, `demo_sn_469e7c0a2941dcd`, `demo_sn_5b7aee7d2abb7be`, `demo_sn_7a71ec4407a5954`, `demo_sn_7c9cf2d5337e630`, `demo_sn_8a85b9c2d0cf515`, `demo_sn_8bd6837618247df`, `demo_sn_9a3caa27d8cab1a`, `demo_sn_c7dd2ca41335aa1`, `demo_sn_cbb0b4e9f608b65`, `demo_sn_cc8c098dc03be8b`, `demo_sn_cefd32ee9a799dd`, `demo_sn_e40782ebb36657d`

### `strain` — text

- **Declared type:** `varchar(255)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 34 · **Distinct:** 17 (50.0% of non-null)
- **Flags:** LOW-CARDINALITY (categorical), INDEXED
- **Range:** min=`Berry Fizz` · max=`The Hive`
- **Length:** min=3 · max=19 · avg=12.0
- **All distinct values (17):** `Berry Fizz`, `Black Maple`, `Candied Oranges`, `Deathstar`, `Donkey Butter`, `Dulce de Uva`, `G13 Skunk`, `GMO`, `Honey Banana`, `Lavender Piff`, `Melted Strawberries`, `Moroccan Peaches`, `Papaya Juice`, `Sherb Cream Pie`, `Sour Diesel`, `Strawberry Guava`, `The Hive`

### `effectTag` — text

- **Declared type:** `varchar(100)`
- **Nullable:** True · **Null %:** 0.0%
- **Rows:** 34 · **Distinct:** 5 (14.71% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`ENERGY` · max=`RELAX`
- **Length:** min=5 · max=13 · avg=7.65
- **All distinct values (5):** `ENERGY`, `HYBRID`, `HYBRID-Energy`, `HYBRID-Relax`, `RELAX`

### `genetics1` — text

- **Declared type:** `varchar(255)`
- **Nullable:** True · **Null %:** 0.0%
- **Rows:** 34 · **Distinct:** 14 (41.18% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`Chemdawg` · max=`Strawberry Guava`
- **Length:** min=6 · max=17 · avg=11.59
- **All distinct values (14):** `Chemdawg`, `Dulce de Uva`, `G13 Haze`, `Grease Monkey`, `Honey Banana`, `Ice Cream Cake`, `Lavender`, `Mimosa V6`, `Papaya`, `Papaya Bx`, `Sour Diesel`, `Spanish Barbara`, `Strawberry Banana`, `Strawberry Guava`

### `genetics2` — text

- **Declared type:** `varchar(255)`
- **Nullable:** True · **Null %:** 0.0%
- **Rows:** 34 · **Distinct:** 15 (44.12% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`Girl Scout Cookies` · max=`Z`
- **Length:** min=1 · max=27 · avg=10.71
- **All distinct values (15):** `Girl Scout Cookies`, `GMO`, `Grape Pie x Wedding Crasher`, `Honey Boo Boo`, `Lemon Tree Skorange`, `Papaya`, `Piff x Uptown Haze`, `Red Piegasm`, `Sensi Star`, `Sherb Bx1`, `Sherbanger`, `Skunk #1`, `Super Skunk`, `Triple OG`, `Z`

### `breeder` — text

- **Declared type:** `varchar(255)`
- **Nullable:** True · **Null %:** 0.0%
- **Rows:** 34 · **Distinct:** 13 (38.24% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`808 Genetics` · max=`Terp Fountain Genetics`
- **Length:** min=9 · max=22 · avg=14.47
- **All distinct values (13):** `808 Genetics`, `Bloom Seed Co`, `Dominion Seed Co`, `Elemental Seeds`, `Exotic Genetix`, `Mamiko Seeds`, `NY Legend`, `Piff Coast`, `Purple City Genetics`, `Seed Junky Genetics`, `Symbiotic Genetics`, `Team Deathstar`, `Terp Fountain Genetics`

### `flavor1` — text

- **Declared type:** `varchar(100)`
- **Nullable:** True · **Null %:** 0.0%
- **Rows:** 34 · **Distinct:** 15 (44.12% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`Banana` · max=`Sweet`
- **Length:** min=3 · max=6 · avg=5.47
- **All distinct values (15):** `Banana`, `Berry`, `Creamy`, `Diesel`, `Floral`, `Fruity`, `Garlic`, `Gas`, `Grape`, `Herbal`, `Orange`, `Papaya`, `Peach`, `Sour`, `Sweet`

### `flavor2` — text

- **Declared type:** `varchar(100)`
- **Nullable:** True · **Null %:** 0.0%
- **Rows:** 34 · **Distinct:** 13 (38.24% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`Berry` · max=`Tropical`
- **Length:** min=4 · max=8 · avg=5.41
- **All distinct values (13):** `Berry`, `Candy`, `Citrus`, `Diesel`, `Floral`, `Fruit`, `Haze`, `Honey`, `Rubber`, `Skunk`, `Sour`, `Sweet`, `Tropical`

### `flavor3` — text

- **Declared type:** `varchar(100)`
- **Nullable:** True · **Null %:** 0.0%
- **Rows:** 34 · **Distinct:** 9 (26.47% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`Candy` · max=`Tropical`
- **Length:** min=3 · max=8 · avg=4.76
- **All distinct values (9):** `Candy`, `Creamy`, `Funk`, `Gas`, `Skunk`, `Soda`, `Spice`, `Sweet`, `Tropical`

### `createdAt` — datetime

- **Declared type:** `datetime`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 34 · **Distinct:** 7 (20.59% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`2026-03-03 11:40:55` · max=`2026-06-04 11:10:00`
- **Length:** min=19 · max=19 · avg=19.0
- **Pattern hints:** datetime-string
- **All distinct values (7):** `2026-03-03 11:40:55`, `2026-03-03 11:40:56`, `2026-03-03 11:40:57`, `2026-03-03 11:40:58`, `2026-03-03 11:40:59`, `2026-03-03 11:41:00`, `2026-06-04 11:10:00`

### `updatedAt` — datetime

- **Declared type:** `datetime`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 34 · **Distinct:** 7 (20.59% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`2026-03-03 11:40:55` · max=`2026-06-04 11:10:00`
- **Length:** min=19 · max=19 · avg=19.0
- **Pattern hints:** datetime-string
- **All distinct values (7):** `2026-03-03 11:40:55`, `2026-03-03 11:40:56`, `2026-03-03 11:40:57`, `2026-03-03 11:40:58`, `2026-03-03 11:40:59`, `2026-03-03 11:41:00`, `2026-06-04 11:10:00`

### `tenantid` — integer

- **Declared type:** `int`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 34 · **Distinct:** 2 (5.88% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`1` · max=`99`
- **Length:** min=1 · max=2 · avg=1.5
- **Pattern hints:** boolean-token, integer-as-text
- **All distinct values (2):** `1`, `99`

### `brand_id` — text

- **Declared type:** `varchar(36)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 34 · **Distinct:** 2 (5.88% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`ca323241-ef74-425f-aa67-239247ccd0e9` · max=`cmmakqdsn0037qsoig4b4yo9t`
- **Length:** min=25 · max=36 · avg=30.5
- **Pattern hints:** uuid
- **All distinct values (2):** `ca323241-ef74-425f-aa67-239247ccd0e9`, `cmmakqdsn0037qsoig4b4yo9t`

## Sample rows

| id | strain | effecttag | genetics1 | genetics2 | breeder | flavor1 | flavor2 | flavor3 | createdat | updatedat | tenantid | brand_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cmmaje4mq01hrzpoi7uwprrhp | Donkey Butter | RELAX | Grease Monkey | Triple OG | Exotic Genetix | Sour | Rubber | Gas | 2026-03-03 11:40:55 | 2026-03-03 11:40:55 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| cmmaje4x701hszpoi92vv1628 | Papaya Juice | HYBRID-Energy | Papaya | GMO | 808 Genetics | Papaya | Citrus | Sweet | 2026-03-03 11:40:56 | 2026-03-03 11:40:56 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| cmmaje55n01htzpoif2cd399t | Melted Strawberries | HYBRID | Strawberry Guava | GMO | Bloom Seed Co | Gas | Berry | Funk | 2026-03-03 11:40:56 | 2026-03-03 11:40:56 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| cmmaje5dj01huzpoidmfja4jf | Black Maple | HYBRID | Dulce de Uva | Sherbanger | Bloom Seed Co | Herbal | Floral | Skunk | 2026-03-03 11:40:56 | 2026-03-03 11:40:56 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| cmmaje5mr01hvzpoiccwgfrh1 | Honey Banana | RELAX | Strawberry Banana | Honey Boo Boo | Elemental Seeds | Banana | Honey | Tropical | 2026-03-03 11:40:56 | 2026-03-03 11:40:56 | 1 | cmmakqdsn0037qsoig4b4yo9t |

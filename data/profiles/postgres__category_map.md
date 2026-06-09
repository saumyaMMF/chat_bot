# `category_map` (postgres)

- **Schema:** public
- **Rows:** 47
- **Columns:** 2
- **Primary key:** `raw_lower`
- **Indexes:** `category_map_pkey`(U: raw_lower), `category_map_raw_lower_idx`(N: raw_lower)

## Columns

### `raw_lower` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 47 · **Distinct:** 47 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, LOW-CARDINALITY (categorical)
- **Range:** min=`accessories` · max=`vaporizers`
- **Length:** min=3 · max=25 · avg=12.26
- **All distinct values (47):** `accessories`, `beverage`, `cartridge`, `carts`, `cbd`, `concentrate`, `concentrates`, `concentrates (med)`, `distillate edibles`, `edible`, `edibles`, `edibles (med)`, `flower`, `flower (except deli)`, `flower (med)`, `formlulated edibles`, `infused pre-roll`, `infused preroll`, `infused pre-rolls`, `infused pre-roll (single)`, `live rosin edibles`, `pre-packed-flower`, `pre-packed flowers`, `pre-roll`, `preroll`, `pre-roll (infused)`, `pre roll (multi-pack)`, `pre-roll (multi-pack)`, `pre rolls`, `pre-rolls`, `prerolls`, `pre roll (single)`, `pre-rolls (single)`, `rosin`, `thc vape`, `tinctures`, `topicals`, `uncategorized`, `vape`, `vape batteries`, `vape/cart`, `vape cart & concentrate`, `vape-carts`, `vapecarts`, `vape pens`, `vapes`, `vaporizers`

### `category_norm` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 47 · **Distinct:** 6 (12.77% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`Concentrate` · max=`Vape`
- **Length:** min=4 · max=11 · avg=6.09
- **All distinct values (6):** `Concentrate`, `Edible`, `Flower`, `Other`, `PreRoll`, `Vape`

## Sample rows

| raw_lower | category_norm |
| --- | --- |
| flower | Flower |
| flower (except deli) | Flower |
| flower (med) | Flower |
| pre-packed flowers | Flower |
| pre-packed-flower | Flower |

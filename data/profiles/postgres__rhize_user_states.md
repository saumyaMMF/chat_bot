# `rhize_user_states` (postgres)

- **Schema:** public
- **Rows:** 3
- **Columns:** 3
- **Primary key:** `id`
- **Indexes:** `idx_user_states_tenantid`(N: tenantid), `rhize_user_states_pkey`(U: id), `rhize_user_states_tenantid_state_key_key`(U: tenantid,state_key)

## Columns

### `id` — integer

- **Declared type:** `bigint (int8)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 3 · **Distinct:** 3 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, LOW-CARDINALITY (categorical)
- **Range:** min=`1` · max=`6`
- **Length:** min=1 · max=1 · avg=1.0
- **Pattern hints:** integer-as-text
- **All distinct values (3):** `1`, `2`, `6`

### `tenantid` — integer

- **Declared type:** `integer (int4)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 3 · **Distinct:** 3 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, LOW-CARDINALITY (categorical)
- **Range:** min=`1` · max=`99`
- **Length:** min=1 · max=2 · avg=1.33
- **Pattern hints:** integer-as-text
- **All distinct values (3):** `1`, `3`, `99`

### `state_key` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 3 · **Distinct:** 2 (66.67% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`MA` · max=`VT`
- **Length:** min=2 · max=2 · avg=2.0
- **All distinct values (2):** `MA`, `VT`

## Sample rows

| id | tenantid | state_key |
| --- | --- | --- |
| 6 | 3 | MA |
| 1 | 1 | VT |
| 2 | 99 | VT |

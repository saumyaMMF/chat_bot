# `rhize_live_inventory` (mysql)

- **Schema:** —
- **Rows:** 146
- **Columns:** 12
- **Primary key:** `id`
- **Indexes:** `idx_lotNumber`(N: lotNumber), `idx_strain`(N: strain), `PRIMARY`(U: id), `uq_product_tenant`(U: productName,tenantid)

## Columns

### `id` — text

- **Declared type:** `varchar(36)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 146 · **Distinct:** 146 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, PRIMARY-KEY
- **Range:** min=`0clgn3ickmpwdlu53` · max=`zvtr5x76jmpwdlr0y`
- **Length:** min=17 · max=23 · avg=20.0
- **All distinct values (146):** `0clgn3ickmpwdlu53`, `162eaz2z9mpwdlskd`, `1jadje5a4mpwdlopv`, `1y2fbdbh5mpwdlr7w`, `2xk3pdynympwdloc1`, `37uq3fgkjmpwdlkhm`, `4u1tbudiompwdlp3q`, `5aztpk7xgmpwdlqn3`, `5ji8psf4dmpwdluq0`, `6in03qy0qmpwdlq99`, `6r5ip8q4empwdlwab`, `727186ueqmpwdluj3`, `7y99djpxgmpwdlpvf`, `9nwpznb21mpwdlxto`, `a5yahmhj6mpwdlyek`, `bmwqhnlocmpwdlty6`, `bn3i6zgnompwdlx8y`, `bu6tqltx6mpwdlwh8`, `c6bam3w1qmpwdlphl`, `cbvydej7umpwdlret`, `cnbgqgwrdmpwdlkvh`, `ctexu3g79mpwdlrzj`, `cwujq3dlampwdlln6`, `d8c2kb537mpwdlm7y`, `demo_iv_0185f3bc3c51f9b`, `demo_iv_030cf99fa175763`, `demo_iv_0363351050f5afb`, `demo_iv_07d48518570b3e1`, `demo_iv_092bd614e9250d6`, `demo_iv_0e0d2a70f620401`, `demo_iv_14b170226bd36ee`, `demo_iv_167216c6ff03888`, `demo_iv_1a8c63a14d62e05`, `demo_iv_1b1d3fae1740ba7`, `demo_iv_1e1191160de1199`, `demo_iv_239af4c75387262`, `demo_iv_24d8a511a4712e9`, `demo_iv_25d67548d8dfc7e`, `demo_iv_25fdba052d89597`, `demo_iv_2a16f3b66cb051f`, `demo_iv_3a16404eec9b1ce`, `demo_iv_3fddf7948933ff4`, `demo_iv_440aa7cda111868`, `demo_iv_446b089ec784209`, `demo_iv_4597b87a545fc3d`, `demo_iv_48ee9424eb87f39`, `demo_iv_490f803f18981ec`, `demo_iv_4cdbe40f685ae72`, `demo_iv_517b9e30cd352b2`, `demo_iv_545b95a702776ad`, `demo_iv_569868dd649bb6b`, `demo_iv_577f7c9a8cf9754`, `demo_iv_586c9059e1f73a8`, `demo_iv_5b85f31241eaa41`, `demo_iv_5d58c7fdfc3305b`, `demo_iv_604721a09b0a7fd`, `demo_iv_692f5316c6aa742`, `demo_iv_72fdcc8e47c40d4`, `demo_iv_740e867e0b0b22b`, `demo_iv_795eba0457b2bf2`, `demo_iv_7bc3deba8b291e9`, `demo_iv_87d7c871a95ddfb`, `demo_iv_88e7692dc6ed092`, `demo_iv_8cbde06cbd17b7f`, `demo_iv_8d20ac221d763d1`, `demo_iv_8dbb2647e42089c`, `demo_iv_8e9ca5ffd471bd1`, `demo_iv_915b74b8ecc9b07`, `demo_iv_9189b51c054d5b9`, `demo_iv_9406e3836464e11`, `demo_iv_9bce268fa4fcf06`, `demo_iv_9c030dbbe7e6d7b`, `demo_iv_a07c5061b7800a6`, `demo_iv_a0c6021d9b64994`, `demo_iv_a306b0d1a35df72`, `demo_iv_a5d16123952fec8`, `demo_iv_aa60c29ba9ad72a`, `demo_iv_b1733a807a9a1cc`, `demo_iv_b2e52c0edfd12eb`, `demo_iv_b3626f6779308a9`, `demo_iv_b4d5fed2d40141f`, `demo_iv_b8d8687e43a0d6e`, `demo_iv_c1a3711741685f2`, `demo_iv_ca2556d6d6f556f`, `demo_iv_cfbc3ea8e23af91`, `demo_iv_d43992c6143e55f`, `demo_iv_d567c4413c8ca76`, `demo_iv_d7b912b59ddd58f`, `demo_iv_da5371ae537eee4`, `demo_iv_df1e984cac8f598`, `demo_iv_e124f1d387dea50`, `demo_iv_e831764b97774c5`, `demo_iv_efd1b0feb612710`, `demo_iv_f35dfb242bea909`, `demo_iv_f6e5fa5263811de`, `demo_iv_f9bb67c91f6e71b`, `demo_iv_f9cac27169a2bc3`, `dj3ugf5h9mpwdlubz`, `fhhkxr1d9mpwdlrlo`, `fkxaofp05mpwdlwv2`, `gibz0bbd3mpwdltr9`, `gt2tzlzzsmpwdly0q`, `hmducr6i0mpwdlnr9`, `idbj4ha8smpwdloiy`, `idh92aj4jmpwdll2f`, `iendzyb05mpwdlt6i`, `it8qt0pc6mpwdllu3`, `j9f711bp7mpwdlylx`, `jcsrc22ypmpwdlqu1`, `kbkjan7hwmpwdlvbp`, `kpraeey52mpwdluxu`, `ks1l3zj3tmpwdlsr9`, `ksoer101ampwdllg9`, `l03n0f08ampwdlmso`, `l46kglc14mpwdlmev`, `l9wmz4bfempwdlxmr`, `lnwq7bbgqmpwdlmzl`, `ntwfnmy8cmpwdlqg6`, `om6ffv7qampwdlm10`, `p5rfdskpqmpwdlv4r`, `plmq1mk8qmpwdlq2c`, `pulg7vk6fmpwdlw3e`, `q6iiqmf9lmpwdlows`, `rsgo200f1mpwdlsde`, `rz7s17vrhmpwdln6k`, `s3up6aybtmpwdlndg`, `sotw6kl8hmpwdlx1z`, `ssm3mu8t3mpwdlvim`, `t8iu5ih90mpwdlny7`, `tmibmdehwmpwdlo53`, `tyasggo5vmpwdlpoi`, `v8i48sqdrmpwdltdf`, `vbtgg58o9mpwdls6g`, `vnoouw77ampwdlvpj`, `vywq7no5fmpwdlpao`, `w9jen5mbrmpwdlvwg`, `weshmjt5hmpwdlxfu`, `wvoqlb6vompwdlrsl`, `x2dye4dy6mpwdly7n`, `xb9248lbympwdltkc`, `xyto5j9egmpwdlwo5`, `y4g9uq47rmpwdlnkd`, `zody3sn2umpwdlsye`, `zrlmy9qjcmpwdll9c`, `zvsy3y8y6mpwdlmlr`, `zvtr5x76jmpwdlr0y`

### `productName` — text

- **Declared type:** `varchar(500)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 146 · **Distinct:** 73 (50.0% of non-null)
- **Flags:** INDEXED
- **Range:** min=`Battery - Accessory - N/A` · max=`Strawberry Guava - Trim - HL-17`
- **Length:** min=18 · max=43 · avg=31.78
- **All distinct values (73):** `Battery - Accessory - N/A`, `Berry Fizz - Flower Bulk - HL-24`, `Berry Fizz - Flower Bulk - HL-25`, `Berry Fizz - Flower Bulk - HL-29`, `Berry Fizz - Flower Smalls - HL-24`, `Berry Fizz - Flower Smalls - HL-25`, `Berry Fizz - Trim - HL-24`, `Berry Fizz - Trim - HL-25`, `Berry Fizz - Waste - HL-24`, `Berry Fizz - Waste - HL-25`, `Black Maple - Flower Bulk - HL-18`, `Black Maple - Flower Smalls - HL-18`, `Black Maple - Trim - HL-18`, `Black Maple - Waste - HL-18`, `Candied Oranges - Flower Bulk - HL-29`, `Deathstar - Flower Bulk - HL-15`, `Donkey Butter - Rosin Jar - ML-36`, `Dulce De Uva - Flower Bulk - HL-17`, `Dulce De Uva - Flower Bulk - HL-18`, `Dulce De Uva - Flower Jars - HL-15`, `Dulce De Uva - Flower Smalls - HL-18`, `Dulce De Uva - Trim - HL-17`, `Dulce De Uva - Trim - HL-18`, `Dulce De Uva - Waste - HL-18`, `G13 Skunk - Flower Bulk - HL-25`, `G13 Skunk - Flower Bulk - HL-29`, `G13 Skunk - Flower Smalls - HL-25`, `G13 Skunk - Trim - HL-25`, `G13 Skunk - Waste - HL-25`, `GMO - Flower Bulk - HL-20`, `GMO - Flower Bulk - HL-25`, `GMO - Flower Smalls - HL-25`, `GMO - Rosin Bulk - ML-42`, `GMO - Trim - HL-25`, `GMO - Waste - HL-25`, `Lavender Piff - Flower Bulk - HL-25`, `Lavender Piff - Flower Smalls - HL-25`, `Lavender Piff - Trim - HL-25`, `Lavender Piff - Waste - HL-25`, `Melted Strawberries - Flower Bulk - HL-18`, `Melted Strawberries - Flower Bulk - HL-20`, `Melted Strawberries - Flower Bulk - HL-24`, `Melted Strawberries - Flower Bulk - HL-25`, `Melted Strawberries - Flower Bulk - HL-29`, `Melted Strawberries - Flower Smalls - HL-18`, `Melted Strawberries - Flower Smalls - HL-24`, `Melted Strawberries - Flower Smalls - HL-25`, `Melted Strawberries - Rosin Bulk - ML-41`, `Melted Strawberries - Trim - HL-17`, `Melted Strawberries - Trim - HL-20`, `Melted Strawberries - Trim - HL-24`, `Melted Strawberries - Trim - HL-25`, `Melted Strawberries - Waste - HL-18`, `Melted Strawberries - Waste - HL-24`, `Melted Strawberries - Waste - HL-25`, `Moroccan Peaches - Flower Bulk - HL-17`, `Moroccan Peaches - Trim - HL-17`, `Multipack - Preroll - ML-44`, `Multipack - Preroll - ML-45`, `Multipack - Preroll - ML-46`, `Multipack - Preroll - ML-47`, `Multipack - Preroll - ML-51`, `Papaya Juice - Flower Bulk - HL-18`, `Papaya Juice - Flower Smalls - HL-18`, `Papaya Juice - Waste - HL-18`, `Sherb Cream Pie - Flower Bulk - HL-24`, `Sherb Cream Pie - Flower Smalls - HL-24`, `Sherb Cream Pie - Trim - HL-24`, `Sherb Cream Pie - Waste - HL-24`, `Sour Diesel - Flower Smalls - HL-24T`, `Sour Diesel - Trim - HL-24T`, `Sour Diesel - Waste - HL-24T`, `Strawberry Guava - Trim - HL-17`

### `strain` — text

- **Declared type:** `varchar(255)`
- **Nullable:** True · **Null %:** 0.0%
- **Rows:** 146 · **Distinct:** 17 (11.64% of non-null)
- **Flags:** LOW-CARDINALITY (categorical), INDEXED
- **Range:** min=`Battery` · max=`Strawberry Guava`
- **Length:** min=3 · max=19 · avg=12.37
- **All distinct values (17):** `Battery`, `Berry Fizz`, `Black Maple`, `Candied Oranges`, `Deathstar`, `Donkey Butter`, `Dulce De Uva`, `G13 Skunk`, `GMO`, `Lavender Piff`, `Melted Strawberries`, `Moroccan Peaches`, `Multipack`, `Papaya Juice`, `Sherb Cream Pie`, `Sour Diesel`, `Strawberry Guava`

### `productType` — text

- **Declared type:** `varchar(255)`
- **Nullable:** True · **Null %:** 0.0%
- **Rows:** 146 · **Distinct:** 9 (6.16% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`Accessory` · max=`Waste`
- **Length:** min=4 · max=13 · avg=8.4
- **All distinct values (9):** `Accessory`, `Flower Bulk`, `Flower Jars`, `Flower Smalls`, `Preroll`, `Rosin Bulk`, `Rosin Jar`, `Trim`, `Waste`

### `lotNumber` — text

- **Declared type:** `varchar(100)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 146 · **Distinct:** 17 (11.64% of non-null)
- **Flags:** LOW-CARDINALITY (categorical), INDEXED
- **Range:** min=`HL-15` · max=`N/A`
- **Length:** min=3 · max=6 · avg=5.01
- **All distinct values (17):** `HL-15`, `HL-17`, `HL-18`, `HL-20`, `HL-24`, `HL-24T`, `HL-25`, `HL-29`, `ML-36`, `ML-41`, `ML-42`, `ML-44`, `ML-45`, `ML-46`, `ML-47`, `ML-51`, `N/A`

### `current_qty` — float

- **Declared type:** `double`
- **Nullable:** True · **Null %:** 32.88%
- **Rows:** 146 · **Distinct:** 49 (50.0% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`5.0` · max=`2300.0`
- **Length:** min=1 · max=6 · avg=4.61
- **Pattern hints:** float-as-text
- **All distinct values (49):** `5.0`, `7.0`, `13.0`, `25.5`, `65.2`, `75.7`, `78.2`, `110.4`, `131.7`, `155.1`, `174.5`, `182.5`, `205.6`, `212.2`, `212.9`, `245.1`, `248.7`, `265.6`, `268.4`, `291.7`, `295.8`, `306.0`, `325.7`, `344.9`, `362.2`, `376.0`, `378.9`, `397.9`, `447.0`, `452.8`, `457.4`, `460.9`, `477.2`, `540.8`, `586.2`, `664.9`, `673.6`, `700.0`, `714.1`, `732.4`, `787.7`, `844.9`, `851.5`, `1067.1`, `1221.7`, `1230.6`, `1310.4`, `1570.1`, `2300.0`

### `pending` — float

- **Declared type:** `double`
- **Nullable:** True · **Null %:** 32.88%
- **Rows:** 146 · **Distinct:** 1 (1.02% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`0.0` · max=`0.0`
- **Length:** min=1 · max=1 · avg=1.0
- **Pattern hints:** float-as-text
- **All distinct values (1):** `0.0`

### `remaining` — float

- **Declared type:** `double`
- **Nullable:** True · **Null %:** 32.88%
- **Rows:** 146 · **Distinct:** 49 (50.0% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`5.0` · max=`2300.0`
- **Length:** min=1 · max=6 · avg=4.61
- **Pattern hints:** float-as-text
- **All distinct values (49):** `5.0`, `7.0`, `13.0`, `25.5`, `65.2`, `75.7`, `78.2`, `110.4`, `131.7`, `155.1`, `174.5`, `182.5`, `205.6`, `212.2`, `212.9`, `245.1`, `248.7`, `265.6`, `268.4`, `291.7`, `295.8`, `306.0`, `325.7`, `344.9`, `362.2`, `376.0`, `378.9`, `397.9`, `447.0`, `452.8`, `457.4`, `460.9`, `477.2`, `540.8`, `586.2`, `664.9`, `673.6`, `700.0`, `714.1`, `732.4`, `787.7`, `844.9`, `851.5`, `1067.1`, `1221.7`, `1230.6`, `1310.4`, `1570.1`, `2300.0`

### `lbs` — float

- **Declared type:** `double`
- **Nullable:** True · **Null %:** 83.56%
- **Rows:** 146 · **Distinct:** 12 (50.0% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`0.76` · max=`5.07`
- **Length:** min=1 · max=4 · avg=3.75
- **Pattern hints:** float-as-text
- **All distinct values (12):** `0.76`, `1.0`, `1.29`, `1.46`, `1.48`, `1.61`, `1.86`, `2.35`, `2.69`, `2.71`, `2.89`, `5.07`

### `updatedAt` — datetime

- **Declared type:** `datetime`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 146 · **Distinct:** 20 (13.7% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`2026-06-02 08:28:47` · max=`2026-06-04 11:10:02`
- **Length:** min=19 · max=19 · avg=19.0
- **Pattern hints:** datetime-string
- **All distinct values (20):** `2026-06-02 08:28:47`, `2026-06-02 08:28:48`, `2026-06-02 08:28:49`, `2026-06-02 08:28:50`, `2026-06-02 08:28:51`, `2026-06-02 08:28:52`, `2026-06-02 08:28:53`, `2026-06-02 08:28:54`, `2026-06-02 08:28:55`, `2026-06-02 08:28:56`, `2026-06-02 08:28:57`, `2026-06-02 08:28:58`, `2026-06-02 08:28:59`, `2026-06-02 08:29:00`, `2026-06-02 08:29:01`, `2026-06-02 08:29:02`, `2026-06-02 08:29:03`, `2026-06-02 08:29:04`, `2026-06-02 08:29:05`, `2026-06-04 11:10:02`

### `tenantid` — integer

- **Declared type:** `int`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 146 · **Distinct:** 2 (1.37% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`1` · max=`99`
- **Length:** min=1 · max=2 · avg=1.5
- **Pattern hints:** boolean-token, integer-as-text
- **All distinct values (2):** `1`, `99`

### `brand_id` — text

- **Declared type:** `varchar(36)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 146 · **Distinct:** 2 (1.37% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`ca323241-ef74-425f-aa67-239247ccd0e9` · max=`cmmakqdsn0037qsoig4b4yo9t`
- **Length:** min=25 · max=36 · avg=30.5
- **Pattern hints:** uuid
- **All distinct values (2):** `ca323241-ef74-425f-aa67-239247ccd0e9`, `cmmakqdsn0037qsoig4b4yo9t`

## Sample rows

| id | productname | strain | producttype | lotnumber | current_qty | pending | remaining | lbs | updatedat | tenantid | brand_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0clgn3ickmpwdlu53 | Melted Strawberries - Trim - HL-20 | Melted Strawberries | Trim | HL-20 | 248.7 | 0.0 | 248.7 | — | 2026-06-02 08:28:59 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| 162eaz2z9mpwdlskd | Melted Strawberries - Flower Bulk - HL-24 | Melted Strawberries | Flower Bulk | HL-24 | 268.4 | 0.0 | 268.4 | — | 2026-06-02 08:28:57 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| 1jadje5a4mpwdlopv | Dulce De Uva - Trim - HL-17 | Dulce De Uva | Trim | HL-17 | 376.0 | 0.0 | 376.0 | — | 2026-06-02 08:28:52 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| 1y2fbdbh5mpwdlr7w | GMO - Waste - HL-25 | GMO | Waste | HL-25 | 78.2 | 0.0 | 78.2 | — | 2026-06-02 08:28:56 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| 2xk3pdynympwdloc1 | Dulce De Uva - Flower Jars - HL-15 | Dulce De Uva | Flower Jars | HL-15 | 5.0 | 0.0 | 5.0 | — | 2026-06-02 08:28:52 | 1 | cmmakqdsn0037qsoig4b4yo9t |

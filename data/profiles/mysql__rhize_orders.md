# `rhize_orders` (mysql)

- **Schema:** —
- **Rows:** 3,457
- **Columns:** 21
- **Primary key:** `id`
- **Indexes:** `idx_customer_name`(N: customerName), `idx_date`(N: date), `idx_nat_key`(N: orderNumber,productName,productType,variant,lotNumber), `idx_orderNumber`(N: orderNumber), `idx_status`(N: status), `idx_status_date`(N: status,date), `idx_status_delivery`(N: status,deliveryDate), `idx_storeId`(N: storeId), `PRIMARY`(U: id), `uq_uid_tenant`(U: uid,tenantid)

## Columns

### `id` — text

- **Declared type:** `varchar(36)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 3,457 · **Distinct:** 3,457 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, PRIMARY-KEY
- **Range:** min=`00a1b73g6mpwfgvia` · max=`zzyle46ulmpwfgvib`
- **Length:** min=17 · max=23 · avg=17.35
- **All distinct values (3457):** `00a1b73g6mpwfgvia`, `00fskq9xempwfgt8w`, `00nzpg4eumpwfgtns`, `01m6cx417mpwfgto8`, `01t449nvtmpwfgvia`, `01uilxf5jmpwfgt91`, `023brq87zmpwfgvib`, `024n78z9ompwfgtoa`, `02mx6qtvjmpwfgtnx`, `03vaqdcn7mpwfgu33`, `04nfubkjjmpwfgu31`, `05ipgtv2dmpwfgtvi`, `05j6uky6vmpwfgu2z`, `06df394d7mpwfgtvk`, `06u7c3nmlmpwfgxi1`, `074slt3pbmpwfgtnz`, `07a7tpmbimpwfgto1`, `07bvjwgjkmpwfgvi8`, `07d5xgbmympwfgt8x`, `07wit8ee3mpwfgto3`, `08hvvuqmcmpwfgtvj`, `0bl5q7kt2mpwfgto3`, `0c2tbopu4mpwfgtnt`, `0c6eetkdvmpwfgto4`, `0c7wwb359mpwfgtvg`, `0ddx3bodsmpwfgx3q`, `0e9tntsitmpwfgtnz`, `0eah0mdp1mpwfgto1`, `0erme8lfpmpwfgto9`, `0f7hdzhr7mpwfgtnw`, `0fac01dy6mpwfgvi7`, `0fcmamo0lmpwfgto4`, `0frsjseo4mpwfgu2z`, `0ft35czx2mpwfgto7`, `0gbcxtn31mpwfgx3q`, `0gwnyhoo6mpwfgvia`, `0hiu6h1j4mpwfgu2y`, `0hrcuyaxkmpwfgv38`, `0i5rh3ju2mpwfgto6`, `0id6fgv9ampwfgu30`, `0jbvxgx0rmpwfgtnw`, `0jfc1aetrmpwfgto1`, `0jt13fe93mpwfgtnr`, `0k20ax78bmpwfgt91`, `0k29bzhnimpwfgtnr`, `0kn5g8jc2mpwfgtvm`, `0lwrnygytmpwfgvi9`, `0ma6nvxaympwfgxi2`, `0mqe0q8glmpwfgto0`, `0n7u79dq3mpwfgu31`, `0nk6inr6gmpwfgto9`, `0nt083hzxmpwfgu2y`, `0o71pmuapmpwfgtoa`, `0ormfzme1mpwfgvi7`, `0out6px7qmpwfgtnu`, `0ov4g26pempwfgtnx`, `0p87aht8jmpwfgv38`, `0pwsxk7nxmpwfgxi2`, `0pzbq6h6ympwfgu2y`, `0qc3m23x9mpwfgtvm`, `0qwotk0y8mpwfgt8w`, `0r8glzgkumpwfgtvi`, `0r8hszi5pmpwfgu32`, `0ru0ugl33mpwfgu2z`, `0snturl0fmpwfgtnr`, `0srxk3qbxmpwfgto8`, `0tusxwciqmpwfgto9`, `0u01e8x6impwfgtvi`, `0udh9qaalmpwfgu2x`, `0ui6g65p1mpwfgu2w`, `0utec4uismpwfgtnz`, `0vdtloswpmpwfgu2x`, `0vii69wammpwfgtnt`, `0wnu4mtn4mpwfgtnw`, `0wx91wvtcmpwfgto8`, `0wxlh2ixsmpwfgt8z`, `0wyrcp8tompwfgtnz`, `0x6d4uskqmpwfgto0`, `0xofiwsrtmpwfgto5`, `0xz9bpmtlmpwfgu31`, `0y0ahrn6ampwfgtnv`, `0ygb3g9wkmpwfgt8y`, `0zcuqfydlmpwfgtvi`, `0zheq6bizmpwfgu2z`, `0zhz59todmpwfgu32`, `0zzf5ggnsmpwfgto2`, `11dh6oasxmpwfgtnu`, `11ytrguczmpwfgto0`, `121z5ee9ompwfgtvn`, `12h6hp9vmmpwfgxi1`, `12hmyudkqmpwfgu32`, `133nqz6xhmpwfgtvh`, `137x9prmimpwfgv38`, `13biwomxjmpwfgto9`, `13sn2nkk5mpwfgu2y`, `146uv90ckmpwfgtny`, `14royt1gpmpwfgtns`, `14vy5gx8gmpwfgu31`, `157h2jnlxmpwfgu2z`, `15j7rmfrqmpwfgto4`, `15k9tw4wdmpwfgu33`, `15lcqprvpmpwfgu2y`, `168tw60kmmpxrp0ml`, `16e1py43wmpwfgt8t`, `16i7ekr3pmpwfgtns`, `17ax58w76mpwfgtnu`, `17glmolssmpwfgtns`, `17qsee27mmpwfgto1`, `17uvuu5pjmpwfgvi8`, `17xwz06eqmpwfgto5`, `18eq7vulvmpwfgtvi`, `19dt78hj8mpwfgtvi`, `19emlemv2mpwfgto4`, `1a5une0q0mpwfgu32`, `1anf2s3tzmpwfgt8u`, `1apefpsvgmpwfgto1`, `1ayjvtjw4mpwfgu31`, `1bpx3cu0ympwfgtnu`, `1bqah0c9ampwfgto8`, `1c8sxbc78mpwfgt8v`, `1cnwz3x32mpwfgtnz`, `1d0lizv6qmpwfgu32`, `1du354llwmpwfgu2y`, `1dvafxm8fmpwfgtvm`, `1dymc1k5bmpwfgvi9`, `1e3b7il3ympwfgv37`, `1e7qh2st0mpwfgto9`, `1ebpybzyrmpwfgtnv`, `1efb2sj33mpwfgto5`, `1f0h18dpympwfgto7`, `1fj6xwfwempwfgtvk`, `1fq7ryxkumpwfgtnt`, `1fr5pzrs3mpwfgtvj`, `1gkqpexnxmpwfgtvl`, `1gp5mgavdmpwfgu2y`, `1h0qqdh83mpwfgtnt`, `1hchabfx7mpwfgu34`, `1iqg9z0g4mpwfgtvm`, `1iud0bnivmpwfgvi9`, `1j092cx3ympwfgtnr`, `1jcj4al3mmpwfgtvi`, `1l11w4pwhmpwfgtny`, `1l1egmy7fmpwfgtny`, `1l8wfkscmmpwfgu32`, `1lhm21zapmpwfgvi9`, `1lkpzqyjdmpwfgu2y`, `1lli1dd06mpwfgtns`, `1mecs61ivmpwfgtvi`, `1mo033tuzmpwfgv38`, `1mxs20tbympwfgtvk`, `1n5svskuompwfgu33`, `1njxoyidjmpwfgtnt`, `1nk42d060mpwfgtnu`, `1p7tip8nimpwfgv38`, `1pffzclq9mpwfgu2z`, `1porbvd3fmpwfgto4`, `1qeq67f4kmpwfgx3r`, `1qqfpznuhmpwfgto5`, `1qxr8oyw3mpwfgvia`, `1rh1nedb2mpwfgtvi`, `1sajfpi5hmpwfgvi9`, `1slykb4ximpwfgu2y`, `1u16gk8wrmpwfgu2y`, `1u77hnxaampwfgu31`, `1v5os3j77mpwfgto9`, `1vynnhx7nmpwfgtvj`, `1whbuoxaympwfgtnu`, `1wn2peab1mpwfgtnw`, `1x6cy3v0xmpwfgtvi`, `1xe5y7cnzmpwfgx3r`, `1xqtrnah1mpwfgto8`, `1xrpxljj3mpwfgto4`, `1xytnisjzmpwfgu2y`, `1y71pbu86mpwfgto4`, `1y7hpumg6mpwfgvi9`, `1yentw87jmpwfgtvj`, `1z0ex983nmpwfgtnx`, `1z9p1blxhmpwfgtnz`, `1zry2xi2jmpwfgt8w`, `1zxfkkz9xmpwfgtnz`, `201jbgem6mpwfgv37`, `20bb7x7q4mpwfgu32`, `21gy28h6umpwfgu33`, `22zn83pspmpwfgto7`, `23jf6vmr4mpwfgtnw`, `23ntb1uxsmpwfgtnr`, `24mugjtymmpwfgt8x`, `24qn7tknpmpwfgto5`, `24ss8x5u6mpwfgt8z`, `253p0nit2mpwfgt8z`, `254kyrq19mpwfgvi7`, `25kqpr179mpwfgto3`, `25ms3tey5mpwfgt8z`, `25ymzwxhampwfgx3q`, `26q1k7xsumpwfgtvm`, `26qmcbumempwfgxi1`, `2712jxffbmpwfgvi9`, `271k5r4wzmpwfgto1`, `27ts90qanmpwfgtvl`, `27vjimao3mpwfgtnx` _(+3257 more)_

### `date` — datetime

- **Declared type:** `datetime`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 3,457 · **Distinct:** 261 (7.55% of non-null)
- **Flags:** INDEXED
- **Range:** min=`2024-01-03 00:00:00` · max=`2026-06-02 00:00:00`
- **Length:** min=19 · max=19 · avg=19.0
- **Pattern hints:** datetime-string
- **All distinct values (261):** `2024-01-03 00:00:00`, `2024-01-08 00:00:00`, `2024-01-14 00:00:00`, `2024-01-18 00:00:00`, `2024-01-26 00:00:00`, `2024-02-02 00:00:00`, `2024-02-07 00:00:00`, `2024-02-08 00:00:00`, `2024-02-09 00:00:00`, `2024-02-14 00:00:00`, `2024-02-20 00:00:00`, `2024-02-21 00:00:00`, `2024-02-22 00:00:00`, `2024-02-26 00:00:00`, `2024-02-27 00:00:00`, `2024-02-29 00:00:00`, `2024-03-04 00:00:00`, `2024-03-06 00:00:00`, `2024-03-09 00:00:00`, `2024-03-13 00:00:00`, `2024-03-20 00:00:00`, `2024-03-21 00:00:00`, `2024-03-27 00:00:00`, `2024-03-28 00:00:00`, `2024-04-01 00:00:00`, `2024-04-10 00:00:00`, `2024-04-18 00:00:00`, `2024-04-19 00:00:00`, `2024-05-02 00:00:00`, `2024-05-03 00:00:00`, `2024-05-06 00:00:00`, `2024-05-09 00:00:00`, `2024-05-10 00:00:00`, `2024-05-16 00:00:00`, `2024-05-17 00:00:00`, `2024-05-23 00:00:00`, `2024-05-28 00:00:00`, `2024-05-31 00:00:00`, `2024-06-05 00:00:00`, `2024-06-06 00:00:00`, `2024-06-13 00:00:00`, `2024-06-18 00:00:00`, `2024-06-19 00:00:00`, `2024-06-21 00:00:00`, `2024-06-28 00:00:00`, `2024-07-02 00:00:00`, `2024-07-04 00:00:00`, `2024-07-05 00:00:00`, `2024-07-11 00:00:00`, `2024-07-19 00:00:00`, `2024-07-24 00:00:00`, `2024-07-25 00:00:00`, `2024-07-26 00:00:00`, `2024-07-30 00:00:00`, `2024-08-02 00:00:00`, `2024-08-03 00:00:00`, `2024-08-04 00:00:00`, `2024-08-06 00:00:00`, `2024-08-08 00:00:00`, `2024-08-09 00:00:00`, `2024-08-13 00:00:00`, `2024-08-16 00:00:00`, `2024-08-21 00:00:00`, `2024-08-22 00:00:00`, `2024-08-23 00:00:00`, `2024-08-24 00:00:00`, `2024-08-28 00:00:00`, `2024-08-29 00:00:00`, `2024-08-30 00:00:00`, `2024-09-03 00:00:00`, `2024-09-05 00:00:00`, `2024-09-07 00:00:00`, `2024-09-10 00:00:00`, `2024-09-12 00:00:00`, `2024-09-13 00:00:00`, `2024-09-19 00:00:00`, `2024-09-26 00:00:00`, `2024-09-27 00:00:00`, `2024-10-03 00:00:00`, `2024-10-11 00:00:00`, `2024-10-17 00:00:00`, `2024-10-18 00:00:00`, `2024-10-21 00:00:00`, `2024-10-22 00:00:00`, `2024-10-30 00:00:00`, `2024-11-01 00:00:00`, `2024-11-06 00:00:00`, `2024-11-07 00:00:00`, `2024-11-08 00:00:00`, `2024-11-14 00:00:00`, `2024-11-15 00:00:00`, `2024-11-21 00:00:00`, `2024-11-22 00:00:00`, `2024-11-26 00:00:00`, `2024-12-05 00:00:00`, `2024-12-06 00:00:00`, `2024-12-11 00:00:00`, `2024-12-13 00:00:00`, `2024-12-17 00:00:00`, `2024-12-18 00:00:00`, `2024-12-19 00:00:00`, `2024-12-27 00:00:00`, `2025-01-02 00:00:00`, `2025-01-03 00:00:00`, `2025-01-09 00:00:00`, `2025-01-15 00:00:00`, `2025-01-16 00:00:00`, `2025-01-17 00:00:00`, `2025-01-20 00:00:00`, `2025-01-22 00:00:00`, `2025-01-29 00:00:00`, `2025-02-02 00:00:00`, `2025-02-03 00:00:00`, `2025-02-10 00:00:00`, `2025-02-12 00:00:00`, `2025-02-17 00:00:00`, `2025-02-24 00:00:00`, `2025-03-03 00:00:00`, `2025-03-04 00:00:00`, `2025-03-10 00:00:00`, `2025-03-11 00:00:00`, `2025-03-17 00:00:00`, `2025-03-19 00:00:00`, `2025-03-24 00:00:00`, `2025-03-26 00:00:00`, `2025-03-31 00:00:00`, `2025-04-01 00:00:00`, `2025-04-07 00:00:00`, `2025-04-08 00:00:00`, `2025-04-10 00:00:00`, `2025-04-14 00:00:00`, `2025-04-18 00:00:00`, `2025-04-21 00:00:00`, `2025-04-22 00:00:00`, `2025-04-23 00:00:00`, `2025-04-28 00:00:00`, `2025-05-01 00:00:00`, `2025-05-05 00:00:00`, `2025-05-06 00:00:00`, `2025-05-12 00:00:00`, `2025-05-19 00:00:00`, `2025-05-21 00:00:00`, `2025-05-26 00:00:00`, `2025-05-27 00:00:00`, `2025-05-28 00:00:00`, `2025-06-02 00:00:00`, `2025-06-03 00:00:00`, `2025-06-09 00:00:00`, `2025-06-10 00:00:00`, `2025-06-16 00:00:00`, `2025-06-23 00:00:00`, `2025-06-24 00:00:00`, `2025-06-30 00:00:00`, `2025-07-06 00:00:00`, `2025-07-14 00:00:00`, `2025-07-20 00:00:00`, `2025-07-21 00:00:00`, `2025-07-22 00:00:00`, `2025-07-28 00:00:00`, `2025-08-04 00:00:00`, `2025-08-11 00:00:00`, `2025-08-18 00:00:00`, `2025-08-19 00:00:00`, `2025-08-20 00:00:00`, `2025-08-25 00:00:00`, `2025-08-26 00:00:00`, `2025-08-27 00:00:00`, `2025-09-02 00:00:00`, `2025-09-03 00:00:00`, `2025-09-08 00:00:00`, `2025-09-10 00:00:00`, `2025-09-15 00:00:00`, `2025-09-18 00:00:00`, `2025-09-22 00:00:00`, `2025-09-23 00:00:00`, `2025-09-29 00:00:00`, `2025-10-05 00:00:00`, `2025-10-06 00:00:00`, `2025-10-07 00:00:00`, `2025-10-14 00:00:00`, `2025-10-21 00:00:00`, `2025-10-22 00:00:00`, `2025-10-23 00:00:00`, `2025-10-27 00:00:00`, `2025-10-28 00:00:00`, `2025-11-02 00:00:00`, `2025-11-03 00:00:00`, `2025-11-04 00:00:00`, `2025-11-09 00:00:00`, `2025-11-10 00:00:00`, `2025-11-17 00:00:00`, `2025-11-19 00:00:00`, `2025-11-24 00:00:00`, `2025-11-25 00:00:00`, `2025-11-30 00:00:00`, `2025-12-01 00:00:00`, `2025-12-08 00:00:00`, `2025-12-09 00:00:00`, `2025-12-11 00:00:00`, `2025-12-15 00:00:00` _(+61 more)_

### `orderNumber` — integer

- **Declared type:** `int`
- **Nullable:** True · **Null %:** 0.0%
- **Rows:** 3,457 · **Distinct:** 889 (25.72% of non-null)
- **Flags:** INDEXED
- **Range:** min=`0` · max=`10199`
- **Length:** min=1 · max=5 · avg=3.02
- **Pattern hints:** integer-as-text
- **All distinct values (889):** `0`, `7`, `8`, `9`, `10`, `11`, `12`, `14`, `15`, `16`, `17`, `18`, `19`, `20`, `21`, `22`, `23`, `24`, `25`, `27`, `28`, `29`, `30`, `31`, `32`, `33`, `34`, `35`, `36`, `37`, `38`, `39`, `40`, `41`, `42`, `43`, `44`, `45`, `46`, `47`, `49`, `50`, `52`, `53`, `54`, `55`, `56`, `57`, `58`, `59`, `60`, `61`, `62`, `64`, `66`, `67`, `68`, `69`, `70`, `71`, `72`, `73`, `74`, `75`, `76`, `78`, `79`, `80`, `81`, `82`, `86`, `87`, `88`, `89`, `90`, `91`, `92`, `93`, `94`, `95`, `96`, `97`, `98`, `99`, `100`, `101`, `102`, `103`, `104`, `105`, `106`, `107`, `108`, `109`, `110`, `111`, `112`, `113`, `114`, `116`, `117`, `118`, `119`, `120`, `121`, `122`, `123`, `124`, `125`, `126`, `127`, `128`, `129`, `130`, `131`, `132`, `133`, `134`, `135`, `136`, `137`, `138`, `139`, `140`, `141`, `142`, `143`, `144`, `145`, `146`, `147`, `148`, `149`, `150`, `151`, `152`, `153`, `154`, `155`, `156`, `157`, `158`, `159`, `160`, `161`, `162`, `163`, `164`, `165`, `166`, `167`, `168`, `169`, `170`, `171`, `172`, `173`, `174`, `175`, `176`, `177`, `178`, `179`, `180`, `181`, `182`, `183`, `184`, `185`, `186`, `187`, `188`, `189`, `190`, `191`, `192`, `193`, `194`, `195`, `196`, `197`, `198`, `199`, `200`, `201`, `202`, `203`, `204`, `205`, `206`, `207`, `208`, `209`, `210`, `211`, `212`, `213`, `214`, `215`, `216` _(+689 more)_

### `storeId` — text

- **Declared type:** `varchar(36)`
- **Nullable:** True · **Null %:** 100.0%
- **Rows:** 3,457 · **Distinct:** 0 (0.0% of non-null)
- **Flags:** INDEXED

### `customerName` — text

- **Declared type:** `varchar(255)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 3,457 · **Distinct:** 60 (1.74% of non-null)
- **Flags:** INDEXED
- **Range:** min=`31 North` · max=`Valley Meade`
- **Length:** min=4 · max=38 · avg=11.4
- **All distinct values (60):** `31 North`, `Bern Legacy Cannabis`, `Big Intelligence Group dba/Wild Legacy`, `Bud Stop`, `Cambridge`, `Capital Cannabis Company`, `Cloud 9`, `Craftsbury Cannabis, LLC`, `Demo Customer 01`, `Demo Customer 02`, `Demo Customer 04`, `Demo Customer 06`, `Demo Customer 08`, `Demo Customer 10`, `Demo Customer 11`, `Demo Customer 12`, `Demo Customer 13`, `Demo Customer 14`, `Demo Customer 15`, `Demo Customer 16`, `Demo Customer 17`, `Demo Customer 18`, `Demo Customer 19`, `Demo Customer 20`, `Demo Customer 21`, `Demo Customer 22`, `Demo Customer 23`, `Demo Customer 24`, `Demo Customer 25`, `Dome City`, `Down to the Roots`, `FLORA`, `Forbin's Reserve`, `Forbin’s Reserve`, `Freedom Flower, LLC`, `Garcia's`, `Garcia’s`, `Gaston Weed Company`, `GMCW`, `Gram Central`, `Higher Elevation`, `Kushies`, `Magic Mann`, `Milton Remedies`, `MothaPlant`, `Mountain Girl`, `Pine Grove Organics`, `Polestar`, `Poultney Cannabis Supply`, `Ratu's Cannabis Supply, LLC`, `Rimeline`, `Rolling Twenties`, `Something Wicked Cannabis Company`, `Somewhere On The Mountain`, `Sunday Drive`, `Sweetspot`, `Tea House`, `The Bud Stop`, `The Gas Station`, `Valley Meade`

### `productName` — text

- **Declared type:** `varchar(500)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 3,457 · **Distinct:** 59 (1.71% of non-null)
- **Range:** min=`1g GMO Live Rosin` · max=`Tropical Summer`
- **Length:** min=3 · max=32 · avg=12.38
- **All distinct values (59):** `1g GMO Live Rosin`, `3g GMO Live Rosin`, `87 Lem OG`, `Animal Face`, `Animal Face Live Rosin`, `Battery`, `Berry Fizz`, `Black Maple`, `Blackout Truffle`, `Blackout Truffle 1/2 lb`, `Bop Gun`, `Bop Gun (Promotion)`, `Bop Gun Live Rosin`, `Candied Oranges`, `Deathstar`, `Donkey Butter`, `Donkey Butter 1/2 lb`, `Donkey Butter Live Rosin`, `Dulce De Uva`, `Eastside OG`, `Eastside OG Cart`, `Eastside OG Carts`, `Eastside OG Live Rosin`, `Forbidden Fruit`, `Forbidden Fruit 1/4 lb`, `G13 Skunk`, `GMO`, `GMO Cart`, `GMO Carts`, `GMO Flower`, `GMO Live Rosin`, `Grape Pie`, `Grape Pie 1/2 lb`, `Grape Pie Bulk Flower (g)`, `Honey Banana`, `Humble Skunk Hash Rosin`, `Ice Cream Cake`, `Lavender Piff`, `Mellowz`, `Melted Strawberries`, `Moroccan Peaches`, `Mountian Girl Live Rosin Gummies`, `Multipack`, `Multipacks`, `P-06 - Humble Skunk Gummies`, `Papaya Juice`, `Raspberry Gummies`, `Raspberry Hash Rosin`, `Rhize Multipack`, `Rhize Tropical Multipack`, `Rhize Universal Cart Battery`, `Rosin Cart Battery`, `Sherb Cream Pie`, `Sour Diesel`, `Strawberry Guava`, `Strawberry Pie`, `Tahiti Lime`, `The Hive`, `Tropical Summer`

### `productType` — text

- **Declared type:** `varchar(255)`
- **Nullable:** True · **Null %:** 0.52%
- **Rows:** 3,457 · **Distinct:** 37 (1.08% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`Accessory` · max=`Tropical Summer 7x 0.5g Pre Rolls`
- **Length:** min=4 · max=33 · avg=9.36
- **All distinct values (37):** `Accessory`, `Cart`, `Dog Walker Packs 2x 1/2g`, `Edibles`, `Edibles Jar`, `Flower Bulk`, `Flower Jar`, `Flower Jars`, `GMO Live Rosin P-06205`, `Gummies`, `Humble Skunk Hash Rosin`, `Multipack`, `Multipack 7x 0.5g Pre Rolls`, `Mutipack`, `Package Rhize Rosin 1g`, `Packaged Flower`, `Packaged Flower 3.55g Each`, `Packaged Pre Roll 1.05g Each`, `Packaged Pre Roll 1g`, `Packaged Pre Rolls 1g`, `Packaged Rhize Flower 3.5g`, `Packaged Rhize Rosin 1g`, `Packaged Rhize Rosin 3g`, `Packaged Rosin 1g Each`, `Preroll`, `Rhize Bulk Flower`, `Rhize Pre Rolls`, `Rhize Rosin 1g`, `Rhize Rosin Edibles`, `Rhize Rosin Gummies`, `Rhize Rosin Gummies 100 mg`, `Rhize Rosin Gummies 20 ct`, `Rhize Rosin Jars`, `Rosin 1g Jar`, `Rosin Jar`, `Trim`, `Tropical Summer 7x 0.5g Pre Rolls`

### `qty` — float

- **Declared type:** `double`
- **Nullable:** True · **Null %:** 0.0%
- **Rows:** 3,457 · **Distinct:** 116 (3.36% of non-null)
- **Range:** min=`0.0` · max=`1275.0`
- **Length:** min=1 · max=5 · avg=1.96
- **Pattern hints:** float-as-text
- **All distinct values (116):** `0.0`, `0.62`, `0.79`, `1.0`, `1.07`, `1.43`, `1.61`, `2.0`, `2.31`, `3.0`, `4.0`, `5.0`, `6.0`, `7.0`, `8.0`, `9.0`, `10.0`, `11.0`, `12.0`, `13.0`, `14.0`, `15.0`, `16.0`, `17.0`, `18.0`, `20.0`, `21.0`, `22.0`, `23.0`, `24.0`, `25.0`, `26.0`, `27.0`, `28.0`, `29.0`, `30.0`, `32.0`, `35.0`, `38.0`, `40.0`, `42.0`, `43.0`, `44.0`, `45.0`, `46.0`, `48.0`, `49.0`, `50.0`, `55.0`, `56.0`, `60.0`, `62.0`, `64.0`, `68.0`, `70.0`, `72.0`, `75.0`, `79.0`, `80.0`, `82.0`, `85.0`, `90.0`, `91.0`, `96.0`, `99.0`, `100.0`, `102.0`, `112.0`, `115.0`, `120.0`, `123.0`, `128.0`, `139.0`, `140.0`, `150.0`, `165.0`, `182.0`, `185.0`, `187.0`, `195.0`, `198.0`, `200.0`, `206.0`, `219.4`, `220.0`, `222.0`, `227.0`, `230.0`, `250.0`, `261.0`, `286.0`, `320.0`, `325.0`, `328.0`, `340.0`, `348.0`, `370.0`, `405.0`, `430.0`, `456.0`, `460.0`, `472.0`, `480.0`, `483.0`, `484.0`, `499.0`, `510.0`, `521.0`, `591.0`, `595.0`, `610.0`, `724.0`, `743.0`, `844.0`, `865.0`, `1275.0`

### `variant` — text

- **Declared type:** `varchar(100)`
- **Nullable:** True · **Null %:** 9.86%
- **Rows:** 3,457 · **Distinct:** 8 (0.26% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`0.5g` · max=`Gummies`
- **Length:** min=2 · max=10 · avg=3.59
- **All distinct values (8):** `0.5g`, `1g`, `2g`, `3.5`, `3.5g`, `3g`, `grams bulk`, `Gummies`

### `lotNumber` — text

- **Declared type:** `varchar(100)`
- **Nullable:** True · **Null %:** 28.38%
- **Rows:** 3,457 · **Distinct:** 129 (5.21% of non-null)
- **Range:** min=`HL-10` · max=`N/A`
- **Length:** min=3 · max=16 · avg=5.17
- **All distinct values (129):** `HL-10`, `HL-11`, `HL-12`, `HL-14`, `HL-15`, `HL-16`, `HL-17`, `HL-18`, `HL-19`, `HL-20`, `HL-21`, `HL-22`, `HL-22T`, `HL-23`, `HL-23T`, `HL-24`, `HL-24T`, `HL-25`, `HL-26`, `HL-26B`, `HL-27`, `HL-28`, `HL-29`, `HL-30`, `HL-5`, `HL-SCLT0295-24-2`, `ML-100`, `ML-101`, `ML-102`, `ML-103`, `ML-104`, `ML-105`, `ML-107`, `ML-109`, `ML-110`, `ML-111`, `ML-112`, `ML-113`, `ML-115`, `ML-117`, `ML-118`, `ML-119`, `ML-121`, `ML-122`, `ML-124`, `ML-125`, `ML-126`, `ML-127`, `ML-128`, `ML-129`, `ML-131`, `ML-132`, `ML-133`, `ML-135`, `ML-138`, `ML-139`, `ML-140`, `ML-141`, `ML-142`, `ML-143`, `ML-144`, `ML-145`, `ML-20`, `ML-23`, `ML-26`, `ML-28`, `ML-29`, `ML-31`, `ML-32`, `ML-34`, `ML-36`, `ML-37`, `ML-38`, `ML-39`, `ML-40`, `ML-41`, `ML-42`, `ML-43`, `ML-44`, `ML-45`, `ML-46`, `ML-47`, `ML-48`, `ML-49`, `ML-50`, `ML-51`, `ML-52`, `ML-53`, `ML-54`, `ML-57`, `ML-59`, `ML-60`, `ML-61`, `ML-62`, `ML-63`, `ML-64`, `ML-65`, `ML-66`, `ML-67`, `ML-69`, `ML-70`, `ML-71`, `ML-72`, `ML-73`, `ML-74`, `ML-75`, `ML-76`, `ML-77`, `ML-78`, `ML-79`, `ML-80`, `ML-81`, `ML-82`, `ML-86`, `ML-87`, `ML-88`, `ML-89`, `ML-90`, `ML-91`, `ML-92`, `ML-93`, `ML-94`, `ML-95`, `ML-96`, `ML-97`, `ML-98`, `ML-99`, `ML140`, `N/A`

### `unitPrice` — float

- **Declared type:** `double`
- **Nullable:** True · **Null %:** 0.17%
- **Rows:** 3,457 · **Distinct:** 186 (5.39% of non-null)
- **Range:** min=`0.0` · max=`1500.0`
- **Length:** min=1 · max=18 · avg=2.33
- **Pattern hints:** float-as-text
- **All distinct values (186):** `0.0`, `0.5`, `0.53`, `0.87`, `0.88`, `0.881`, `0.8810572687224669`, `1.0`, `1.59`, `2.0`, `2.5`, `3.0`, `3.33`, `3.73`, `3.84`, `4.0`, `4.45`, `4.5`, `4.85`, `4.9`, `5.0`, `5.217391304`, `5.26`, `5.405405405`, `5.43`, `5.44`, `5.5`, `5.6`, `5.65`, `5.65217`, `5.65218`, `5.7`, `5.73`, `5.79`, `5.869565217391305`, `5.87`, `5.9`, `5.947136563876652`, `5.95`, `5.99`, `6.0`, `6.08`, `6.085`, `6.086953`, `6.086956521739131`, `6.086956522`, `6.087`, `6.09`, `6.1`, `6.13`, `6.16`, `6.17`, `6.260869565`, `6.3`, `6.304347826`, `6.304347826086956`, `6.3044`, `6.305`, `6.31`, `6.4`, `6.5`, `6.51`, `6.52`, `6.5217`, `6.52173`, `6.521732`, `6.52173913`, `6.521739130434782`, `6.52175`, `6.525`, `6.52566`, `6.53`, `6.54`, `6.55`, `6.61`, `6.62`, `6.65`, `6.6667`, `6.67`, `6.87`, `6.9`, `6.94`, `6.9565`, `6.95652`, `6.956521739`, `6.956521739130435`, `6.96`, `6.97`, `7.0`, `7.01`, `7.25`, `7.39`, `7.47`, `7.5`, `7.51`, `7.52`, `7.6`, `7.96`, `8.0`, `9.0`, `15.0`, `15.625`, `15.75`, `16.0`, `16.55`, `17.0`, `17.5`, `17.52`, `17.85`, `18.0`, `18.7`, `18.75`, `19.0`, `19.08`, `19.55`, `20.0`, `20.27`, `20.49`, `20.7`, `21.0`, `21.47`, `21.6`, `22.0`, `22.5`, `22.52`, `23.0`, `23.34`, `23.55`, `23.59`, `23.69`, `23.89`, `24.0`, `24.53`, `24.57`, `24.88`, `25.0`, `25.34`, `26.0`, `27.0`, `27.03`, `27.2`, `28.0`, `28.9`, `29.0`, `29.43`, `29.57`, `29.75`, `30.0`, `31.0`, `31.39`, `31.4`, `32.0`, `32.68`, `33.0`, `34.0`, `35.0`, `40.0`, `44.0`, `48.0`, `50.0`, `53.0`, `54.0`, `55.0`, `56.0`, `70.0`, `71.0`, `75.0`, `76.0`, `77.0`, `77.5`, `90.0`, `100.0`, `225.0`, `400.0`, `436.0`, `500.0`, `528.0`, `650.0`, `700.0`, `721.64`, `725.0`, `750.0`, `800.0`, `1300.0`, `1400.0`, `1500.0`

### `subtotal` — float

- **Declared type:** `double`
- **Nullable:** True · **Null %:** 0.06%
- **Rows:** 3,457 · **Distinct:** 391 (11.32% of non-null)
- **Range:** min=`0.0` · max=`3201.6`
- **Length:** min=1 · max=18 · avg=3.4
- **Pattern hints:** float-as-text
- **All distinct values (391):** `0.0`, `5.0`, `9.0`, `10.0`, `14.0`, `20.0`, `30.0`, `32.5`, `35.0`, `36.0`, `40.0`, `45.0`, `50.0`, `60.0`, `61.31`, `64.0`, `65.0`, `65.35`, `67.5`, `68.0`, `69.68`, `70.0`, `72.0`, `72.5`, `74.69`, `75.0`, `78.0`, `79.63`, `80.0`, `82.5`, `84.0`, `90.0`, `96.0`, `100.0`, `105.0`, `105.11`, `110.0`, `110.5`, `112.5`, `114.0`, `115.23`, `116.0`, `120.0`, `123.35`, `125.0`, `125.58`, `128.0`, `130.0`, `133.0`, `135.0`, `137.35`, `137.5`, `138.0`, `140.0`, `142.5`, `144.0`, `145.0`, `150.0`, `150.04`, `152.0`, `155.0`, `157.5`, `160.0`, `160.35`, `161.0`, `162.0`, `162.5`, `165.0`, `168.0`, `170.0`, `171.0`, `174.45`, `175.0`, `176.0`, `177.0`, `180.0`, `181.25`, `185.0`, `187.5`, `188.0`, `189.0`, `190.0`, `192.0`, `195.0`, `198.0`, `200.0`, `204.86`, `204.87`, `210.0`, `216.0`, `217.5`, `220.0`, `220.26431718061673`, `224.0`, `225.0`, `228.0`, `229.95594713656388`, `230.0`, `231.0`, `236.0`, `238.89`, `240.0`, `245.0`, `248.0`, `248.84`, `250.0`, `251.98237885462555`, `252.0`, `253.42`, `256.0`, `260.0`, `264.0`, `270.0`, `270.31`, `273.0`, `275.0`, `276.0`, `280.0`, `281.9383259911894`, `286.34`, `288.0`, `288.968`, `288.99`, `289.65`, `289.66`, `290.0`, `294.0`, `294.32`, `295.65`, `300.0`, `301.0`, `304.0`, `306.6079295154185`, `308.0`, `310.0`, `312.0`, `313.94`, `315.0`, `316.0`, `320.0`, `322.0`, `325.0`, `325.99`, `326.75`, `326.76`, `330.0`, `331.02`, `331.03`, `336.0`, `337.5`, `338.0`, `340.0`, `343.0`, `345.0`, `350.0`, `350.36`, `352.0`, `353.18`, `353.87`, `356.805`, `360.0`, `362.5`, `367.9`, `368.0`, `368.61`, `372.0`, `373.44`, `375.0`, `378.0`, `378.85`, `380.0`, `384.0`, `385.0`, `390.0`, `391.0`, `392.0`, `400.0`, `401.736`, `405.0`, `408.0`, `414.0`, `415.86`, `420.0`, `420.21`, `422.90748898678413`, `426.404`, `428.0`, `429.45`, `432.0`, `436.0`, `438.0`, `439.619`, `440.0`, `443.7`, `448.0`, `449.33920704845815`, `450.0`, `459.001`, `460.0`, `466.8` _(+191 more)_

### `status` — text

- **Declared type:** `varchar(50)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 3,457 · **Distinct:** 2 (0.06% of non-null)
- **Flags:** LOW-CARDINALITY (categorical), INDEXED
- **Range:** min=`Completed` · max=`Pending`
- **Length:** min=7 · max=9 · avg=8.96
- **All distinct values (2):** `Completed`, `Pending`

### `deliveryDate` — datetime

- **Declared type:** `datetime`
- **Nullable:** True · **Null %:** 0.09%
- **Rows:** 3,457 · **Distinct:** 231 (6.69% of non-null)
- **Range:** min=`2015-04-18 00:00:00` · max=`2026-06-05 00:00:00`
- **Length:** min=19 · max=19 · avg=19.0
- **Pattern hints:** datetime-string
- **All distinct values (231):** `2015-04-18 00:00:00`, `2024-01-03 00:00:00`, `2024-01-08 00:00:00`, `2024-01-14 00:00:00`, `2024-01-18 00:00:00`, `2024-01-26 00:00:00`, `2024-02-02 00:00:00`, `2024-02-07 00:00:00`, `2024-02-08 00:00:00`, `2024-02-09 00:00:00`, `2024-02-14 00:00:00`, `2024-02-20 00:00:00`, `2024-02-21 00:00:00`, `2024-02-22 00:00:00`, `2024-02-26 00:00:00`, `2024-02-27 00:00:00`, `2024-02-29 00:00:00`, `2024-03-04 00:00:00`, `2024-03-06 00:00:00`, `2024-03-09 00:00:00`, `2024-03-13 00:00:00`, `2024-03-20 00:00:00`, `2024-03-21 00:00:00`, `2024-03-27 00:00:00`, `2024-03-28 00:00:00`, `2024-04-01 00:00:00`, `2024-04-10 00:00:00`, `2024-04-18 00:00:00`, `2024-04-19 00:00:00`, `2024-05-02 00:00:00`, `2024-05-03 00:00:00`, `2024-05-06 00:00:00`, `2024-05-09 00:00:00`, `2024-05-10 00:00:00`, `2024-05-16 00:00:00`, `2024-05-17 00:00:00`, `2024-05-23 00:00:00`, `2024-05-28 00:00:00`, `2024-05-31 00:00:00`, `2024-06-05 00:00:00`, `2024-06-06 00:00:00`, `2024-06-13 00:00:00`, `2024-06-18 00:00:00`, `2024-06-19 00:00:00`, `2024-06-21 00:00:00`, `2024-06-28 00:00:00`, `2024-07-02 00:00:00`, `2024-07-04 00:00:00`, `2024-07-05 00:00:00`, `2024-07-11 00:00:00`, `2024-07-19 00:00:00`, `2024-07-24 00:00:00`, `2024-07-25 00:00:00`, `2024-07-26 00:00:00`, `2024-07-30 00:00:00`, `2024-08-02 00:00:00`, `2024-08-03 00:00:00`, `2024-08-04 00:00:00`, `2024-08-06 00:00:00`, `2024-08-08 00:00:00`, `2024-08-09 00:00:00`, `2024-08-13 00:00:00`, `2024-08-16 00:00:00`, `2024-08-21 00:00:00`, `2024-08-22 00:00:00`, `2024-08-23 00:00:00`, `2024-08-24 00:00:00`, `2024-08-28 00:00:00`, `2024-08-29 00:00:00`, `2024-08-30 00:00:00`, `2024-09-03 00:00:00`, `2024-09-05 00:00:00`, `2024-09-07 00:00:00`, `2024-09-10 00:00:00`, `2024-09-12 00:00:00`, `2024-09-13 00:00:00`, `2024-09-19 00:00:00`, `2024-09-26 00:00:00`, `2024-09-27 00:00:00`, `2024-10-03 00:00:00`, `2024-10-11 00:00:00`, `2024-10-17 00:00:00`, `2024-10-18 00:00:00`, `2024-10-21 00:00:00`, `2024-10-22 00:00:00`, `2024-10-30 00:00:00`, `2024-11-01 00:00:00`, `2024-11-06 00:00:00`, `2024-11-07 00:00:00`, `2024-11-08 00:00:00`, `2024-11-14 00:00:00`, `2024-11-15 00:00:00`, `2024-11-21 00:00:00`, `2024-11-22 00:00:00`, `2024-11-26 00:00:00`, `2024-12-05 00:00:00`, `2024-12-06 00:00:00`, `2024-12-11 00:00:00`, `2024-12-13 00:00:00`, `2024-12-17 00:00:00`, `2024-12-18 00:00:00`, `2024-12-19 00:00:00`, `2024-12-27 00:00:00`, `2025-01-02 00:00:00`, `2025-01-03 00:00:00`, `2025-01-09 00:00:00`, `2025-01-10 00:00:00`, `2025-01-17 00:00:00`, `2025-01-24 00:00:00`, `2025-01-31 00:00:00`, `2025-02-05 00:00:00`, `2025-02-07 00:00:00`, `2025-02-14 00:00:00`, `2025-02-19 00:00:00`, `2025-02-20 00:00:00`, `2025-02-27 00:00:00`, `2025-02-28 00:00:00`, `2025-03-06 00:00:00`, `2025-03-07 00:00:00`, `2025-03-13 00:00:00`, `2025-03-14 00:00:00`, `2025-03-18 00:00:00`, `2025-03-20 00:00:00`, `2025-03-28 00:00:00`, `2025-04-03 00:00:00`, `2025-04-10 00:00:00`, `2025-04-11 00:00:00`, `2025-04-16 00:00:00`, `2025-04-17 00:00:00`, `2025-04-18 00:00:00`, `2025-04-19 00:00:00`, `2025-04-25 00:00:00`, `2025-05-01 00:00:00`, `2025-05-08 00:00:00`, `2025-05-09 00:00:00`, `2025-05-15 00:00:00`, `2025-05-22 00:00:00`, `2025-05-29 00:00:00`, `2025-06-04 00:00:00`, `2025-06-05 00:00:00`, `2025-06-12 00:00:00`, `2025-06-19 00:00:00`, `2025-06-20 00:00:00`, `2025-06-26 00:00:00`, `2025-07-03 00:00:00`, `2025-07-10 00:00:00`, `2025-07-17 00:00:00`, `2025-07-18 00:00:00`, `2025-07-23 00:00:00`, `2025-07-24 00:00:00`, `2025-07-25 00:00:00`, `2025-07-31 00:00:00`, `2025-08-07 00:00:00`, `2025-08-08 00:00:00`, `2025-08-14 00:00:00`, `2025-08-15 00:00:00`, `2025-08-21 00:00:00`, `2025-08-28 00:00:00`, `2025-08-29 00:00:00`, `2025-09-04 00:00:00`, `2025-09-11 00:00:00`, `2025-09-12 00:00:00`, `2025-09-18 00:00:00`, `2025-09-25 00:00:00`, `2025-09-26 00:00:00`, `2025-10-03 00:00:00`, `2025-10-09 00:00:00`, `2025-10-10 00:00:00`, `2025-10-16 00:00:00`, `2025-10-17 00:00:00`, `2025-10-25 00:00:00`, `2025-10-30 00:00:00`, `2025-10-31 00:00:00`, `2025-11-05 00:00:00`, `2025-11-06 00:00:00`, `2025-11-13 00:00:00`, `2025-11-14 00:00:00`, `2025-11-20 00:00:00`, `2025-11-21 00:00:00`, `2025-11-26 00:00:00`, `2025-12-04 00:00:00`, `2025-12-05 00:00:00`, `2025-12-12 00:00:00`, `2025-12-18 00:00:00`, `2025-12-24 00:00:00`, `2026-01-02 00:00:00`, `2026-01-06 00:00:00`, `2026-01-07 00:00:00`, `2026-01-09 00:00:00`, `2026-01-15 00:00:00`, `2026-01-22 00:00:00`, `2026-01-30 00:00:00`, `2026-01-31 00:00:00`, `2026-02-05 00:00:00`, `2026-02-12 00:00:00`, `2026-02-19 00:00:00`, `2026-02-20 00:00:00`, `2026-02-26 00:00:00`, `2026-03-05 00:00:00`, `2026-03-06 00:00:00` _(+31 more)_

### `paymentType` — text

- **Declared type:** `varchar(100)`
- **Nullable:** True · **Null %:** 100.0%
- **Rows:** 3,457 · **Distinct:** 0 (0.0% of non-null)

### `openBalance` — float

- **Declared type:** `double`
- **Nullable:** True · **Null %:** 100.0%
- **Rows:** 3,457 · **Distinct:** 0 (0.0% of non-null)

### `updatedAt` — datetime

- **Declared type:** `timestamp`
- **Nullable:** True · **Null %:** 5.79%
- **Rows:** 3,457 · **Distinct:** 15 (0.46% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`2026-06-02 09:21:11` · max=`2026-06-03 07:51:09`
- **Length:** min=19 · max=19 · avg=19.0
- **Pattern hints:** datetime-string
- **All distinct values (15):** `2026-06-02 09:21:11`, `2026-06-02 09:21:12`, `2026-06-02 09:21:13`, `2026-06-02 09:21:14`, `2026-06-02 09:21:15`, `2026-06-02 09:21:16`, `2026-06-02 09:22:59`, `2026-06-02 09:23:00`, `2026-06-02 09:23:01`, `2026-06-02 09:23:02`, `2026-06-02 09:23:03`, `2026-06-02 09:23:04`, `2026-06-02 09:23:05`, `2026-06-02 09:23:06`, `2026-06-03 07:51:09`

### `uid` — text

- **Declared type:** `varchar(100)`
- **Nullable:** True · **Null %:** 3.38%
- **Rows:** 3,457 · **Distinct:** 3,340 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, INDEXED
- **Range:** min=`00P94J` · max=`ZZ5VIP`
- **Length:** min=6 · max=23 · avg=7.02
- **All distinct values (3340):** `00P94J`, `00Z3Z0`, `0124U3`, `012L52`, `0181NF`, `01BOS8`, `01HRTS`, `01LUCB`, `01SI5N`, `01YHP6`, `022DHE`, `02HPOW`, `02ICBR`, `02TNMD`, `034M71`, `034XMO`, `03RPOQ`, `03XRBK`, `04TXL7`, `059TRA`, `05B55W`, `05DFVZ`, `05QLYT`, `065GLP`, `06EYC2`, `06WR30`, `06XNNR`, `078UT1`, `07ATWY`, `07N82J`, `07OU92`, `07QBZ7`, `084BJ7`, `0AHHWS`, `0BB8MI`, `0BHNB3`, `0BL7CG`, `0C0A4J`, `0CBDO7`, `0CK8OR`, `0CT074`, `0DFIWW`, `0DXPQJ`, `0E3Q5L`, `0E8VO5`, `0EQACL`, `0EQBPF`, `0GPMXD`, `0GRG5L`, `0HKM3X`, `0HO1Q8`, `0HXD6M`, `0IA9FV`, `0IDBI9`, `0J14Y0`, `0JL4KA`, `0JRW21`, `0JZ1JF`, `0KD5N5`, `0L4LF1`, `0LUZIO`, `0MDRRJ`, `0MPQ53`, `0MZV4C`, `0N93C2`, `0N95BF`, `0O198J`, `0O1TMC`, `0OMUJF`, `0OTR89`, `0PZ5JI`, `0R15RS`, `0R8ZMB`, `0SUHFL`, `0T3NXC`, `0T8OQN`, `0T9U5A`, `0U3XH7`, `0U5L6K`, `0UN73R`, `0V30JV`, `0V54JU`, `0VA587`, `0WB10N`, `0WPX72`, `0WVNP1`, `0X259W`, `0X8NCJ`, `0XCYZQ`, `0XOHE0`, `0Y956V`, `0YT2W4`, `0Z51C9`, `1041IZ`, `10UAWJ`, `11MKO5`, `11ULND`, `12K2QE`, `12NPBX`, `131MCZ`, `13D505`, `146LVW`, `14YXXX`, `159FDQ`, `15H4KI`, `16590G`, `17Z8NP`, `18NA7B`, `18OIF7`, `19C1PQ`, `1A7YQ7`, `1AMGWX`, `1B3Z4W`, `1B811U`, `1BODYQ`, `1CCTA4`, `1CE7W5`, `1CIM0X`, `1DFJGI`, `1DH63L`, `1E72I6`, `1EMVAM`, `1ESQFK`, `1F2MCF`, `1F2TTL`, `1FK7MS`, `1FRWYQ`, `1FSQP1`, `1FUGFI`, `1G58GB`, `1G9L5Q`, `1H3ZQO`, `1H4RTB`, `1I1B4E`, `1I7PVC`, `1IMAE2`, `1IYF1E`, `1JLTLD`, `1K1K5E`, `1L0RWT`, `1L84NS`, `1LHPCH`, `1LS6MU`, `1MKQLD`, `1MNXJP`, `1MOKFK`, `1MU4M5`, `1MWWR4`, `1MWXSP`, `1N0K9N`, `1NI7YS`, `1NJMMV`, `1O2UKM`, `1O5QTM`, `1O8UX4`, `1OCI3Q`, `1OP6WT`, `1OWW32`, `1PQ8C4`, `1PRDXO`, `1QA3LA`, `1QD7VR`, `1QYT0R`, `1QYX65`, `1R43P8`, `1RB60I`, `1RH0KR`, `1RQHSN`, `1SM6LL`, `1SVYEW`, `1T4O9O`, `1TFPIO`, `1TWL2Q`, `1TZURD`, `1UOI28`, `1US6N7`, `1VLYI2`, `1VPCAI`, `1VRN1R`, `1VYB0F`, `1W486O`, `1WE7IZ`, `1X9WQ9`, `1XFZK6`, `1XT6S4`, `1Y14BJ`, `1Z0935`, `207YWV`, `20DK0J`, `20GEM6`, `211A6W`, `211QKV`, `21CMEO`, `22S9RY`, `23883I`, `23C2YG`, `23G2SU`, `23HJJN`, `23U7PG`, `2453D0` _(+3140 more)_

### `createdAt` — datetime

- **Declared type:** `datetime`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 3,457 · **Distinct:** 9 (0.26% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`2026-06-02 09:21:11` · max=`2026-06-04 11:10:04`
- **Length:** min=19 · max=19 · avg=19.0
- **Pattern hints:** datetime-string
- **All distinct values (9):** `2026-06-02 09:21:11`, `2026-06-02 09:21:12`, `2026-06-02 09:21:13`, `2026-06-02 09:21:14`, `2026-06-02 09:21:15`, `2026-06-02 09:21:16`, `2026-06-03 07:51:09`, `2026-06-04 11:10:03`, `2026-06-04 11:10:04`

### `tenantid` — integer

- **Declared type:** `int`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 3,457 · **Distinct:** 2 (0.06% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`1` · max=`99`
- **Length:** min=1 · max=2 · avg=1.06
- **Pattern hints:** boolean-token, integer-as-text
- **All distinct values (2):** `1`, `99`

### `brand_id` — text

- **Declared type:** `varchar(36)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 3,457 · **Distinct:** 2 (0.06% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`ca323241-ef74-425f-aa67-239247ccd0e9` · max=`cmmakqdsn0037qsoig4b4yo9t`
- **Length:** min=25 · max=36 · avg=25.64
- **Pattern hints:** uuid
- **All distinct values (2):** `ca323241-ef74-425f-aa67-239247ccd0e9`, `cmmakqdsn0037qsoig4b4yo9t`

## Sample rows

| id | date | ordernumber | storeid | customername | productname | producttype | qty | variant | lotnumber | unitprice | subtotal | status | deliverydate | paymenttype | openbalance | updatedat | uid | createdat | tenantid | brand_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00a1b73g6mpwfgvia | 2024-04-10 00:00:00 | 54 | — | Pine Grove Organics | GMO Cart | Cart | 15.0 | 0.5g | — | 25.0 | 375.0 | Completed | 2024-04-10 00:00:00 | — | — | 2026-06-02 09:21:15 | C6OEGT | 2026-06-02 09:21:15 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| 00fskq9xempwfgt8w | 2026-05-18 00:00:00 | 690 | — | Sweetspot | G13 Skunk | Cart | 10.0 | 0.5g | ML-133 | 25.0 | 250.0 | Completed | 2026-05-21 00:00:00 | — | — | 2026-06-02 09:21:11 | 23C2YG | 2026-06-02 09:21:11 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| 00nzpg4eumpwfgtns | 2026-03-16 00:00:00 | 634 | — | Poultney Cannabis Supply | Black Maple | Cart | 10.0 | — | ML-104 | 22.0 | 220.0 | Completed | 2026-03-20 00:00:00 | — | — | 2026-06-02 09:21:11 | 65X0N6 | 2026-06-02 09:21:11 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| 01m6cx417mpwfgto8 | 2025-08-04 00:00:00 | 443 | — | Bud Stop | Dulce De Uva | Preroll | 20.0 | 1g | HL-17 | 6.5 | 130.0 | Completed | 2025-08-07 00:00:00 | — | — | 2026-06-02 09:21:13 | VFUZK9 | 2026-06-02 09:21:13 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| 01t449nvtmpwfgvia | 2024-04-18 00:00:00 | 58 | — | Tea House | Raspberry Hash Rosin | Rhize Rosin Gummies 20 ct | 50.0 | — | — | 17.0 | 850.0 | Completed | 2024-04-18 00:00:00 | — | — | 2026-06-02 09:21:15 | O3VLOD | 2026-06-02 09:21:15 | 1 | cmmakqdsn0037qsoig4b4yo9t |

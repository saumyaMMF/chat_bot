# `rhize_brands` (mysql)

- **Schema:** —
- **Rows:** 1,691
- **Columns:** 5
- **Primary key:** `id`
- **Indexes:** `idx_brands_tenantid`(N: tenantid), `idx_isRhize`(N: isRhize), `PRIMARY`(U: id), `unique_tenant_brand`(U: tenantid,name)

## Columns

### `id` — text

- **Declared type:** `varchar(36)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 1,691 · **Distinct:** 1,691 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, PRIMARY-KEY
- **Range:** min=`01k3o5fyeavhmmaqzjd3` · max=`ztmp8ao3shimmaqyjxz`
- **Length:** min=17 · max=36 · avg=22.98
- **All distinct values (1691):** `01k3o5fyeavhmmaqzjd3`, `04w9as7ipsfrmmaqzjd3`, `05b01bnyakl7mmaqz594`, `0c7dk7z57osmmaqwc75`, `0gccokpck8vqmmasxaxk`, `0hipo1pn1zo6mmaqwc75`, `0i2jf49gi3bmmmasppdl`, `0lz4dlphgu9ammaqyjxz`, `0rguj3rl6wpemmaqyjxz`, `0wcftvs8r9tmmaqwc75`, `114pirszp5efmmar4e2a`, `12gk30yrrhfammaqyjxz`, `144y7t7gdx7pmmasppdl`, `18ou6oc7yrvmmaqx4jf`, `19izhwnp0c5mmaqwc75`, `1cc7u5fq6a2mmar23wn`, `1cembhwsukmmarhcu9`, `1coujji715zmmarkr20`, `1ea6hs6hak0jmmaqyjxz`, `1f3bqbav6lgmmar23wn`, `1f849noqf2ammaqz594`, `1f9p31sjfmbmmaqzjd3`, `1gszlt825fammaqzjd3`, `1n7m926kt29mmaqz594`, `1nbm1x4xi4kmmaqyjxz`, `1pfycwblvk5mmaqz594`, `1s8amubef05mmasxaxk`, `1taf2guf6rrmmaqx4jf`, `1wg5q7m1lfzmmaqx4jf`, `1whtjuav19mmaqxmws`, `1x4xgo3h8qtmmaqz594`, `20fb47rctymmaqzv2w`, `28mzjj51tdnmmaqxmws`, `2az0mqabntymmaqyjxz`, `2cvp13uxf72mmar23wn`, `2hqcbi0br6mmmarhcu9`, `2jh8dzi9bhammar4e2a`, `2mvdw44cktmmat65lh`, `2oyamvh930qmmaqwc75`, `2ru858qpy12mmaqzjd3`, `2wadylhk0zqmmar23wn`, `3029d7zpc87mmaqzjd3`, `30883ka2m6rmmaqyjxz`, `337rviezk1nmmaqwc75`, `33dn4bz48srmmaqwc75`, `3bxc0b0agpbmmaqx4jf`, `3bxqe4iz0ermmaqzjd3`, `3c17ch0fw1jmmar4e2a`, `3lr0wwacrf7mmas2ddg`, `3mjuun4c35kmmardout`, `3mqx922o207mmarosj0`, `3omzxujjcldmmasxaxk`, `3tnp90c3d1ammaqyjxz`, `3uq2xom7cwqmmaqyjxz`, `3uqwu60o3cammaqwc75`, `3v5ezisgky1mmautbsk`, `3z5mgi1866rmmaqx4jf`, `41kt4sdva1wmmaqz594`, `48nypz5ash3mmar23wn`, `49wvkbxt07lmmasxaxk`, `4fhkqmbvyrhmmaqx4jf`, `4hgxys0m1ppmmaqwc75`, `4j5nsshrhqymmaqyjxz`, `4krjqis00a3mmaqyjxz`, `4l0k5zw4a0bmmaq78vg`, `4n7o3pzyf86mmaqx4jf`, `4sje0kvvhk8mmasxaxk`, `4srs3n2b74cmmaqyjxz`, `4xwn5e23g1ymmar23wn`, `50g93gp300ummaqz594`, `54t4l6a5vammaqyjxz`, `5bvwc6ws7rymmaqyjxz`, `5c2eytjed26mmaqwc75`, `5e2ox4b9f8tmmaqyjxz`, `5lmqe41ydohmmasxaxk`, `5m0773zs90nmmasxaxk`, `5s7hupgfl4mmaqzjd3`, `5ssrjd1kd6wmmar23wn`, `5tfohma4tvxmmaqwc75`, `5uok7n03thimmaqxmws`, `5vh5opgkfjrmmaq78vg`, `5wx9b19mn7dmmaqwc75`, `5xo06k4f52mmmar9y3c`, `5zg8ykxwykkmmaqwc75`, `601tdvtww9ummarhcu9`, `61ftcvsvvxmmasxaxk`, `62t691kk7gmmaqwc75`, `63anfmujjoimmaq78vg`, `6a6450olfh6mmaqyjxz`, `6du9f80q9bhmmaqx4jf`, `6gqeune5dt4mmaqwc75`, `6i2bk3qer2lmmaqwc75`, `6j98by19j7immaqzjd3`, `6nrvsi3j16nmmaqwc75`, `6phbc0su97ymmaqyjxz`, `6qzudq9arkpmmaqz594`, `6s5hljaaj2mmaqyjxz`, `6v4mrwjmy6hmmar4e2a`, `6xw4wkygkdwmmaqzjd3`, `70gsct9syzmmaqx4jf`, `70y67v2whlmmaq78vg`, `732sr9tdnmmmaqx4jf`, `78yg3zc3rnbmmaqyjxz`, `7c7q3vo3o3nmmaqyjxz`, `7e1bf9mtcbymmaqxmws`, `7iivkry04jkmmaqyjxz`, `7mi84tqimcbmmaqyjxz`, `7qilkt0qhpmmmar9y3c`, `7s67d9bopqdmmaqyjxz`, `7xpcx5g7uh4mmar9y3c`, `84jbtuoztpdmmaqyjxz`, `84xke5rublmmmaqyjxz`, `85efnzuowkmmaqyjxz`, `87fy8raf31lmmar4e2a`, `89vhix0ld3hmmaqyjxz`, `8az1kpr1koammaqzjd3`, `8fkl16wfftmmaqwc75`, `8flwplxzgjmmar9y3c`, `8i68eb1ft0ammaqyjxz`, `8ovl0y34n8ummaqx4jf`, `8pifefp95h6mmaqwc75`, `8q5ncr2hz8bmmaqwc75`, `8ufqtt9qyfrmmaqx4jf`, `8wcev82gbgommaqwc75`, `8x4txl5m862mmar23wn`, `8xw2yc2hylhmmaqyjxz`, `8zbadcbl03immaqyjxz`, `91kq5sdw9b4mmaqxmws`, `923602am9bgmmaqz594`, `92p7f8zt8mbmmaqx4jf`, `92te1wof3fmmaqyjxz`, `94cw31trutmmmaqz594`, `94iq72ff8o9mmaqyjxz`, `95ncn3c90dmmaqyjxz`, `9b3ehg8q8dmmaqzjd3`, `9fkye3gmlqfmmaqyjxz`, `9hdj2dln56wmmaqz594`, `9qutnht1nwwmmasxaxk`, `9s5d9wdvhpmmmaqyjxz`, `9u9got0pbnfmmaqz594`, `9zba9y3q34gmmasxaxk`, `a2c8cko6i3mmaqyjxz`, `a4hh5ymg98qmmaqyjxz`, `a5bb33e7-5365-11f1-bc3a-7e0f98092871`, `a6malmku12ammaqyjxz`, `a7owiwaetbmmaqwc75`, `a8ou55gzubmmaqz594`, `aaq8s08eanfmmaqzjd3`, `adseaia3oacmmaqx4jf`, `afk5rcseoy8mmar4e2a`, `aimgix02hthmmaqyjxz`, `aio0gwdynr6mmaqyjxz`, `alckquyu45emmaqzjd3`, `amgcapn9huommaqzjd3`, `ams78jqlom8mmasxaxk`, `ar5rkbe8xsmmasxaxk`, `aw0xnv87jbfmmaqx4jf`, `ayucm5m2lgqmmar9y3c`, `b26kev1fnommaqz594`, `b2bej4b0b1hmmasxaxk`, `b4s7o99ln6vmmaqzjd3`, `b6h15g0yucemmaqxmws`, `b84lls9by8jmmaqwc75`, `beli3vrhf1rmmaqz594`, `bfjjmpcu8tpmmaqzjd3`, `blk4y9iu9ujmmasxaxk`, `bn1h53udkngmmaqyjxz`, `bqdkkfam5ybmmar23wn`, `bqoxsrpruuummaqzjd3`, `bqruntwwyvjmmarhcu9`, `bqtceakxjqqmmaqyjxz`, `bs2b2i1fjmummaqyjxz`, `bs4xatokzemmasxaxk`, `bwyc48awrgvmmar4e2a`, `by3gbmb1uznmmasxaxk`, `c2n5aqsi46gmmaqz594`, `c2sigqo3aoimmaqwc75`, `c5r9zfvmgummaqxmws`, `c6q3jvsiczkmmar4e2a`, `c7kp5cj4xs7mmautbsk`, `c9kvw2qficummaqx4jf`, `ca323241-ef74-425f-aa67-239247ccd0e9`, `cb2lqos3petmmautbsk`, `cdesov2sww6mmaqyjxz`, `chi3iqbi6h9mmaqwc75`, `ci8lemw3z5gmmaqx4jf`, `ckv8wtdqsy9mmaqwc75`, `cmmakqdsn002qqsoih7vdigqv`, `cmmakqdsn002rqsoim4plc5kt`, `cmmakqdsn002sqsoibyaswwp1`, `cmmakqdsn002tqsoi8o1af5rr`, `cmmakqdsn002uqsoitionpva4`, `cmmakqdsn002vqsoi1jciuxti`, `cmmakqdsn002wqsoik1kige9u`, `cmmakqdsn002xqsoiwjz8afqt`, `cmmakqdsn002yqsoizkz81hqu`, `cmmakqdsn002zqsoip2hjuhac`, `cmmakqdsn0030qsoi253vqyf8`, `cmmakqdsn0031qsoim9bpx1pc`, `cmmakqdsn0032qsoihp1zcuyh` _(+1491 more)_

### `name` — text

- **Declared type:** `varchar(255)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 1,691 · **Distinct:** 1,689 (99.88% of non-null)
- **Range:** min=` Green Mountain Kana` · max=`Zweet Inzanity`
- **Length:** min=1 · max=45 · avg=13.0
- **All distinct values (1689):** ` Green Mountain Kana`, `.decimal`, `(1906)`, `(the) Essence`, `&Shine`, `#HASH`, `1791`, `1791 Star Cannabis`, `1791*`, `1906`, `1937`, `1958`, `1958 Cannabis Co.`, `1958 Cannabis Company`, `1964`, `1G Preroll`, `1Spliff`, `1UP`, `3 Saints`, `3Saints`, `40 Tons`, `45 North`, `45 North Nurseries`, `5 POINTS`, `5 Points Cannabis`, `7 Leaf Genetics`, `710 Labs`, `7ashish`, `802 Farmacy`, `802 glue`, `802 Grow`, `802 GROW LLC`, `9th State`, `9th State Cannabis`, `A Flying Cactus`, `Ac/Dc`, `Addison Pure`, `Adults Only`, `AFG`, `Afghan Hemp`, `AIC`, `Airo`, `Alchemy Pure`, `Algonquin Technologies`, `Alien Brainz`, `ALL BLISS CANNABIS`, `Alternative Compassion Services`, `Altitude`, `Altitude Drops`, `altitude drops/new england can co.`, `ALTIUS`, `AltSol`, `Altus`, `Always Toasted`, `Ambr`, `American Hash Makers`, `Ammanana Growers`, `Amnesia`, `Animal`, `Animal House`, `Annamana`, `Anthem`, `Antler Ridge`, `APOLLO`, `APOLLO LEGACY`, `Apollo Legacy LLC`, `Apple Soup`, `Applegate Valley Organics`, `Aqua ViTea`, `Arden's Garden`, `ARDENS GARDEN`, `Armetra Wilcox`, `AroMed Essentials`, `ASPIRE`, `Astro Labs`, `At Ease`, `Athletic Brewing Co.`, `Atlas Cultivars`, `Atlas Processing Center (Atlas Extracts)`, `Autumn Brands`, `Avexia`, `Awella Gardens`, `AXEA`, `Ayrloom`, `BACK COUNTRY`, `Back Forty`, `Back Home Cannabis`, `Backcountry Botanicals`, `Backwoods Farm`, `Baked`, `Bakked`, `Balance`, `Banana`, `Banger`, `Banned`, `Bannermans Batch`, `Banting Farm Buds`, `BC 1/2 OZ`, `BC 1/4`, `BC Doobies`, `BC Green`, `BC OZ`, `BC Smalls`, `Be Humble.`, `Be Kind`, `Be-Leaf & Terps Co.`, `Bed`, `BEE KIND`, `BEL SOLAS FARM`, `Bel Solas Farms`, `Belushi's Farm`, `Bent Glass`, `bent tree`, `Bern gallery`, `Bern legacy`, `Bern Legacy Cannabis`, `Bern Legacy x Disco Biscuits`, `Bern Legacy x Florist`, `Bern Legacy x Roundhouse Hash Co.`, `Bern Legacy x SOTM`, `Bern Legacy/Vermont Kind Craft Cannabis`, `Bern Living Organics`, `BERNIS DOBIS LLC`, `Better Made Cannabis`, `Betty`, `Betty's Eddies`, `Betty’s Edibles`, `Bhang`, `BHL Enterprises`, `BIG`, `Big Bag O' Buds`, `Big Dawg Brands`, `Big House `, `Big House Cultivation`, `Big House Cultivators `, `BIRDLAND`, `Birdman`, `Birdseye Botanicals`, `Bison Botanics`, `Bizee Beez Farms`, `Bizzee Bee Farm`, `Bizzee Bee Farms`, `Bizzee Beez Farm`, `BIZZEE BEEZ FARMS`, `Bizzee Beez Farms LLC`, `Black`, `Black Market Extracts`, `Black Mountain`, `Blackberry`, `Blackstone Valley Cannabis`, `Blaze n chill`, `Blezz`, `Blezz Farm`, `Blezz Farms`, `Bliss Bar`, `BLISS BARS`, `Blissed`, `Blissful`, `BLKMKT`, `Blondie Bud Co`, `Blondies Bud`, `Blue`, `Blue Anchor`, `Blue Sage`, `Blueberry`, `Bog Brook Botanicals`, `Bog Brook Cream Pie`, `Bogart's Kitchen`, `BOLD GLAZED`, `Bold Growth`, `Bold Team`, `Bordertown Apothecary`, `Bordertown Farm `, `BOREAS VENTURES`, `Bosa`, `Botanist`, `Bougie Glass`, `Boujee Bones`, `Bouket`, `BOXHOT`, `BOXHOT 1000`, `BOXHOT Highlighters`, `Brass Knuckles`, `Breathe Free`, `BREEZE Canna`, `Bright Valley Organics`, `Brix Stix`, `Broken Coast Cannabis`, `Brookfield Buds`, `Brookfield Buds - Some Weed`, `Brookfield Buds -Campfire Hash Co`, `Brother Nature Brands`, `Brown Dog Cannabis`, `BTV Blunts`, `Bubble Kush`, `Bubby's Baked`, `Bud Barn`, `BUD LAFLEUR`, `Buddies Brand`, `Buddy Blooms` _(+1489 more)_

### `isRhize` — integer

- **Declared type:** `tinyint(1)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 1,691 · **Distinct:** 2 (0.12% of non-null)
- **Flags:** LOW-CARDINALITY (categorical), INDEXED
- **Range:** min=`0` · max=`1`
- **Length:** min=1 · max=1 · avg=1.0
- **Pattern hints:** boolean-token, integer-as-text
- **All distinct values (2):** `0`, `1`

### `createdAt` — datetime

- **Declared type:** `datetime`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 1,691 · **Distinct:** 38 (2.25% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`2026-03-03 12:18:26` · max=`2026-05-30 10:22:06`
- **Length:** min=19 · max=19 · avg=19.0
- **Pattern hints:** datetime-string
- **All distinct values (38):** `2026-03-03 12:18:26`, `2026-03-03 12:18:27`, `2026-03-03 12:18:28`, `2026-03-03 12:18:29`, `2026-03-03 12:18:30`, `2026-03-03 12:18:31`, `2026-03-03 14:51:31`, `2026-03-03 15:11:02`, `2026-03-03 15:11:39`, `2026-03-03 15:12:03`, `2026-03-03 15:12:45`, `2026-03-03 15:13:13`, `2026-03-03 15:13:31`, `2026-03-03 15:13:47`, `2026-03-03 15:15:31`, `2026-03-03 15:17:18`, `2026-03-03 15:21:37`, `2026-03-03 15:24:32`, `2026-03-03 15:27:23`, `2026-03-03 15:30:01`, `2026-03-03 15:33:10`, `2026-03-03 15:38:17`, `2026-03-03 15:40:51`, `2026-03-03 15:43:43`, `2026-03-03 15:46:40`, `2026-03-03 15:49:38`, `2026-03-03 15:52:43`, `2026-03-03 15:55:55`, `2026-03-03 16:01:52`, `2026-03-03 16:07:46`, `2026-03-03 16:14:39`, `2026-03-03 16:21:31`, `2026-03-03 16:27:55`, `2026-03-03 16:41:50`, `2026-03-03 16:49:07`, `2026-03-03 17:00:40`, `2026-05-19 09:32:26`, `2026-05-30 10:22:06`

### `tenantid` — integer

- **Declared type:** `int`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 1,691 · **Distinct:** 3 (0.18% of non-null)
- **Flags:** LOW-CARDINALITY (categorical), INDEXED
- **Range:** min=`1` · max=`99`
- **Length:** min=1 · max=2 · avg=1.0
- **Pattern hints:** integer-as-text
- **All distinct values (3):** `1`, `3`, `99`

## Sample rows

| id | name | isrhize | createdat | tenantid |
| --- | --- | --- | --- | --- |
| 01k3o5fyeavhmmaqzjd3 | First Frost | 0 | 2026-03-03 15:13:31 | 1 |
| 04w9as7ipsfrmmaqzjd3 | Pleasantea | 0 | 2026-03-03 15:13:31 | 1 |
| 05b01bnyakl7mmaqz594 | Pinnacle Vally Farms | 0 | 2026-03-03 15:13:13 | 1 |
| 0c7dk7z57osmmaqwc75 | Good Pot Co | 0 | 2026-03-03 15:11:02 | 1 |
| 0gccokpck8vqmmasxaxk | Cruise Control by BOXHOT | 0 | 2026-03-03 16:07:46 | 1 |

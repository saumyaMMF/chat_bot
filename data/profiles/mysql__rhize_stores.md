# `rhize_stores` (mysql)

- **Schema:** —
- **Rows:** 175
- **Columns:** 14
- **Primary key:** `id`
- **Indexes:** `idx_isPartner`(N: isPartner), `idx_slug`(N: slug), `PRIMARY`(U: id), `uq_slug_tenant`(U: slug,tenantid)

## Columns

### `id` — text

- **Declared type:** `varchar(36)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 175 · **Distinct:** 175 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, PRIMARY-KEY
- **Range:** min=`16188dfd-5363-11f1-bc3a-7e0f98092871` · max=`y9u7ori9svrmmaqynf7`
- **Length:** min=18 · max=36 · avg=24.41
- **All distinct values (175):** `16188dfd-5363-11f1-bc3a-7e0f98092871`, `16189cf4-5363-11f1-bc3a-7e0f98092871`, `ais70qd1trmmaqzk3v`, `cmmairubn00004joiaf2uaesn`, `cmmairw9500014joi5rx66iqm`, `cmmairwlx00024joi8q28o5fo`, `cmmairwyu00034joi780hjxhp`, `cmmairxbp00044joi6c4lhlz7`, `cmmairxoq00054joiv8igy6dw`, `cmmairy1k00064joiji5h0o96`, `cmmairyeb00074joio3fxz5ft`, `cmmairywb00084joiut1ie57f`, `cmmairz9500094joi7f4tco1j`, `cmmairzm2000a4joijluvjb37`, `cmmais008000b4joiaz7ywi7q`, `cmmais0d6000c4joi49ir2yg5`, `cmmais0q0000d4joi9a9525q6`, `cmmais1fo000f4joiwpmxgsnm`, `cmmais1we000g4joi4p86k9od`, `cmmais296000h4joiz03cxb5a`, `cmmais2lx000i4joiefoqo58x`, `cmmais2yp000j4joi88pyfcuk`, `cmmais3el000k4joil3ezu6xu`, `cmmais3rf000l4joie6355b1x`, `cmmais447000m4joipymca9x7`, `cmmais4h1000n4joizk5cbbo0`, `cmmais4tw000o4joibf62now7`, `cmmais57y000p4joi0j3lot9h`, `cmmais5kp000q4joi5q2xqmyj`, `cmmais60c000r4joirho6akjl`, `cmmais6d9000s4joiysqf0z5m`, `cmmais6q5000t4joi2zqb6xjo`, `cmmais72z000u4joivbu377og`, `cmmais7fr000v4joim2ekp8fi`, `cmmais7sm000w4joihqqtkpli`, `cmmais85t000x4joilosddsbm`, `cmmais8k1000y4joiw42gf1x8`, `cmmajj9qz0000jaoit4tpf6pc`, `cmmajjait0003jaoifbra8gy2`, `cmmajjd4m000ejaoi6m2fq5tt`, `cmmajjeia000kjaoiwjkaijd7`, `cmmajjg26000rjaoinavapxl3`, `cmmajjhfc000xjaoi1o6y4jps`, `cmmajjija0012jaoiejf184m5`, `cmmajjm21001hjaoil85237zn`, `cmmajjo49001qjaoifvlmfozo`, `cmmajjq8j001zjaoii9hnuc8v`, `cmmajjrgu0024jaoirnzjb2lv`, `cmmajjtl9002cjaoi3udnyw3n`, `cmmajk1xl003bjaoio37rymal`, `cmmajk3if003ijaoiksku3hi7`, `cmmajk4fi003mjaoios33yfd0`, `cmmajk6kd003vjaoiyws0yfog`, `cmmakbfqa003r7ooijuswljzh`, `cmmakbj6c00447ooicdpb5llz`, `cmmakbm3b004g7ooifaivnv79`, `cmmakqcxr0001qsoiwph09tl0`, `cmmakqcxr0002qsoib01or8xx`, `cmmakqcxr0003qsoicz3ovbt7`, `cmmakqcxr0004qsoipojnvtjq`, `cmmakqcxr0005qsoilkyzldpy`, `cmmakqcxr0006qsoiua87e66m`, `cmmakqcxr0007qsoioejgz7ye`, `cmmakqcxr0009qsoi9cefwy73`, `cmmakqcxr000aqsoic314usa1`, `cmmakqcxr000bqsoirrs91gzr`, `cmmakqcxr000cqsoi063hwxgr`, `cmmakqcxr000dqsoi3of2puoy`, `cmmakqcxr000eqsoiufeiq4cj`, `cmmakqcxr000fqsoiveph4z7q`, `cmmakqcxr000gqsoifovbxjtx`, `cmmakqcxr000iqsoik7ktu4e8`, `cmmakqcxr000jqsoi2j123njp`, `cmmakqcxr000kqsoiu168ehp3`, `cmmakqcxr000lqsoi4s4gtfc4`, `cmmakqcxr000mqsoi1ntlje5r`, `cmmakqcxr000nqsoi3fjrdmec`, `cmmakqcxr000sqsoihyjr3xq8`, `cmmakqcxr000tqsoifzfhf2pg`, `cmmakqcxr000vqsoimi0fbng8`, `cmmakqcxr000wqsoilur8cjx9`, `cmmakqcxr000yqsoi7xgcwmpn`, `cmmakqcxr000zqsoisv098hdx`, `cmmakqcxr0010qsoiett3ry5r`, `cmmakqcxr0011qsoigdlwutz2`, `cmmakqcxr0012qsoi2fzn3vgh`, `cmmakqcxr0013qsoi0u8e9seq`, `cmmakqcxr0014qsoizbdnk3mj`, `cmmakqcxr0015qsoizrh29jm3`, `cmmakqcxs0016qsoiehapmxtt`, `cmmakqcxs0017qsoiibq66zmx`, `cmmakqcxs0018qsoi40814v9q`, `cmmakqcxs0019qsoi0jx2ijda`, `cmmakqcxs001aqsoiap3vbjfd`, `cmmakqcxs001bqsoi5z2yjqrq`, `cmmakqcxs001cqsoicqegec3n`, `cmmakqcxs001dqsoirt6o2549`, `cmmakqcxs001eqsoir3imu603`, `cmmakqcxs001gqsoio19uc88v`, `cmmakqcxs001hqsoia1av4t90`, `cmmakqcxs001iqsoisx8og0ld`, `cmmakqcxs001jqsoir6v87el9`, `cmmakqcxs001mqsoi1itzi1hg`, `cmmakqcxs001nqsoi5r5v59px`, `cmmakqcxs001oqsoi69de4qsm`, `cmmakqcxs001rqsoi9f73xft2`, `cmmakqcxs001tqsoih24ycuew`, `cmmakqcxs001uqsoi7sfcbbc6`, `cmmakqcxs001vqsoidlymlf57`, `cmmakqcxs001wqsoi7yu4xbzd`, `cmmakqcxs001xqsoivb7afopf`, `cmmakqcxs001zqsoi3azehvqx`, `cmmakqcxs0020qsoi3dfxykcw`, `cmmakqcxs0023qsoiuburqpmg`, `cmmakqcxs0024qsoigoli8llg`, `cmmakqcxs0025qsoip3zqlgvp`, `cmmakqcxs0026qsoisl8j4kyb`, `cmmakqcxs0027qsoidmgi4vgd`, `cmmakqcxs0028qsoivthfv6ff`, `cmmakqcxs0029qsoi52hutyeg`, `cmmakqcxs002aqsoid901wmmd`, `cmmakqcxs002bqsoijftrbiqr`, `cmmakqcxs002cqsoinflf2oq3`, `cmmakqcxs002dqsoi7luspi9o`, `cmmakqcxs002eqsoih2vt1trs`, `cmmakqcxs002fqsoimny7r0rp`, `cmmakqcxs002gqsoifckzayri`, `cmmakqcxs002hqsoi4hv76rqm`, `cmmakqcxs002iqsoi4cl7nx7q`, `cmmakqcxs002jqsoikwq5v3ak`, `cmmakqcxs002kqsoio4y4a4hh`, `cmmakqcxs002lqsoixm5dgy0a`, `cmmakqcxs002mqsoipqstlhh3`, `cmmakqcxs002nqsoimrg4relq`, `cmmakqcxs002oqsoimwz918fl`, `cmmakqcxs002pqsoiqvfa45u6`, `demo_st_0474549e4b674ef`, `demo_st_087cd72fc677564`, `demo_st_0d8d7d0abd0467e`, `demo_st_18bca7fac9f8881`, `demo_st_1b70ad361f0ca04`, `demo_st_217509b543473bd`, `demo_st_231489c9203897c`, `demo_st_29961a37447a78f`, `demo_st_388c872ebc48229`, `demo_st_5154fffc3ac8476`, `demo_st_5c43c27357e96d4`, `demo_st_63f25f28a7bdb29`, `demo_st_64049da73e8c9c7`, `demo_st_65399bf497731ae`, `demo_st_763e6c2cb77baf7`, `demo_st_7e626207eb302fd`, `demo_st_8c12369d3538751`, `demo_st_928703fb909e489`, `demo_st_9f8a426b5706d21`, `demo_st_a3e3cb124c1846b`, `demo_st_a64565af88cb69a`, `demo_st_ace42f725d5b49d`, `demo_st_b49412bf815f18c`, `demo_st_b815c539c7cc911`, `demo_st_d10e95c4c8a7abe`, `demo_st_d2edd1c0512bc5e`, `demo_st_e1532389e6dfb9f`, `demo_st_e694194d8738699`, `demo_st_ed87d68b5ed4325`, `demo_st_f97d27985a8e528`, `g1hu4lfyfn4mmaqzk3v`, `mmgkovd9r2mmaqz5z5`, `n57amr06nzcmmaqynf7`, `o1yesbv8nfmmaqz5z5`, `tjrlov45e7rmmaqynf7`, `u8f23dxsbcmmaqzk3v`, `u90hryimp3mmaqxnck`, `vw21vlk6onkmmaqynf7`, `y9u7ori9svrmmaqynf7`

### `slug` — text

- **Declared type:** `varchar(255)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 175 · **Distinct:** 175 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, INDEXED
- **Range:** min=`100centerrd` · max=`woollymammothshop`
- **Length:** min=6 · max=28 · avg=13.64
- **All distinct values (175):** `100centerrd`, `10railroadstreet`, `120riverst`, `135mainst`, `139pearlst`, `1513us2`, `158nmainst`, `174westst`, `180smainst`, `185churchstreet`, `187vt15`, `21essexwaysuite216`, `21metrowayunit8`, `2200wildbranchrd`, `24pleasantst`, `2653waterburystowerd`, `269mainstreetriverviewunit`, `2parkst`, `319swantonrd`, `31northvt`, `335grovest`, `36wmainst`, `3jscannabis`, `4267usroute5`, `440rockinghamrd`, `442woodstockrdste3a`, `44mainst`, `4542mainstreet`, `4merrillln102`, `50woodstockrd`, `65northgateavesuite6`, `7pineviewdr`, `8768vtrt30`, `87mainst`, `8vermonthighway17`, `97churchst`, `9thstatecannabis`, `bernlegacycannabis`, `bestbuds`, `bluesagevt`, `budbarnvt`, `budega`, `bwellvt`, `cambridgecannabiscompany`, `cannmaxx`, `capitalcannabisvt`, `castlecannabis`, `cleancountry`, `clearskyworcester`, `cloud9vt`, `craftcanabisco`, `craftsburycannabis`, `damesvt`, `demo-store-01`, `demo-store-02`, `demo-store-03`, `demo-store-04`, `demo-store-05`, `demo-store-06`, `demo-store-07`, `demo-store-08`, `demo-store-09`, `demo-store-10`, `demo-store-11`, `demo-store-12`, `demo-store-13`, `demo-store-14`, `demo-store-15`, `demo-store-16`, `demo-store-17`, `demo-store-18`, `demo-store-19`, `demo-store-20`, `demo-store-21`, `demo-store-22`, `demo-store-23`, `demo-store-24`, `demo-store-25`, `demo-store-26`, `demo-store-27`, `demo-store-28`, `demo-store-29`, `demo-store-30`, `depotshop`, `devilsdencannabis`, `domecity`, `downtorootsvt`, `emeraldrose`, `euphoriacannabis`, `fiveseasonscannabis`, `floatoncannabis`, `floravt`, `flowerfirst`, `forbinsfinest`, `freedomflowerllc`, `garciascannabis`, `gastonweedcompany`, `goodfirevt`, `gramcentral`, `greenhavenherbal`, `greenhousedispensary`, `greenleafcentral`, `greenmountaincannabisworks`, `greenmountaintherapeutics`, `greenpeakdispensary`, `greenunion`, `heybudcollective`, `highcountryvt`, `higherelevation`, `highsociety`, `idealcannabis`, `juanasgarden`, `juniperlane`, `killingtonmountaindispensary`, `kingdomboyz`, `kingdomkind`, `kushies`, `lakeeffectvt`, `littleamsterdam`, `littlecitygreen`, `lucky7`, `luckyyoucannabis`, `magicmann`, `maryjanejunction`, `maryjanemountain`, `matterhornapothecary`, `miltonremedies`, `montyvt`, `mothaplant`, `mountaingirlcannabis`, `newbedfordmassachusetts`, `ninnygoatandco`, `northeastkannabis`, `pinegroveorganicsorg`, `polestarvt`, `poultneycannabissupply`, `ratuscannabissupply`, `rimeline`, `rollingtwenties`, `royalbuds`, `silvertherapeutics`, `simpsonbrookdispensary`, `somethingwickedcannabis`, `somewhereonthemountain`, `stoneleafdispensary`, `sunkissedfarm`, `sweetspot`, `teahousevt`, `thebudstop`, `thecannabisshop`, `thedankcloset`, `thegasstation`, `thegreenman`, `theherbalcollectivevt`, `theherbcloset`, `thehiddengrove`, `thehighbar`, `theorywellness`, `tmmdispensary`, `true802cannabis`, `upstateelevatoroperators`, `valleymeade`, `verdiggityorganics`, `vermontalternative`, `vermontcannabiscafe`, `vermontraphouse`, `vermontterps`, `vtstrong`, `vtsundaydrive`, `vtterps`, `vveeds`, `wildlegacycannabis`, `winooskiorganics`, `winterlandhaze`, `woollymammothshop`

### `name` — text

- **Declared type:** `varchar(255)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 175 · **Distinct:** 175 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE
- **Range:** min=`10 Railroad Street` · max=`Woollymammothshop`
- **Length:** min=6 · max=30 · avg=15.11
- **All distinct values (175):** `10 Railroad Street`, `100 Center Rd`, `120 River St`, `135 Main St.`, `139 Pearl St`, `1513 US-2`, `158 N Main St`, `174 West St`, `180 S Main St`, `185 Church Street`, `187 VT 15`, `2 Park St`, `21 Essex Way Suite 216`, `21 Metro Way Unit 8`, `2200 Wild Branch Rd,`, `24 Pleasant St`, `2653 Waterbury-Stowe Rd.`, `269 Main Street Riverview Unit`, `319 Swanton Rd`, `31Northvt`, `335 Grove St`, `36 W Main St`, `3Jscannabis`, `4 Merrill Ln #102`, `4267 U.S. Route 5`, `44 Main St`, `440 Rockingham Rd.`, `442 Woodstock Rd Ste 3A`, `4542 Main Street`, `50 Woodstock Rd`, `65 Northgate Ave Suite 6`, `7 Pine View Dr`, `8 Vermont Highway 17`, `87 Main St`, `8768 VT Rt 30`, `97 Church St`, `9thstatecannabis`, `Bernlegacycannabis`, `Bestbuds`, `Bluesagevt`, `Budbarnvt`, `Budega`, `Bwellvt`, `Cambridgecannabiscompany`, `cannmaxx`, `Capitalcannabisvt`, `Castlecannabis`, `Cleancountry`, `Clear Sky Worcester`, `Cloud9Vt`, `Craftcanabisco`, `Craftsburycannabis`, `Damesvt`, `Demo Dispensary 01`, `Demo Dispensary 02`, `Demo Dispensary 03`, `Demo Dispensary 04`, `Demo Dispensary 05`, `Demo Dispensary 06`, `Demo Dispensary 07`, `Demo Dispensary 08`, `Demo Dispensary 09`, `Demo Dispensary 10`, `Demo Dispensary 11`, `Demo Dispensary 12`, `Demo Dispensary 13`, `Demo Dispensary 14`, `Demo Dispensary 15`, `Demo Dispensary 16`, `Demo Dispensary 17`, `Demo Dispensary 18`, `Demo Dispensary 19`, `Demo Dispensary 20`, `Demo Dispensary 21`, `Demo Dispensary 22`, `Demo Dispensary 23`, `Demo Dispensary 24`, `Demo Dispensary 25`, `Demo Dispensary 26`, `Demo Dispensary 27`, `Demo Dispensary 28`, `Demo Dispensary 29`, `Demo Dispensary 30`, `Depotshop`, `devilsdencannabis`, `Domecity`, `Downtorootsvt`, `Emeraldrose`, `euphoriacannabis`, `Fiveseasonscannabis`, `Floatoncannabis`, `Floravt`, `Flowerfirst`, `Forbinsfinest`, `Freedomflower`, `Garciascannabis`, `Gasstationvt`, `Gastonweedcompany`, `Goodfirevt`, `Gramcentral`, `greenhavenherbal`, `Greenhousedispensary`, `Greenleaf-Central`, `Greenmountaincannabisworks`, `Greenmountaintherapeutics`, `Greenpeakdispensary`, `Greenunion`, `Heybudcollective`, `Highcountryvt`, `Higherelevation`, `Highsociety`, `Idealcannabis`, `Juanasgarden`, `Juniperlane`, `Killingtonmountaindispensary`, `Kingdom-Kind`, `Kingdomboyz`, `Kushies`, `Lakeeffectvt`, `littleamsterdam`, `Littlecitygreen`, `lucky7`, `Luckyyoucannabis`, `Magicmann`, `Maryjanejunction`, `Maryjanemountain`, `matterhornapothecary`, `Miltonremedies`, `Montyvt`, `Mothaplant`, `Mountaingirlcannabis`, `New Bedford Massachusetts`, `Ninnygoatandco`, `Northeastkannabis`, `Pinegroveorganics.Org`, `Polestarvt`, `Poultneycannabissupplyvt`, `Ratuscannabissupply`, `Rimeline`, `Rollingtwenties`, `Royalbuds`, `Silvertherapeutics`, `Simpsonbrookdispensary`, `Somethingwickedcannabis`, `Somewhereonthemountain`, `Stoneleafdispensary`, `Sunkissedfarm`, `Sweetspotfarms`, `Teahousevt`, `Thebudstop`, `Thecannabisshop`, `Thedankcloset`, `Thegreenman`, `Theherbalcollectivevt`, `Theherbcloset`, `Thehiddengrove`, `Thehighbar`, `Theorywellness`, `Tmmdispensary`, `True802Cannabis`, `Upstate-Elevatoroperators`, `Valleymeade`, `Verdiggityorganics`, `Vermontalternative`, `Vermontcannabiscafe`, `Vermontraphouse`, `Vermontterps`, `vtstrong`, `Vtsundaydrive`, `vtterps`, `Vveeds`, `Wildlegacy-Cannabis`, `Winooskiorganics`, `Winterlandhaze`, `Woollymammothshop`

### `licenseNumber` — text

- **Declared type:** `varchar(255)`
- **Nullable:** True · **Null %:** 63.43%
- **Rows:** 175 · **Distinct:** 64 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE
- **Range:** min=`31° North Holdings LLC` · max=`VherBio, LLC DBA Polestar`
- **Length:** min=5 · max=40 · avg=18.44
- **All distinct values (64):** `31° North Holdings LLC`, `802 420 LLC`, `Bern Legacy Cannabis`, `Big Intelligence Group dba/Wild Legacy`, `Cambridge Cannabis Company`, `Capital Cannabis Company`, `Cloud 9 Cannabis Dispensary`, `Clover VT LLC, DBA Sunday Drive`, `Craftsbury Cannabis LLC`, `DEMO-LIC-0001`, `DEMO-LIC-0002`, `DEMO-LIC-0003`, `DEMO-LIC-0004`, `DEMO-LIC-0005`, `DEMO-LIC-0006`, `DEMO-LIC-0007`, `DEMO-LIC-0008`, `DEMO-LIC-0009`, `DEMO-LIC-0010`, `DEMO-LIC-0011`, `DEMO-LIC-0012`, `DEMO-LIC-0013`, `DEMO-LIC-0014`, `DEMO-LIC-0015`, `DEMO-LIC-0016`, `DEMO-LIC-0017`, `DEMO-LIC-0018`, `DEMO-LIC-0019`, `DEMO-LIC-0020`, `DEMO-LIC-0021`, `DEMO-LIC-0022`, `DEMO-LIC-0023`, `DEMO-LIC-0024`, `DEMO-LIC-0025`, `DEMO-LIC-0026`, `DEMO-LIC-0027`, `DEMO-LIC-0028`, `DEMO-LIC-0029`, `DEMO-LIC-0030`, `Down to the Roots`, `DP Holdings LLC DBA The Bud Stop`, `FLORA`, `Forbin's Reserve`, `Freedom Flower, LLC`, `Gaston Weed Company`, `Gram Central, LLC`, `Green Mountain Cannabis Works LLC`, `Higher Elevation, LLC`, `Kushies`, `Magic Mann`, `Mountain Girl Cannabis`, `New England Cannabis Partners, LLC`, `Palatino Ronci LLC`, `Pine Grove Organics`, `Ratu's Cannabis Supply, LLC`, `Rimeline Products LLC - dba Rimeline`, `Sawyer Dog Retail LLC`, `Sharp Family Farms d.b.a The Gas Station`, `Something Wicked Cannabis Company`, `Somewhere On The Mountain, LLC`, `Sweetspot Farms Dispensary`, `The Tea House, LLC`, `Valley Meade Dispensary`, `VherBio, LLC DBA Polestar`

### `address` — text

- **Declared type:** `varchar(500)`
- **Nullable:** True · **Null %:** 63.43%
- **Rows:** 175 · **Distinct:** 59 (92.19% of non-null)
- **Range:** min=`100 Demo Way` · max=`Woodstock VT 05091`
- **Length:** min=12 · max=30 · avg=16.17
- **All distinct values (59):** `100 Demo Way`, `101 Demo Way`, `102 Demo Way`, `103 Demo Way`, `104 Demo Way`, `105 Demo Way`, `106 Demo Way`, `107 Demo Way`, `108 Demo Way`, `109 Demo Way`, `110 Demo Way`, `111 Demo Way`, `112 Demo Way`, `113 Demo Way`, `114 Demo Way`, `115 Demo Way`, `116 Demo Way`, `117 Demo Way`, `118 Demo Way`, `119 Demo Way`, `120 Demo Way`, `121 Demo Way`, `122 Demo Way`, `123 Demo Way`, `124 Demo Way`, `125 Demo Way`, `126 Demo Way`, `127 Demo Way`, `128 Demo Way`, `129 Demo Way`, `335 Grove St`, `Barre, VT 05641`, `Bethel, VT 05032`, `Burlington, Vermont 05401`, `Burlington, VT 05401`, `Cambridge, VT 05464`, `Chester, VT 05149`, `Craftsbury, VT 05826`, `Danville, VT 05828`, `Derby VT 05829`, `Essex Junction, VT 05452`, `Fair Haven, VT 05743`, `Manchester Center, VT 05255`, `Middlebury, VT 05753`, `Milton, VT 05468`, `Montpelier, VT 05602`, `Morrisville, VT 05661`, `Morrisville, VT 05662`, `Randolph, VT 05060`, `Rawsonville VT 05155`, `Rockingham, VT 05101`, `Rutland, VT 05470`, `Rutland, VT 05701`, `St. Albans City, VT 05478`, `Waitsfield, VT 05673`, `Waterbury, VT 05677`, `White River Junction, VT 05001`, `Wilmington, VT 05363`, `Woodstock VT 05091`

### `city` — text

- **Declared type:** `varchar(255)`
- **Nullable:** True · **Null %:** 66.29%
- **Rows:** 175 · **Distinct:** 34 (57.63% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`(802) 262-1701` · max=`Worcester`
- **Length:** min=5 · max=14 · avg=10.76
- **All distinct values (34):** `(802) 262-1701`, `(802) 332-6043`, `(802) 353-8731`, `(802) 464-1390`, `(802) 622-0359`, `(802) 871-5810`, `(802) 989-1163`, `(802)851-8587`, `603-548-9059`, `781-281-0677`, `802-279-2244`, `802-289-1869`, `802-297-2847`, `802-309-1693`, `802-323-8197`, `802-367-3562`, `802-417-7774`, `802-428-6703`, `802-560-7927`, `802-565-5168`, `802-579-6831`, `802-595-1299`, `802-683-0189`, `802-793-9858`, `802-851-8735`, `816-547-6831`, `845-764-0081`, `Brattleboro`, `Burlington`, `Manchester`, `Montpelier`, `New Bedford`, `Stowe`, `Worcester`

### `phone` — text

- **Declared type:** `varchar(100)`
- **Nullable:** True · **Null %:** 63.43%
- **Rows:** 175 · **Distinct:** 64 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE
- **Range:** min=`(555) 555-1000` · max=`Wilson Knight`
- **Length:** min=3 · max=20 · avg=13.19
- **All distinct values (64):** `(555) 555-1000`, `(555) 555-1001`, `(555) 555-1002`, `(555) 555-1003`, `(555) 555-1004`, `(555) 555-1005`, `(555) 555-1006`, `(555) 555-1007`, `(555) 555-1008`, `(555) 555-1009`, `(555) 555-1010`, `(555) 555-1011`, `(555) 555-1012`, `(555) 555-1013`, `(555) 555-1014`, `(555) 555-1015`, `(555) 555-1016`, `(555) 555-1017`, `(555) 555-1018`, `(555) 555-1019`, `(555) 555-1020`, `(555) 555-1021`, `(555) 555-1022`, `(555) 555-1023`, `(555) 555-1024`, `(555) 555-1025`, `(555) 555-1026`, `(555) 555-1027`, `(555) 555-1028`, `(555) 555-1029`, `Adam Blanchard`, `Andrea Cheney`, `Ashley Sorrentino`, `Avery Cheney`, `Ben`, `Brandon Marshall`, `Buying Team`, `Christian Pozcubut`, `Christopher Chabot`, `Cole`, `Devin Clark`, `Dora Palmieri`, `Dove Sharp`, `Dusty Kenney`, `Ebo Singleton`, `Jeff White`, `Jennifer Betit-Engel`, `Joe Ruggiero`, `Josh MacDuff`, `Keith LaPlante`, `Lisa Merriman`, `Michael Sims`, `Parker Rice`, `Patricia James`, `Raeven Petell`, `Robert Ronci`, `Ronnie Kreth`, `Sarah Lefkowitz`, `Scott Blair`, `Shannon`, `Shannon Morrill`, `Shawn Furbish`, `Uday Smith`, `Wilson Knight`

### `contactName` — text

- **Declared type:** `varchar(255)`
- **Nullable:** True · **Null %:** 82.86%
- **Rows:** 175 · **Distinct:** 30 (100.0% of non-null)
- **Flags:** UNIQUE-LIKE, LOW-CARDINALITY (categorical)
- **Range:** min=`Demo Contact 01` · max=`Demo Contact 30`
- **Length:** min=15 · max=15 · avg=15.0
- **All distinct values (30):** `Demo Contact 01`, `Demo Contact 02`, `Demo Contact 03`, `Demo Contact 04`, `Demo Contact 05`, `Demo Contact 06`, `Demo Contact 07`, `Demo Contact 08`, `Demo Contact 09`, `Demo Contact 10`, `Demo Contact 11`, `Demo Contact 12`, `Demo Contact 13`, `Demo Contact 14`, `Demo Contact 15`, `Demo Contact 16`, `Demo Contact 17`, `Demo Contact 18`, `Demo Contact 19`, `Demo Contact 20`, `Demo Contact 21`, `Demo Contact 22`, `Demo Contact 23`, `Demo Contact 24`, `Demo Contact 25`, `Demo Contact 26`, `Demo Contact 27`, `Demo Contact 28`, `Demo Contact 29`, `Demo Contact 30`

### `isPartner` — integer

- **Declared type:** `tinyint(1)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 175 · **Distinct:** 2 (1.14% of non-null)
- **Flags:** LOW-CARDINALITY (categorical), INDEXED
- **Range:** min=`0` · max=`1`
- **Length:** min=1 · max=1 · avg=1.0
- **Pattern hints:** boolean-token, integer-as-text
- **All distinct values (2):** `0`, `1`

### `tier` — text

- **Declared type:** `varchar(10)`
- **Nullable:** True · **Null %:** 100.0%
- **Rows:** 175 · **Distinct:** 0 (0.0% of non-null)

### `createdAt` — datetime

- **Declared type:** `datetime`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 175 · **Distinct:** 44 (25.14% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`2026-03-03 11:23:35` · max=`2026-06-04 11:09:59`
- **Length:** min=19 · max=19 · avg=19.0
- **Pattern hints:** datetime-string
- **All distinct values (44):** `2026-03-03 11:23:35`, `2026-03-03 11:23:38`, `2026-03-03 11:23:39`, `2026-03-03 11:23:40`, `2026-03-03 11:23:41`, `2026-03-03 11:23:42`, `2026-03-03 11:23:43`, `2026-03-03 11:23:44`, `2026-03-03 11:23:45`, `2026-03-03 11:23:46`, `2026-03-03 11:23:47`, `2026-03-03 11:23:48`, `2026-03-03 11:23:49`, `2026-03-03 11:23:50`, `2026-03-03 11:23:51`, `2026-03-03 11:23:52`, `2026-03-03 11:23:53`, `2026-03-03 11:23:54`, `2026-03-03 11:44:55`, `2026-03-03 11:44:56`, `2026-03-03 11:44:59`, `2026-03-03 11:45:01`, `2026-03-03 11:45:03`, `2026-03-03 11:45:05`, `2026-03-03 11:45:06`, `2026-03-03 11:45:11`, `2026-03-03 11:45:14`, `2026-03-03 11:45:16`, `2026-03-03 11:45:18`, `2026-03-03 11:45:21`, `2026-03-03 11:45:32`, `2026-03-03 11:45:34`, `2026-03-03 11:45:35`, `2026-03-03 11:45:38`, `2026-03-03 12:06:49`, `2026-03-03 12:06:54`, `2026-03-03 12:06:57`, `2026-03-03 12:18:24`, `2026-03-03 15:12:03`, `2026-03-03 15:12:50`, `2026-03-03 15:13:14`, `2026-03-03 15:13:32`, `2026-05-19 09:14:06`, `2026-06-04 11:09:59`

### `updatedAt` — datetime

- **Declared type:** `datetime`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 175 · **Distinct:** 9 (5.14% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`2026-05-12 11:58:50` · max=`2026-06-04 11:09:59`
- **Length:** min=19 · max=19 · avg=19.0
- **Pattern hints:** datetime-string
- **All distinct values (9):** `2026-05-12 11:58:50`, `2026-05-19 11:24:13`, `2026-05-19 11:24:35`, `2026-05-19 11:24:53`, `2026-05-19 11:25:05`, `2026-05-19 11:25:27`, `2026-05-19 11:32:07`, `2026-05-30 10:25:32`, `2026-06-04 11:09:59`

### `tenantid` — integer

- **Declared type:** `int`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 175 · **Distinct:** 3 (1.71% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`1` · max=`99`
- **Length:** min=1 · max=2 · avg=1.17
- **Pattern hints:** integer-as-text
- **All distinct values (3):** `1`, `3`, `99`

### `brand_id` — text

- **Declared type:** `varchar(36)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 175 · **Distinct:** 3 (1.71% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`a5bb33e7-5365-11f1-bc3a-7e0f98092871` · max=`cmmakqdsn0037qsoig4b4yo9t`
- **Length:** min=25 · max=36 · avg=27.01
- **Pattern hints:** uuid
- **All distinct values (3):** `a5bb33e7-5365-11f1-bc3a-7e0f98092871`, `ca323241-ef74-425f-aa67-239247ccd0e9`, `cmmakqdsn0037qsoig4b4yo9t`

## Sample rows

| id | slug | name | licensenumber | address | city | phone | contactname | ispartner | tier | createdat | updatedat | tenantid | brand_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 16188dfd-5363-11f1-bc3a-7e0f98092871 | newbedfordmassachusetts | New Bedford Massachusetts | — | — | New Bedford | — | — | 1 | — | 2026-05-19 09:14:06 | 2026-05-30 10:25:32 | 3 | a5bb33e7-5365-11f1-bc3a-7e0f98092871 |
| 16189cf4-5363-11f1-bc3a-7e0f98092871 | clearskyworcester | Clear Sky Worcester | — | — | Worcester | — | — | 1 | — | 2026-05-19 09:14:06 | 2026-05-30 10:25:32 | 3 | a5bb33e7-5365-11f1-bc3a-7e0f98092871 |
| ais70qd1trmmaqzk3v | littleamsterdam | littleamsterdam | — | — | — | — | — | 0 | — | 2026-03-03 15:13:32 | 2026-05-12 11:58:50 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| cmmairubn00004joiaf2uaesn | 2653waterburystowerd | 2653 Waterbury-Stowe Rd. | 31° North Holdings LLC | Waterbury, VT 05677 | 802-560-7927 | Ben | — | 0 | — | 2026-03-03 11:23:35 | 2026-05-12 11:58:50 | 1 | cmmakqdsn0037qsoig4b4yo9t |
| cmmairw9500014joi5rx66iqm | 440rockinghamrd | 440 Rockingham Rd. | 802 420 LLC | Rockingham, VT 05101 | 802-428-6703 | Joe Ruggiero | — | 0 | — | 2026-03-03 11:23:38 | 2026-05-12 11:58:50 | 1 | cmmakqdsn0037qsoig4b4yo9t |

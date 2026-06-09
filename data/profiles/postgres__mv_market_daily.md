# `mv_market_daily` (postgres)

- **Schema:** public
- **Rows:** 2,489,661
- **Columns:** 8
- **Indexes:** `idx_mv_daily_date`(N: date), `idx_mv_daily_date_brand`(N: date,brand), `idx_mv_daily_date_brand_company`(N: date,brand,company,category,revenue,quantity,sku_count), `idx_mv_daily_date_cat`(N: date,category), `idx_mv_daily_date_company`(N: date,company), `idx_mv_daily_date_rev`(N: date,revenue), `idx_mv_daily_state_date`(N: state,date), `idx_mv_date`(N: date), `idx_mv_date_brand`(N: date,brand), `idx_mv_date_cat`(N: date,category), `idx_mv_date_company`(N: date,company), `idx_mvmd_date`(N: date), `mv_market_daily_state_date_idx`(N: state,date)

## Columns

### `date` — date

- **Declared type:** `date`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 2,489,661 · **Distinct:** 229 (0.01% of non-null)
- **Range:** min=`2025-07-25` · max=`2026-06-07`
- **Length:** min=10 · max=10 · avg=10.0
- **Pattern hints:** date-string-YYYY-MM-DD
- **All distinct values (229):** `2025-07-25`, `2025-07-31`, `2025-08-01`, `2025-08-02`, `2025-08-05`, `2025-08-06`, `2025-08-21`, `2025-08-26`, `2025-09-10`, `2025-09-22`, `2025-09-26`, `2025-10-01`, `2025-10-03`, `2025-10-06`, `2025-10-07`, `2025-10-08`, `2025-10-09`, `2025-10-10`, `2025-10-11`, `2025-10-12`, `2025-10-13`, `2025-10-14`, `2025-10-15`, `2025-10-16`, `2025-10-17`, `2025-10-18`, `2025-10-19`, `2025-10-20`, `2025-10-21`, `2025-10-22`, `2025-10-23`, `2025-10-24`, `2025-10-25`, `2025-10-26`, `2025-10-27`, `2025-10-28`, `2025-10-29`, `2025-10-30`, `2025-10-31`, `2025-11-01`, `2025-11-02`, `2025-11-03`, `2025-11-04`, `2025-11-05`, `2025-11-06`, `2025-11-07`, `2025-11-08`, `2025-11-09`, `2025-11-10`, `2025-11-11`, `2025-11-12`, `2025-11-13`, `2025-11-14`, `2025-11-15`, `2025-11-16`, `2025-11-17`, `2025-11-18`, `2025-11-19`, `2025-11-20`, `2025-11-21`, `2025-11-22`, `2025-11-23`, `2025-11-24`, `2025-11-25`, `2025-11-26`, `2025-11-27`, `2025-11-28`, `2025-11-30`, `2025-12-01`, `2025-12-02`, `2025-12-04`, `2025-12-05`, `2025-12-08`, `2025-12-09`, `2025-12-10`, `2025-12-11`, `2025-12-12`, `2025-12-15`, `2025-12-16`, `2025-12-18`, `2025-12-19`, `2025-12-20`, `2025-12-22`, `2025-12-23`, `2025-12-24`, `2025-12-25`, `2025-12-26`, `2025-12-29`, `2025-12-30`, `2025-12-31`, `2026-01-02`, `2026-01-03`, `2026-01-05`, `2026-01-06`, `2026-01-07`, `2026-01-08`, `2026-01-09`, `2026-01-11`, `2026-01-12`, `2026-01-13`, `2026-01-14`, `2026-01-15`, `2026-01-16`, `2026-01-17`, `2026-01-19`, `2026-01-20`, `2026-01-21`, `2026-01-22`, `2026-01-27`, `2026-01-28`, `2026-01-29`, `2026-01-30`, `2026-02-03`, `2026-02-04`, `2026-02-06`, `2026-02-09`, `2026-02-10`, `2026-02-11`, `2026-02-12`, `2026-02-16`, `2026-02-17`, `2026-02-18`, `2026-02-19`, `2026-02-20`, `2026-02-21`, `2026-02-23`, `2026-02-24`, `2026-02-25`, `2026-02-26`, `2026-02-27`, `2026-02-28`, `2026-03-01`, `2026-03-02`, `2026-03-03`, `2026-03-04`, `2026-03-05`, `2026-03-06`, `2026-03-07`, `2026-03-08`, `2026-03-09`, `2026-03-10`, `2026-03-11`, `2026-03-12`, `2026-03-13`, `2026-03-14`, `2026-03-15`, `2026-03-16`, `2026-03-17`, `2026-03-18`, `2026-03-19`, `2026-03-20`, `2026-03-22`, `2026-03-23`, `2026-03-24`, `2026-03-25`, `2026-03-26`, `2026-03-27`, `2026-03-28`, `2026-03-29`, `2026-03-30`, `2026-03-31`, `2026-04-01`, `2026-04-02`, `2026-04-03`, `2026-04-04`, `2026-04-05`, `2026-04-06`, `2026-04-07`, `2026-04-08`, `2026-04-09`, `2026-04-10`, `2026-04-11`, `2026-04-12`, `2026-04-13`, `2026-04-14`, `2026-04-15`, `2026-04-16`, `2026-04-17`, `2026-04-18`, `2026-04-19`, `2026-04-20`, `2026-04-21`, `2026-04-22`, `2026-04-23`, `2026-04-24`, `2026-04-25`, `2026-04-26`, `2026-04-27`, `2026-04-28`, `2026-04-29`, `2026-04-30`, `2026-05-01`, `2026-05-02`, `2026-05-03`, `2026-05-04`, `2026-05-05`, `2026-05-06`, `2026-05-07`, `2026-05-08`, `2026-05-09` _(+29 more)_

### `category` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 2,489,661 · **Distinct:** 6 (0.0% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`Concentrate` · max=`Vape/Cart`
- **Length:** min=5 · max=11 · avg=7.35
- **All distinct values (6):** `Concentrate`, `Edible`, `Flower`, `Other`, `Preroll`, `Vape/Cart`

### `brand` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 2,489,661 · **Distinct:** 21,885 (0.88% of non-null)
- **Range:** min=`` · max=`ZZZ's Collective`
- **Length:** min=0 · max=59 · avg=12.36
- **Top values:** `` (35,915), `Pinnacle Valley Farms` (28,776), `Forbins Finest` (24,445), `Stone Leaf Cannabis` (21,194), `Sunset Lake Cannabis` (20,410), `Clean Cannabis Company` (18,274), `Mr. Z` (16,477), `Rosie's Confections` (16,472), `Satori` (15,739), `Bern Legacy Cannabis` (14,784), `Florist` (14,008), `Doughboi Farms` (13,740), `Gaston Weed Company` (12,983), `Northern Craft Cannabis` (12,776), `Mr. Tree` (12,529), `Emerald Visions` (12,436), `Taunik` (12,046), `Bushy Beard Cultivation` (11,603), `Upstate Elevator Operators` (11,349), `Rhize Cannabis` (10,928)

### `company` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 2,489,661 · **Distinct:** 3,401 (0.14% of non-null)
- **Range:** min=`` · max=`Zipson38Th`
- **Length:** min=0 · max=54 · avg=15.8
- **All distinct values (3401):** ``, `0045Portlandpowell`, `0046Portland11Th`, `0051Bend`, `1045Smeridianllcstabilitycannabis`, `1106Rebeccastreetllc`, `1634Funk`, `1912Cannabiscompany`, `1Connectionllc1`, `2020Solutionsironstreet`, `2020Solutionsnorthbellingham`, `2020Solutionspacifichighway`, `296Retailventuredispensary`, `311Pagespringfield`, `31Cannabisgrandhaven`, `31Cannabismuskegon`, `31Northvt`, `365Recreationalshoreline`, `3807Harlemcannabisllc`, `3Fifteenprimocolumbia`, `3Fifteenprimostlouis`, `3Fifteenprimovalleypark`, `3Jscannabis`, `3Jsumindreretail`, `3Kingsorganics`, `420Dankdetroit`, `420Factory`, `420Spotshop`, `426677Sunsetscannabis`, `6Brickssspringfield`, `716Cannabisblasdell`, `816Dispensary`, `911Kronic`, `960Bloomingdaleroadllc`, `9Thstatecannabis`, `Aaahealthcenter`, `Aberdeenmaryland`, `Aboveallgreenerynorthmedicalfryeburgretail`, `Aclassyjointcannabis`, `Acleef`, `Adegoke`, `Adnaportland`, `Affinitydispensary`, `Affinitydispensarybridgeport`, `Affinitydispensarybridgeportmed`, `Affinityhealthandwellness`, `Affinityhealthandwellnessrec`, `Afny`, `Aircitycannabisllc`, `Akfrost`, `Akronmenu`, `Alaskacannabisexchangeanchorageak`, `Alaskankushcompany`, `Albuquerquecraftcannabis`, `Allgreens1`, `Allgreensadultuse`, `Allgreensrec`, `Allpro`, `Altaialternativecare`, `Altalowermanhattan`, `Alteredstate`, `Alternativecompassionservices`, `Alternativecompassionservicesbridgewaterrecreational`, `Alternativecompassionserviceshullrec`, `Alternativeessence`, `Alternativeessenceoxfordoxfordprovisions`, `Alternativemedicinecapitolhill`, `Alternativetherapiesgroupamesbury`, `Alternativetherapiesgroupsalem`, `Alternativetherapiesgroupsalisbury`, `Altitudecannabis`, `Altitudecannabisdispensary`, `Altitudedispensary1`, `Altitudeithaca`, `Altitudeny`, `Altitudeprosser`, `Altitudeunser`, `Amazonorganics`, `Amberlightcannabishouse`, `Ampadultretailsalem`, `Amplifybedford`, `Amplifycolumbus`, `Amplifycoventry`, `Amplifyeastlakellcdbaamplify`, `Amplifyptllcdbaamplify`, `Amsterdamcannabis`, `Anacostiaorganics`, `Andovercannabis`, `Animacanninc`, `Ankafieldretail`, `Antidoteinksterinc`, `Apexnoire`, `Apothcaarlington`, `Appointmentarea`, `Arborside`, `Arcanna`, `Arizonanaturalconceptsmed`, `Arizonanaturalconceptsrec`, `Arizonaorganix`, `Arizonatreeequity2Tucson`, `Aromafarms`, `Ascendcincinnatiohio`, `Ascendenglewoodohio`, `Ashandivydispensary`, `Aspirecannabis`, `Astrobuds`, `Astrobudsconsumptionlounge`, `Atlanticfarms`, `Atlanticfarmsretailportlandrec`, `Atlanticfarmsretailsomerville`, `Atlanticfarmsretailthomaston`, `Atlanticflower`, `Atlanticmedicinalpartners`, `Atlanticmedicinalpartnersinc`, `Atlanticmedicinalpartnersinc1`, `Atnc`, `Attistradingcocully`, `Attistradingcogladstone`, `Attistradingcolincolncity`, `Attistradingcotillamook`, `Auntmarys`, `Auntmarysflemingtonrec`, `Auracannabiscofallriver`, `Auraofrhodeisland`, `Authentic231`, `Ayrdispensarybackbay`, `Ayrdispensarygibsonia`, `Ayrdispensaryplymouthmeeting`, `Ayrdispensarywatertown`, `Ayrwellnessbrynmawr`, `Ayrwellnessindiana`, `Ayrwellnessmontgomeryville`, `Ayrwellnessnewcastle`, `Azdeeplyrooted`, `Azflowerpowernirvanaaj`, `Baccofarmsflint`, `Backpackboyzdetroit`, `Backpackboyzmonroerec`, `Baiked`, `Bakedcannabis`, `Bakinbad`, `Baltimorehfl`, `Bankofbuds`, `Bask`, `Baskinc400Winthropsttaunton`, `Baskmedkiosk`, `Bataviaillinois`, `Battleborndispensarymoundhouse`, `Battleborndispensaryreno`, `Battlecreekmichigan`, `Bayshorecannabis`, `Baysidecannabisdispensary`, `Bazonzoesprovisioningcenter`, `Bazonzoessouthlansing`, `Bazonzoeswalledlakerec`, `Bb1563Llcdbathefireplace`, `Bbbotanics`, `Bbcfllc`, `Beachboyscannabiscooldorchard`, `Beargrassnaturals`, `Bebrooklynny`, `Beechnutridgeenterprises`, `Behudsonvalley`, `Belfaircannabisco`, `Belmontcollective2`, `Benedictssupply`, `Berkeleyrec`, `Berkshirerootseastbostonmed`, `Berkshirerootseastbostonrec`, `Berkshirerootspittsfieldmed`, `Berkshirerootspittsfieldrec`, `Bernersonmain`, `Bernlegacycannabis`, `Bestatenisland`, `Bestbuds`, `Bestbuds2`, `Bestbudsdover`, `Bestbudsgeorgetown`, `Bestbudz146St`, `Bethelbuds`, `Bethesdahfl`, `Betterbudslongview`, `Betterdaze`, `Betweentheferns`, `Bewellorganicmedicine`, `Bewellorganicmedicineinc`, `Beyondhellolittleferry`, `Beyondthepines`, `Bigcityflavorsdispensary`, `Bigfootbudco`, `Bigfootwellnesscrystalfalls`, `Bigriverbendrec`, `Birchrunrec`, `Blackhatharvard`, `Blackmarketcannapoughkeepsie`, `Blackstonevalleycannabis`, `Blackstonevalleycannabismed`, `Blackwoodwellness`, `Blainedispensary`, `Blairwellnesscenter` _(+3201 more)_

### `revenue` — float

- **Declared type:** `numeric`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 2,489,661 · **Distinct:** 51,434 (2.07% of non-null)
- **Range:** min=`0` · max=`118685.75`
- **Length:** min=1 · max=9 · avg=2.22
- **Pattern hints:** integer-as-text
- **Top values:** `0` (1,443,157), `48` (21,376), `60` (21,107), `36` (18,395), `72` (16,126), `24` (14,086), `30` (13,648), `120` (11,903), `54` (11,508), `96` (11,163), `108` (10,307), `12` (10,160), `144` (9,678), `42` (9,380), `43.2` (7,913), `84` (7,733), `14.4` (7,389), `90` (7,195), `28.8` (7,068), `180` (6,712)

### `quantity` — float

- **Declared type:** `numeric`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 2,489,661 · **Distinct:** 4,187 (0.17% of non-null)
- **Range:** min=`0` · max=`123821`
- **Length:** min=1 · max=6 · avg=2.01
- **Pattern hints:** integer-as-text
- **All distinct values (4187):** `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11`, `12`, `13`, `14`, `15`, `16`, `17`, `18`, `19`, `20`, `21`, `22`, `23`, `24`, `25`, `26`, `27`, `28`, `29`, `30`, `31`, `32`, `33`, `34`, `35`, `36`, `37`, `38`, `39`, `40`, `41`, `42`, `43`, `44`, `45`, `46`, `47`, `48`, `49`, `50`, `51`, `52`, `53`, `54`, `55`, `56`, `57`, `58`, `59`, `60`, `61`, `62`, `63`, `64`, `65`, `66`, `67`, `68`, `69`, `70`, `71`, `72`, `73`, `74`, `75`, `76`, `77`, `78`, `79`, `80`, `81`, `82`, `83`, `84`, `85`, `86`, `87`, `88`, `89`, `90`, `91`, `92`, `93`, `94`, `95`, `96`, `97`, `98`, `99`, `100`, `101`, `102`, `103`, `104`, `105`, `106`, `107`, `108`, `109`, `110`, `111`, `112`, `113`, `114`, `115`, `116`, `117`, `118`, `119`, `120`, `121`, `122`, `123`, `124`, `125`, `126`, `127`, `128`, `129`, `130`, `131`, `132`, `133`, `134`, `135`, `136`, `137`, `138`, `139`, `140`, `141`, `142`, `143`, `144`, `145`, `146`, `147`, `148`, `149`, `150`, `151`, `152`, `153`, `154`, `155`, `156`, `157`, `158`, `159`, `160`, `161`, `162`, `163`, `164`, `165`, `166`, `167`, `168`, `169`, `170`, `171`, `172`, `173`, `174`, `175`, `176`, `177`, `178`, `179`, `180`, `181`, `182`, `183`, `184`, `185`, `186`, `187`, `188`, `189`, `190`, `191`, `192`, `193`, `194`, `195`, `196`, `197`, `198`, `199` _(+3987 more)_

### `sku_count` — integer

- **Declared type:** `smallint (int2)`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 2,489,661 · **Distinct:** 454 (0.02% of non-null)
- **Range:** min=`1` · max=`2278`
- **Length:** min=1 · max=4 · avg=1.1
- **Pattern hints:** integer-as-text
- **All distinct values (454):** `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11`, `12`, `13`, `14`, `15`, `16`, `17`, `18`, `19`, `20`, `21`, `22`, `23`, `24`, `25`, `26`, `27`, `28`, `29`, `30`, `31`, `32`, `33`, `34`, `35`, `36`, `37`, `38`, `39`, `40`, `41`, `42`, `43`, `44`, `45`, `46`, `47`, `48`, `49`, `50`, `51`, `52`, `53`, `54`, `55`, `56`, `57`, `58`, `59`, `60`, `61`, `62`, `63`, `64`, `65`, `66`, `67`, `68`, `69`, `70`, `71`, `72`, `73`, `74`, `75`, `76`, `77`, `78`, `79`, `80`, `81`, `82`, `83`, `84`, `85`, `86`, `87`, `88`, `89`, `90`, `91`, `92`, `93`, `94`, `95`, `96`, `97`, `98`, `99`, `100`, `101`, `102`, `103`, `104`, `105`, `106`, `107`, `108`, `109`, `110`, `111`, `112`, `113`, `114`, `115`, `116`, `117`, `118`, `119`, `120`, `121`, `122`, `123`, `124`, `125`, `126`, `127`, `128`, `129`, `130`, `131`, `132`, `133`, `134`, `135`, `136`, `137`, `138`, `139`, `140`, `141`, `142`, `143`, `144`, `145`, `146`, `147`, `148`, `149`, `150`, `151`, `152`, `153`, `154`, `155`, `156`, `157`, `158`, `159`, `160`, `161`, `162`, `163`, `164`, `165`, `166`, `167`, `168`, `169`, `170`, `171`, `172`, `173`, `174`, `176`, `177`, `178`, `179`, `180`, `181`, `182`, `183`, `184`, `185`, `186`, `187`, `188`, `189`, `190`, `191`, `192`, `193`, `194`, `195`, `196`, `197`, `198`, `199`, `200`, `201` _(+254 more)_

### `state` — text

- **Declared type:** `text`
- **Nullable:** False · **Null %:** 0.0%
- **Rows:** 2,489,661 · **Distinct:** 28 (0.0% of non-null)
- **Flags:** LOW-CARDINALITY (categorical)
- **Range:** min=`AK` · max=`WA`
- **Length:** min=2 · max=2 · avg=2.0
- **All distinct values (28):** `AK`, `AZ`, `CA`, `CO`, `CT`, `DC`, `DE`, `FL`, `IL`, `MA`, `MD`, `ME`, `MI`, `MN`, `MO`, `MT`, `NJ`, `NM`, `NV`, `NY`, `OH`, `OK`, `OR`, `PA`, `RI`, `VA`, `VT`, `WA`

## Sample rows

| date | category | brand | company | revenue | quantity | sku_count | state |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-04-12 | Preroll | Green Mountain Kana | Wildlegacy-Cannabis | 0 | 1 | 1 | VT |
| 2026-04-12 | Preroll | Green Mountain Sativa | Luckyyoucannabis | 0 | 3 | 1 | VT |
| 2026-04-12 | Preroll | Green Mountain Sativa | Somethingwickedcannabis | 30 | 130 | 6 | VT |
| 2026-04-12 | Preroll | Green Mountain Sativa | Winooskiorganics | 36 | 11 | 1 | VT |
| 2026-04-12 | Preroll | Green Mountain Scientific | Capitalcannabisvt | 67.2 | 98 | 4 | VT |

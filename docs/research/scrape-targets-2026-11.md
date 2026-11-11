# Scrape targets survey (checked 11 Nov 2026)

A survey of HK listing sites, bank rate pages and bank valuation tools, done with plain GET requests from a non-HK sandbox on 2026-11-11. Sites may behave differently from GitHub Actions runners (datacenter IPs) or from a home connection. Re-test each target from the environment that will actually run the scraper.

## Listing platforms

| Site | Reachable? | Notes |
| --- | --- | --- |
| **Midland** | Yes, no bot protection | The estate page's server-rendered `__NEXT_DATA__` JSON holds estate-level aggregates. robots.txt allows it. **Recommended primary source.** |
| **Centaline** | Yes (server-rendered Nuxt) | Listing cards show saleable area and price or rent in the HTML. Estate pages include Land Registry transactions and the median rent. `crawl-delay: 1`. **Cross-check source.** |
| 28Hse | Cloudflare challenge (403) from the sandbox | Worked in the week 6 class exercise, so it may work from HK or home IPs. Untested from GitHub Actions. |
| Spacious, Squarefoot | Cloudflare block (403) | Not usable. |

### Midland

- Estate page: `https://www.midland.com.hk/zh-hk/estate/新界-第一城-石門-沙田第一城-E00012`. Taikoo Shing is `E00024`. All estate URLs are in the sitemap `https://res.midland.com.hk/sitemap/estate_detail_sitemap_0.xml`.
- `props.pageProps.result.estateData` contains `sell_count`, `rent_count`, `avg_net_ft_price` (average saleable $/ft²), `avg_net_ft_rent`, `min_rent` and `max_rent`.
- It also has `market_stat` (from transactions: `net_ft_price`, `net_ft_rent`, `tx_count`, `net_ft_price_chg`), `market_stat_by_room` (average price and rent per ft² by bedroom count), the min/max saleable area and the latest Land Registry transaction.
- The sale and rent list pages load by JS from `data.midland.com.hk/search/v2/properties`, which needs a page-embedded JWT. Avoid them: the estate page alone is enough.
- robots.txt blocks only `/property-news/author/` and two new-property paths.

### Centaline

- Sale list: `https://hk.centanet.com/findproperty/list/buy/太古城`. Rent list: `https://hk.centanet.com/findproperty/list/rent/太古城`. 24 cards per page.
- Estate history page, e.g. `https://hk.centanet.com/estate/太古城-翠湖台/2-OVDUURFSCJ`. It shows Land Registry transactions (date, unit, price, saleable area, saleable $/ft²), 10-month $/ft² ranges and the median monthly rent.
- robots.txt disallows `/centanetapi/api/` and `/estate/hkChartAPi/PropertyPrice/GetAvgPrice`, so do not call those.
- Each list card has `.title-lg` (estate and court), `.usable-area` ("實用 實 702 呎 702呎 @ $21,082 /呎") and `.price-info`. `rentorbuy/scrapers/centaline.py` keeps cards whose title starts with the estate name and takes the median $/ft.
- `/findproperty/list/transaction/<estate>` returns the page frame but no rows: they load by JavaScript from the disallowed API. So from Centaline we only get **asking** prices.
- On 12 Nov 2026, Taikoo Shing's median asking price was $18,804/ft against Midland's transaction figure of $16,256/ft (+16%). Rent: $48.5/ft asking against $46.6/ft. Asking prices overstate the price, which favours renting.

## Bank rate pages

No bank's HTML states the H-plan spread, cap or cash rebate as numbers; those are in Key Facts Statement PDFs (HSBC's robots.txt disallows PDFs). Plan terms will have to be entered by hand from the KFS documents.

| Bank | Prime / best lending rate | HKD time deposits | robots.txt |
| --- | --- | --- | --- |
| HSBC | `https://www.hsbc.com.hk/investments/market-information/hk/lending-rate/` (HTML, 5.00% since 31 Oct 2025) | `https://www.hsbc.com.hk/investments/market-information/hk/deposit-rate/` (HTML) | HTML allowed, PDFs disallowed |
| BOCHK | `https://www.bochk.com/whk/rates/hkDollarPrimeRate/hkDollarPrimeRate-enquiry.action?lang=en` (HTML, 5.00%) | `https://www.bochk.com/whk/rates/depositRates/depositRates-input.action?lang=en` (HTML) | none (404) |
| Standard Chartered | not found | `https://www.sc.com/hk/deposits/board-rates/` (HTML; was marked "As at 5 June 2026", so may be stale) | `/hk/` allowed |
| Hang Seng | JS-filled; JSON at `https://rbwm-api.hsbc.com.hk/pws-hk-hase-rates-papi-prod-proxy/v1/hkd-prime-rates` (works with a plain GET; field `rate`) | `…/interest-rates` (not called) | rate paths allowed |

On 2026-11-11 HSBC, BOCHK and SC all showed HKD 3M 0.125% and 12M 0.150%.

## HKD time deposits for new funds (checked 12 Nov 2026)

All five read with a plain GET; parsed by `rentorbuy/scrapers/deposits.py`.

| Bank | Page | Where the rates are |
| --- | --- | --- |
| HSBC | `https://www.hsbc.com.hk/accounts/offers/deposits/` | One table per tier and currency; HKD tables' caption says "Minimum deposit amount: HKD…". Rates are "equivalent" rates that include RewardCash. 3 and 6 months only. |
| BOCHK | `https://www.bochk.com/en/deposits/promotion/timedeposits.html` | One table; the currency cell spans rows. No 12-month HKD rate. |
| Standard Chartered | `https://www.sc.com/hk/deposits/online-time-deposit/` | Table headed "New funds of HKD10,000 or above". |
| Mox | `https://mox.com/promotions/time-deposit/` | Table after "HKD New Funds Time Deposit". |
| eleBank | `https://www.elebank.com/vendor/json/deposit_rate.json` | JSON, `rate_type` "Time Deposit Rate" (week 6 exercise). |

Hang Seng's promotions depend on balance growth and are not a plain rate; ZA Bank shows rates only in its app.

## Bank property-valuation tools

| Bank | Usable? | Returns area? |
| --- | --- | --- |
| **HSBC** | Yes, tested | Yes: `saleableArea`, `grossFloorArea`, `propAge` |
| **Hang Seng** | Endpoints found in JS, not called | Yes: `saleableArea`, `grossArea`, `valuation`, `valuationDate` |
| **DBS** | Endpoints found in JS, not called (Cushman & Wakefield hosted) | Yes: `netarea`, `grossarea`, `price` |
| BOCHK | No: CAPTCHA-protected form | n/a |
| Standard Chartered, BEA | No endpoint found | n/a |

### HSBC (tested)

- Valuation: POST `https://rbwm-api.hsbc.com.hk/digital-pws-tools-mortgages-eapi-prod-proxy/v1/mortgages/property-valuation` with `{locale, zoneId, districtId, estateId, blockId, floor, flat}`, all values as strings.
- Example response: `{"propAddr":"Flat G,7/F,Phase 1 Block/Tower 2,Discovery Park,Tsuen Wan,New Territories/Island","valn":"6750000","grossFloorArea":"610","saleableArea":"491","propAge":29,"valnDt":"2026-11-11 22:08:22 +0800"}`
- Lookup chain: POST `…/v1/mortgages/property-valuation-tool` with `{locale, locate, zoneId, districtId, estateId, blockId, floor}`. Every key must be present (use `null` for levels not chosen); leaving keys out gives a 404.
  - `locate` names the level just chosen: `null` → zones, `"zone"` → districts, `"district"` → estates, `"estate"` → blocks, `"block"` → floors, `"floor"` → flats.
  - The response key is `zoneList`, `districtList`, `estateList`, `blockList`, `floorList` or `flatList`. Each item is `{id, name}`; `id` may be `"N/A"`.
- Keyword search: POST `…/v1/mortgages/property-valuation-address` with `{locale, zoneId, estateKeyword}`. Tseung Kwan O estates are in zone 3 (New Territories), not Kowloon as on Midland. Our 27 estates' ids are in `data/hsbc_estates.json`.
- Valuations are supplied by Cushman & Wakefield.
- Known flakiness: about 1 in 4 calls returns a random 404, so retry with backoff (week 6 exercise).
- Browser access: a CORS preflight from another site (`Origin: https://lohk2016.github.io`) returned `Access-Control-Allow-Origin: *` on 2026-11-11, so a web page on any domain can call it directly.

### Hang Seng (not called)

- Address search page: `https://www.hangseng.com/en-hk/e-valuation/address-search/`.
- GET `{papiUrl}/pws-hk-hase-mortgage-eapi-prod-proxy/v1/property/area2blockfulllist` returns the whole area→block tree. Then call `/property/floor?blockcode=` and `/property/flat?blockcode=&floorcode=`.
- POST `/property/valuation` with `{area, district, estate, block, floor, flat, carpark, openCarpark, tcKnowledge}`.
- `papiUrl` is probably `rbwm-api.hsbc.com.hk`; not confirmed.

### DBS (not called)

- `http://go.dbs.com/hk-evaluation-en` redirects to `https://evalhk.cushmanwakefield.com.hk/e-valuation/DBSV2/Home/Index/en`.
- Form POST `/e-valuation/DBSV2/Home/SelectJson` with `{lancode, fid, group:"#inputselect_<level>", floor, bloid}` returns `[{id, name}]`. At flat level it returns `grossarea`, `netarea`, `price`, `opyear` and `opmonth`.

# Live data sources: how to call them, and what went wrong

Read this before calling any live API or website from your own machine (HKMA, Midland, a bank's rate page or valuation tool).

## How to call them

- **Work from the snapshot.** While building or debugging, read `data/latest.json` (or a dated `data/<date>/snapshot.json`). It holds everything the scrapers fetch, so most work needs no live call at all.
- **One call to check a shape.** When you must see a live response, make one request, save it to a file, and work from the file.
- **Retries are for flaky endpoints only.** Retry with a growing wait (as in `rentorbuy/scrapers/hkma.py`) when a site fails at random, like HSBC's valuation API. A run of identical errors (403, 405, 429) is a block: stop, and try again hours later.
- **Log every burst here.** Write down the date, the endpoint, how many requests and what came back, so the next person knows what each source tolerates.

## Midland from GitHub Actions: refused on 2026-11-11

Midland answers GitHub's servers with **403 Forbidden** on every estate page; from a home connection in Hong Kong the same pages work. HKMA answered the same run normally.

| Time (UTC) | Who | Requests | Result |
| --- | --- | --- | --- |
| 11 Nov 15:28 | `daily.py` from home | 27 Midland pages | all 200 |
| 11 Nov 16:27 | `scrape.yml` on GitHub Actions | 27 Midland pages | all **403** (the scraper did not yet stop at the first one) |
| 11 Nov 16:27 | `scrape.yml` on GitHub Actions | 2 HKMA | 200 |
| 11 Nov 16:31 | `scrape.yml` again, after the fix | 1 Midland, 2 HKMA | Midland 403 (stopped there); HKMA HIBOR 200, prime **405** |

| 12 Nov 00:36 HKT | `curl` from home, one estate page with an `Origin` header | 1 Midland | 200, but no `Access-Control-Allow-Origin`: a browser on our site cannot read Midland |
| 12 Nov 00:37 HKT | one-off scrape of 灝景灣 from home | 1 Midland, 1 HSBC search | both 200 |

| 12 Nov 00:57 HKT | `curl` from home, each bank's prime-rate page once (saved as test fixtures) | HSBC, BOCHK, Hang Seng: 1 each | all 200 |

| 12 Nov 01:12 HKT | `curl` from home, each time-deposit offer page once (saved as test fixtures) | HSBC, BOCHK, Standard Chartered, Mox, eleBank JSON: 1 each | all 200 |

| 12 Nov 03:12 HKT | `rentorbuy.scrapers.etf` from home, yfinance, whole monthly history | Yahoo Finance: 2 tickers (2800.HK, SPY), a few requests each | both fine; saved to `data/etf/`. Yahoo has 2800.HK monthly prices only from 2008-01 |

| 12 Nov 05:04 HKT | temporary `probe-centaline.yml` on GitHub Actions (branch `probe/centaline`, since deleted) | 1 Centaline list page | **200**, full page (640 KB): Centaline answers GitHub's servers. (A first run pushed at 04:21 sat queued and never started.) |
| 12 Nov 05:18 HKT | `scrape.yml` on GitHub Actions, run by hand | 1 Midland, 54 Centaline (27 estates × buy and rent), 2 s apart | Midland **403** (stopped there); Centaline all 200 |
| 12 Nov 04:26–04:28 HKT | `curl` from home: Taikoo Shing buy list, rent list, transaction list (first two saved as test fixtures) | 3 Centaline | all 200; the transaction list's rows load by JavaScript from the disallowed API, so the HTML has none |

GitHub's runners share IP addresses with many other users, so HKMA's limit may already be used up by others. `daily.py` now fetches HIBOR and prime separately, so one refusal keeps the other fresh.

What we changed: `midland.scrape_all()` now stops at the first 403, 405 or 429, and `daily.py` keeps each Estate's last figures (with their date) while still saving fresh rates. Since 12 Nov, an Estate Midland misses takes Centaline's median asking prices instead (`rentorbuy/scrapers/centaline.py`), and keeps its last figures only if Centaline fails too.

## HSBC valuation tool: 2026-11-11 to 12, no problems

About 1 call in 4 gets a random 404 (expected; we retry). No 403, 405 or 429.

| Time (UTC) | Who | Requests | Result |
| --- | --- | --- | --- |
| 11 Nov, before 14:13 | survey subagent | 1 valuation | 200 |
| 15:55 | `curl`, CORS preflight (OPTIONS) | 1 | 200, `Access-Control-Allow-Origin: *` |
| 15:58–16:00 | `curl` and a probe script, learning the request shapes | 9 | 7 × 200, 2 × 404 |
| 16:01 | `hsbc_estates.py`, first run | 27 keyword searches | all 200 (4 estates not found in Midland's zone) |
| 16:02 | `hsbc_estates.py`, the 4 missing estates in other zones | 12 | all 200 |
| ~16:10 | the website in the browser, one flat picked | about 4 (blocks, floors, flats, valuation) | worked |

## HKMA open API: blocked on 2026-11-11

`api.hkma.gov.hk` started answering **HTTP 405 "Not Allowed"** to every request from one home connection after about 20 requests in two hours. The same requests had worked minutes earlier, and the block was still in place 30 minutes later. We do not know HKMA's limit or how long the block lasts.

| Time (UTC) | Who | Requests | Result |
| --- | --- | --- | --- |
| 14:07 | research subagent | 5, one per endpoint, in a loop | all 200 |
| 15:26 | `curl`, checking field names | 2 | 200 |
| 15:26 | `hkma.get_rates()` | 2 | 200 |
| 15:27 | `daily.py`, first run | 1 | **405** |
| 15:27 | `curl` loop, "is it random?" | 3 | 405 |
| 15:28 | `curl` with 4 different User-Agents | 4 | 405 |
| 15:28 | `daily.py` with 3 retries | 3 | 405 |
| 15:55 | `curl`, "has it recovered?" | 1 | 405 |

Total: 21 requests, 9 answered, then 12 refused. The last 12 did nothing but prolong the block. Trying other User-Agents in particular was the wrong move: it looks like evading a block.

What we changed:

- `daily.py` falls back to the last saved rates and marks them `"stale": true`; the site then says the rates are not today's.
- The daily GitHub Actions job makes 2 HKMA requests a day, from GitHub's IP addresses, not ours.

Still to find out: whether GitHub's runners are allowed, and when this connection is unblocked. Add the answer to the table above.

## RVD price and rent index CSVs: 2026-11-25, no problems

`rentorbuy/market_benchmarks.py` reads two monthly CSVs from the Rating and Valuation Department's open data: `1.4M.csv` (private domestic price indices) and `1.3M.csv` (rent indices). They are static files, updated once a month. The daily job fetches both every morning.

| Time (UTC) | Who | Requests | Result |
| --- | --- | --- | --- |
| 24 Nov, around PR #5 | the PR author, while building `market_benchmarks.py` | not logged | worked |
| 24 Nov 19:22 | `curl` from home, each CSV once with `USER_AGENT` (saved as `tests/fixtures/rvd_1.4M.csv` and `rvd_1.3M.csv`) | 2 | both 200, about 25 KB each, data to 09-2026 |

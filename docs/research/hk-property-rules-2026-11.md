# HK property rules and data sources (checked 11 Nov 2026)

Researched from official sources on 2026-11-11. Re-check before relying on it after a Budget (late February) or an HKMA announcement.

## 1. Stamp duty (AVD) on residential purchases by individuals

Scale 2 and Part 1 of Scale 1 have had identical rates since 28 Feb 2024, so the duty is the same for permanent and non-permanent residents, and for first-time and other buyers. Duty is charged on the higher of consideration and value. Table in force from 26 Feb 2026 ([IRD AVD FAQ Q1](https://www.ird.gov.hk/eng/faq/avd.htm)):

| Value (HK$) | Duty |
| --- | --- |
| up to 4,000,000 | $100 |
| 4,000,001 – 4,323,780 | $100 + 20% of excess over 4M |
| 4,323,781 – 4,500,000 | 1.5% |
| 4,500,001 – 4,935,480 | $67,500 + 10% of excess over 4.5M |
| 4,935,481 – 6,000,000 | 2.25% |
| 6,000,001 – 6,642,860 | $135,000 + 10% of excess over 6M |
| 6,642,861 – 9,000,000 | 3.00% |
| 9,000,001 – 10,080,000 | $270,000 + 10% of excess over 9M |
| 10,080,001 – 20,000,000 | 3.75% |
| 20,000,001 – 21,739,120 | $750,000 + 10% of excess over 20M |
| 21,739,121 – 100,000,000 | 4.25% |
| 100,000,001 – 109,574,470 | $4,250,000 + 30% of excess over 100M |
| 109,574,471 and above | 6.5% |

- The $100 band rose from $3M to $4M on 26 Feb 2025 ([Budget 2025-26 para 228](https://www.budget.gov.hk/2025/eng/budget46.html)).
- The top rate went from 4.25% to 6.5% above $100M on 26 Feb 2026 ([Budget 2026-27 para 261(a)](https://www.budget.gov.hk/2026/eng/budget51.html)).
- BSD, SSD and NRSD were abolished for agreements on or after 28 Feb 2024 ([IRD notice](https://www.ird.gov.hk/eng/ppr/archives/24022808.htm)). The IRD's BSD FAQ page still shows the old rates; it is out of date.

## 2. HKMA loan-to-value cap

- Since 16 Oct 2024 the maximum LTV is **70% for every residential property**, whatever its value, use or the buyer's other mortgages ([press release](https://www.info.gov.hk/gia/general/202410/16/P2024101600258p.htm), [HKMA table](https://www.hkma.gov.hk/media/eng/doc/other-information/FAQ_table_(e).pdf)).
- The maximum mortgage term is 30 years.
- The cut for income mainly from outside HK was lifted on 7 Jul 2023.

## 3. HKMC Mortgage Insurance Programme (agreements on or after 16 Oct 2024)

Source: [HKMC MIP page](https://www.hkmc.com.hk/eng/our_business/mortgage_insurance_programme.html).

| Property value | Max LTV with insurance |
| --- | --- |
| up to $10M | 80%, or 90% |
| over $10M to under $11.25M | 80–90%, with a $9M loan cap |
| $11.25M – $15M | 80% |
| over $15M to $17.15M | 70–80%, with a $12M loan cap |

- The highest eligible property value is $17.15M.
- **90% needs every mortgagor to own no HK residential property and every applicant to be salaried.** In effect it is a first-time-buyer limit, and it is the only rule that differs by buyer type. Premium rates also differ.
- Maximum debt-to-income ratio 50%, maximum term 30 years.
- A separate small-flat product (up to $6M): 90% up to $4M; a $3.6M loan cap for $4M–4.5M; 80% (capped at $4.8M) up to $6M.

## 4. DSR and stress test

- The DSR limit is **50%** for all properties since 16 Oct 2024.
- **The stress test has been suspended since 28 Feb 2024** ([press release](https://www.info.gov.hk/gia/general/202402/28/P2024022800267.htm)). It used to assume +200bp.

## 5. Historical price and rent data

[RVD property market statistics](https://www.rvd.gov.hk/en/publications/property_market_statistics.html) are published as `.xls` files (read them with pandas plus xlrd) and updated monthly. The latest file runs to Sep 2026.

| File | Contents | Breakdown | From |
| --- | --- | --- | --- |
| [his_data_4.xls](https://www.rvd.gov.hk/doc/en/statistics/his_data_4.xls) | Price indices (1999=100) | Class A–E, whole territory | monthly Jan 1993 |
| [his_data_3.xls](https://www.rvd.gov.hk/doc/en/statistics/his_data_3.xls) | Rental indices | Class A–E, whole territory | monthly Jan 1993 |
| [his_data_2.xls](https://www.rvd.gov.hk/doc/en/statistics/his_data_2.xls) | Average prices $/m² | Class × HK Island / Kowloon / NT | 1982 |
| [his_data_1.xls](https://www.rvd.gov.hk/doc/en/statistics/his_data_1.xls) | Average rents $/m² | Class × region | 1982 |
| [his_data_5.xls](https://www.rvd.gov.hk/doc/en/statistics/his_data_5.xls) | Price index, selected popular developments | Urban / NT, by size | 1992 |

- Classes by saleable area: A <40 m², B 40–69.9, C 70–99.9, D 100–159.9, E ≥160.
- First-hand sales are excluded from these figures.
- There is no free official price history for individual estates.
- The Centa-City Leading Index (weekly, commercial) can be viewed at [hk.centanet.com/CCI](https://hk.centanet.com/CCI/index). Bulk download and reuse terms could not be confirmed.

## 6. HKMA open API (tested, JSON)

The API blocked us after about 20 requests on 2026-11-11. Read `docs/research/api-access-log.md` before calling it.

| Data | Endpoint | Field | Updated |
| --- | --- | --- | --- |
| Daily 1-month HIBOR | [daily-figures-interbank-liquidity](https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity) | `hibor_fixing_1m` (2.59452 on 2026-11-11) | daily |
| Interbank rates, overnight to 12 months | [hk-interbank-ir-daily](https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily) | `ir_overnight` … `ir_12m` | monthly |
| Best lending (prime) rate | [hkd-ir-effdates](https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hkd-ir-effdates) | `best_lending_rate` (5.000% since 2025-10-31) | when it changes |

- Page through results with the `pagesize` and `offset` query parameters.
- The prime-rate endpoint does not say which bank's rate it is. Check [apidocs.hkma.gov.hk](https://apidocs.hkma.gov.hk/) before relying on it.

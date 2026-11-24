import type { ReactNode } from "react"
import { SCENARIO_NAMES, type BankPlan, type Estate, type Flat, type ForecastReply, type Result, type Snapshot } from "@/lib/types"
import { STRINGS, translate, type Lang } from "@/i18n"
import { money, percent, shortMoney } from "@/lib/format"

type Props = {
  lang: Lang
  estate: Estate
  data: Snapshot
  flat: Flat | null
  /** What rentorbuy.compare_forecast returned; the report shows its middle (neutral) result in detail. */
  reply: ForecastReply
  plan: BankPlan
  prime: number
  primeChoice?: "h" | "small" | "big"
  primeBank?: string
  bankPrimeDate?: string
  investmentSource: string
}

function NetWorthFigure({ result, lang }: { result: Result; lang: Lang }) {
  const width = 720
  const height = 220
  const left = 72
  const right = 704
  const top = 16
  const bottom = 178
  const values = [...result.buy_net_worth, ...result.rent_net_worth]
  const low = Math.min(...values)
  const high = Math.max(...values)
  const padding = (high - low) * 0.08 || Math.max(high * 0.08, 1)
  const min = low - padding
  const max = high + padding
  const range = max - min
  const x = (index: number) => left + (right - left) * index / Math.max(result.years.length - 1, 1)
  const y = (value: number) => bottom - (bottom - top) * (value - min) / range
  const points = (values: number[]) => values.map((value, index) => `${x(index)},${y(value)}`).join(" ")
  const t = (key: Parameters<typeof translate>[1], replacements?: Record<string, string | number>) =>
    translate(lang, key, replacements)

  return (
    <figure className="report-chart">
      <figcaption className="report-section-title">{t("reportChart")}</figcaption>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={t("reportChart")}>
        {[0, 0.5, 1].map((fraction) => {
          const value = max - range * fraction
          const position = top + (bottom - top) * fraction
          return (
            <g key={fraction}>
              <line x1={left} x2={right} y1={position} y2={position} className="report-grid-line" />
              <text x={left - 8} y={position + 4} textAnchor="end" className="report-axis-label">
                {shortMoney(value, lang)}
              </text>
            </g>
          )
        })}
        <line x1={left} x2={right} y1={bottom} y2={bottom} className="report-axis-line" />
        <polyline points={points(result.buy_net_worth)} className="report-buy-line" />
        <polyline points={points(result.rent_net_worth)} className="report-rent-line" />
        <text x={left} y={bottom + 20} className="report-axis-label">{t("year", { n: result.years[0] })}</text>
        <text x={right} y={bottom + 20} textAnchor="end" className="report-axis-label">
          {t("year", { n: result.years[result.years.length - 1] })}
        </text>
      </svg>
      <div className="report-legend">
        <span><i className="report-buy-dot" />{t("reportFinalBuy")}</span>
        <span><i className="report-rent-dot" />{t("reportFinalRent")}</span>
      </div>
    </figure>
  )
}

function ReportRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="report-row">
      <span>{label}</span>
      <strong>{children}</strong>
    </div>
  )
}

export function PdfReport({
  lang,
  estate,
  data,
  flat,
  reply,
  plan,
  prime,
  primeChoice = "h",
  primeBank = plan.bank,
  bankPrimeDate,
  investmentSource,
}: Props) {
  const t = (key: Parameters<typeof translate>[1], replacements?: Record<string, string | number>) =>
    translate(lang, key, replacements)
  const result = reply.results.neutral
  const used = result.inputs
  // Python's outcome_range: the smallest and largest gap, and who leads in every scenario.
  const { verdict, low_gap: lowGap, high_gap: highGap } = reply.range
  const short = (n: number) => shortMoney(Math.abs(n), lang)
  const rangeText =
    verdict === "buy"
      ? t("outcomeIntervalBuy", { low: short(lowGap), high: short(highGap), years: used.horizon_years })
      : verdict === "rent"
        ? t("outcomeIntervalRent", { low: short(highGap), high: short(lowGap), years: used.horizon_years })
        : t("outcomeIntervalMixed", { rentLead: short(lowGap), buyLead: short(highGap), years: used.horizon_years })
  const buyEnd = result.buy_net_worth[result.buy_net_worth.length - 1]
  const rentEnd = result.rent_net_worth[result.rent_net_worth.length - 1]
  const estateName = lang === "en" ? estate.name_en : estate.name_zh
  const location = lang === "en"
    ? `${estate.district_en}, ${estate.region_en}`
    : `${estate.region_zh} · ${estate.district_zh}`
  const prepared = new Date().toLocaleDateString(lang === "zh-Hant" ? "zh-HK" : "en-GB", {
    year: "numeric",
    month: "long",
    day: "numeric",
  })
  const winner = t(result.verdict === "buy" ? "reportFinalBuy" : "reportFinalRent")

  return (
    <article className="pdf-report" aria-label={t("reportTitle")}>
      <header className="report-header">
        <div>
          <p className="report-eyebrow">{t("title")}</p>
          <h1>{t("reportTitle")}</h1>
          <p className="report-property">
            {estateName} · {location} · {t(flat ? "reportSpecificFlat" : "reportTypicalFlat")}
            {flat && <> · {flat.address}</>}
          </p>
          <p className="report-date">{t("reportPrepared", { date: prepared })}</p>
        </div>
        <span className="report-scenario">{t("marketBenchmarkLabel")}</span>
      </header>

      <section className={`report-verdict report-verdict-${verdict}`}>
        <div>
          <h2>{t(verdict === "buy" ? "buyWins" : verdict === "rent" ? "rentWins" : "dependsOnMarket")}</h2>
          <p>{rangeText}</p>
          <p className="report-label">{t("reportOutcome", { years: used.horizon_years })}</p>
          <p>{t("reportAdvantage", { choice: winner, amount: money(Math.abs(result.gap)) })}</p>
          <p className="report-break-even">
            {result.break_even_year !== null
              ? t("breakEven", { year: result.break_even_year })
              : t("neverBreakEven", { years: used.horizon_years })}
          </p>
        </div>
        <div className="report-final-values">
          <div><span>{t("reportFinalBuy")}</span><strong>{money(buyEnd)}</strong></div>
          <div><span>{t("reportFinalRent")}</span><strong>{money(rentEnd)}</strong></div>
        </div>
      </section>

      <NetWorthFigure result={result} lang={lang} />

      <section className="report-section">
        <h2 className="report-section-title">{t("reportScenarios")}</h2>
        <div className="report-scenarios">
          {SCENARIO_NAMES.map((name) => {
            const scenarioResult = reply.results[name]
            const growth = reply.scenarios[name]
            const scenarioWinner = t(scenarioResult.verdict === "buy" ? "reportFinalBuy" : "reportFinalRent")
            return (
              <div className={`report-scenario-card${name === "neutral" ? " report-selected" : ""}`} key={name}>
                <span>{t(name)} · {`${growth.price_growth}% / ${growth.rent_growth}%`}</span>
                <strong>{scenarioWinner}</strong>
                <small>{t("reportAdvantage", {
                  choice: scenarioWinner,
                  amount: money(Math.abs(scenarioResult.gap)),
                })}</small>
              </div>
            )
          })}
        </div>
      </section>

      <section className="report-section report-page-break">
        <h2 className="report-section-title">{t("reportInputs")}</h2>
        <div className="report-columns">
          <div className="report-panel">
            <ReportRow label={t("reportPurchasePrice")}>{money(used.price)}</ReportRow>
            {flat && (
              <>
                <ReportRow label={t("valuation")}>{money(flat.valuation)}</ReportRow>
                <ReportRow label={t("reportValuationDate")}>{flat.date}</ReportRow>
              </>
            )}
            <ReportRow label={t("reportMonthlyRent")}>{money(used.monthly_rent)}</ReportRow>
            <ReportRow label={t("reportSaleableArea")}>{`${used.saleable_area} ${t("sqft")}`}</ReportRow>
            <ReportRow label={t("reportMortgageRate")}>{percent(used.mortgage_rate / 100, 2)}</ReportRow>
            <ReportRow label={t("reportLoanToValue")}>{percent(used.ltv, 0)}</ReportRow>
            <ReportRow label={t("reportInvestmentReturn")}>{percent(used.investment_return / 100, 2)}</ReportRow>
            <ReportRow label={t("reportMortgageTerm")}>{`${used.mortgage_years} ${t("years")}`}</ReportRow>
            <ReportRow label={t("reportGrowth")}>
              {`${used.price_growth}% / ${used.rent_growth}%`}
            </ReportRow>
            <ReportRow label={t("reportBuyer")}>
              {t(used.first_time ? "reportFirstTimeBuyer" : "reportOtherBuyer")}
            </ReportRow>
            {used.monthly_income !== null && (
              <ReportRow label={t("income")}>{money(used.monthly_income)}</ReportRow>
            )}
            <p className="report-small-note">{investmentSource}</p>
          </div>
          <div className="report-panel">
            <h3>{t("reportUpfront")}</h3>
            <ReportRow label={t("downPayment")}>{money(result.upfront.down_payment)}</ReportRow>
            <ReportRow label={t("stampDuty")}>{money(result.upfront.stamp_duty)}</ReportRow>
            <ReportRow label={t("agentFee")}>{money(result.upfront.agent_fee)}</ReportRow>
            <ReportRow label={t("legalFee")}>{money(result.upfront.legal_fee)}</ReportRow>
            <ReportRow label={t("insurance")}>{money(result.upfront.insurance_premium)}</ReportRow>
            {result.upfront.cash_rebate > 0 && (
              <ReportRow label={t("cashRebate")}>−{money(result.upfront.cash_rebate)}</ReportRow>
            )}
            <ReportRow label={t("reportCashNeeded")}>{money(result.upfront.total_cash)}</ReportRow>
            <ReportRow label={t("reportLoan")}>{money(result.upfront.loan)}</ReportRow>
          </div>
        </div>
      </section>

      <section className="report-section">
        <h2 className="report-section-title">{t("reportFirstYearCosts")}</h2>
        <div className="report-columns">
          <div className="report-panel">
            <ReportRow label={t("repayment")}>{money(result.yearly_costs[0].mortgage)}</ReportRow>
            <ReportRow label={t("managementFee")}>{money(result.yearly_costs[0].management_fee)}</ReportRow>
            <ReportRow label={t("rates")}>{money(result.yearly_costs[0].rates)}</ReportRow>
            <ReportRow label={t("governmentRent")}>{money(result.yearly_costs[0].government_rent)}</ReportRow>
            <ReportRow label={t("repairs")}>{money(result.yearly_costs[0].repairs)}</ReportRow>
            <ReportRow label={t("reportOwnerMonthly")}>{money(result.yearly_costs[0].owner_monthly)}</ReportRow>
            <ReportRow label={t("reportTenantMonthly")}>{money(result.yearly_costs[0].rent_monthly)}</ReportRow>
          </div>
          <div className="report-panel">
            <h3>{t("reportReference")}</h3>
            <ReportRow label={t("rentalYield")}>{percent(result.rental_yield, 2)}</ReportRow>
            {result.debt_servicing_ratio !== null && (
              <ReportRow label={t("dsr")}>{percent(result.debt_servicing_ratio, 0)}</ReportRow>
            )}
            {result.dsr_too_high && <p className="report-warning">{t("dsrTooHigh")}</p>}
          </div>
        </div>
      </section>

      <section className="report-section">
        <h2 className="report-section-title">{t("reportBankRate")}</h2>
        <div className="report-panel">
          <p>{plan.bank}{plan.provisional ? ` · ${t("provisional")}` : ""}</p>
          <p>
            {primeChoice === "h"
              ? t("rateFormula", {
                  hibor: data.rates.hibor_1m.toFixed(2),
                  spread: plan.hibor_spread,
                  prime: prime.toFixed(2),
                  discount: plan.prime_discount,
                })
              : t("pRateFormula", { prime: prime.toFixed(2) })}
          </p>
          <p>
            {bankPrimeDate
              ? t("primeFromBank", { bank: primeBank, date: bankPrimeDate })
              : t("primeFromHkma")}
          </p>
        </div>
      </section>

      <section className="report-section">
        <h2 className="report-section-title">{t("reportMethod")}</h2>
        <ul className="report-list">
          {STRINGS[lang].how.map((line) => <li key={line}>{line}</li>)}
        </ul>
      </section>

      <section className="report-section">
        <h2 className="report-section-title">{t("reportAssumptions")}</h2>
        <ul className="report-list">
          {STRINGS[lang].limits.map((line) => <li key={line}>{line}</li>)}
        </ul>
      </section>

      <section className="report-section">
        <h2 className="report-section-title">{t("reportData")}</h2>
        <div className="report-data">
          <p><strong>{t("reportDataDate")}:</strong> {data.date}</p>
          <p>
            {estate.price_source === "centaline"
              ? t("dataEstateCentaline", { date: estate.scraped ?? data.date })
              : `${t("dataEstate", { date: estate.scraped ?? data.date })}${
                  (estate.scraped ?? data.date) !== data.date ? ` ${t("dataEstateStale")}` : ""
                }`}
          </p>
          {flat && <p>{t("dataHsbc")}</p>}
          <p>
            {t("dataRates", { date: data.rates.hibor_date })}
            {data.rates.stale ? ` ${t("dataStale")}` : ""}
          </p>
          {bankPrimeDate && <p>{t("primeFromBank", { bank: primeBank, date: bankPrimeDate })}</p>}
          {data.etf_returns?.SPY && <p>{t("dataEtf", { date: data.etf_returns.SPY.prices_to })}</p>}
          {reply.source === "forecast" && data.market_benchmark && (
            <p>
              {t("dataForecast", {
                from: data.market_benchmark.price.history_from,
                to: data.market_benchmark.price.history_to,
                low: data.market_benchmark.price.past_ten_year_growth.low,
                high: data.market_benchmark.price.past_ten_year_growth.high,
              })}
            </p>
          )}
          <p>{investmentSource}</p>
          <p>{t("dataManual")}</p>
        </div>
      </section>

      <footer className="report-footer">
        <span>{t("footer")}</span>
        <span>{t("reportPage")}</span>
      </footer>
    </article>
  )
}

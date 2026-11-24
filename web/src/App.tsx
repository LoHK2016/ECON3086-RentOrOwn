import { useEffect, useMemo, useState } from "react"
import { AlertTriangle, ExternalLink, FileDown } from "lucide-react"
import { DepositRanking } from "@/components/DepositRanking"
import { FlatPicker } from "@/components/FlatPicker"
import { NetWorthChart } from "@/components/NetWorthChart"
import { Affordability } from "@/components/Affordability"
import { PdfReport } from "@/components/PdfReport"
import { NumberField, Row, Section, Segmented, digits, parsed } from "@/components/grouped"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { LANGUAGES, STRINGS, defaultLang, translate, type Lang } from "@/i18n"
import { money, percent, shortMoney } from "@/lib/format"
import { compareForecast, loadCalculator } from "@/lib/python"
import type { Estate, Flat, ForecastReply, Snapshot } from "@/lib/types"
import { cn } from "@/lib/utils"

type Shift = "-1" | "0" | "1"
type InvestMode = "deposit" | "hk" | "us" | "custom"
type PrimeChoice = "h" | "small" | "big"
type Tool = "comparison" | "affordability"

// The ETF behind each stock choice (returns worked out in rentorbuy/etf_returns.py).
const ETF_TICKER = { hk: "2800.HK", us: "SPY" } as const
const P_RATE_BANKS = { small: "HSBC", big: "BOCHK" } as const
const PRIME_SOURCE_URLS: Record<string, string> = {
  HSBC: "https://www.hsbc.com.hk/investments/market-information/hk/lending-rate/",
  BOCHK: "https://www.bochk.com/whk/rates/hkDollarPrimeRate/hkDollarPrimeRate-enquiry.action?lang=en",
  "Hang Seng": "https://rbwm-api.hsbc.com.hk/pws-hk-hase-rates-papi-prod-proxy/v1/hkd-prime-rates",
}

const REGION_ORDER = ["香港島", "九龍", "新界"]
const REGION_SHORT_EN: Record<string, string> = { 香港島: "HK Island", 九龍: "Kowloon", 新界: "New Territories" }

/** The first Estate for each distinct key, keeping their order. */
function unique(estates: Estate[], key: (e: Estate) => string): Estate[] {
  const seen = new Set<string>()
  return estates.filter((e) => !seen.has(key(e)) && seen.add(key(e)))
}

function ProvisionalBadge({ lang }: { lang: Lang }) {
  return (
    <span className="rounded-full bg-warning/15 px-2 py-0.5 text-[11px] font-semibold text-warning">
      {translate(lang, "provisional")}
    </span>
  )
}

export default function App() {
  const [lang, setLang] = useState<Lang>(defaultLang)
  const [tool, setTool] = useState<Tool>("comparison")
  const t = (key: Parameters<typeof translate>[1], values?: Record<string, string | number>) =>
    translate(lang, key, values)

  const [data, setData] = useState<Snapshot | null>(null)
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading")
  const [reply, setReply] = useState<ForecastReply | null>(null)

  // What the user has chosen. Empty strings mean "use the typical value".
  const [estateId, setEstateId] = useState("")
  const [mode, setMode] = useState<"typical" | "specific">("typical")
  const [flat, setFlat] = useState<Flat | null>(null)
  const [area, setArea] = useState("500")
  const [price, setPrice] = useState("")
  const [rent, setRent] = useState("")
  const [valuation, setValuation] = useState("")
  const [firstTime, setFirstTime] = useState(true)
  const [permanent, setPermanent] = useState(true)
  const [income, setIncome] = useState("")
  const [bank, setBank] = useState(0)
  const [primeChoice, setPrimeChoice] = useState<PrimeChoice>("h")
  const [ltv, setLtv] = useState<number | null>(null)
  const [term, setTerm] = useState(30)
  const [shift, setShift] = useState<Shift>("0")
  const [horizon, setHorizon] = useState(10)
  const [invest, setInvest] = useState("")
  const [investMode, setInvestMode] = useState<InvestMode>("deposit")
  const [rebate, setRebate] = useState("")

  useEffect(() => {
    document.documentElement.lang = lang === "zh-Hant" ? "zh-Hant-HK" : "en"
    document.title = STRINGS[lang].title
    try {
      localStorage.setItem("lang", lang)
    } catch {
      // Storage can be blocked; the language just won't be remembered.
    }
  }, [lang])

  useEffect(() => {
    // "no-cache": ask the server each time, so the site never shows yesterday's data.
    const snapshot = fetch(import.meta.env.BASE_URL + "data/latest.json", { cache: "no-cache" }).then((r) => r.json())
    Promise.all([snapshot, loadCalculator()])
      .then(([snap]: [Snapshot, unknown]) => {
        setData(snap)
        setEstateId(snap.estates[0].id)
        setStatus("ready")
      })
      .catch(() => setStatus("error"))
  }, [])

  const estate: Estate | undefined = data?.estates.find((e) => e.id === estateId)
  const plan = data?.bank_plans[bank]
  const primeBank = primeChoice === "h" ? plan?.bank : P_RATE_BANKS[primeChoice]
  // HKMA publishes one unlabelled best-lending rate; the two choices use bank-specific rates.
  const bankPrime = primeBank ? data?.bank_primes?.[primeBank] : undefined
  const prime = bankPrime?.prime ?? data?.rates.prime ?? 0
  const etf = investMode === "hk" || investMode === "us" ? data?.etf_returns?.[ETF_TICKER[investMode]] : undefined
  // The affordability page's rate is worked out in Python (affordability.plan_rate) from these.
  const planRates = useMemo(
    () => ({
      hibor: data?.rates.hibor_1m ?? 0,
      hibor_spread: plan?.hibor_spread ?? 0,
      prime,
      prime_discount: plan?.prime_discount ?? 0,
      p_rate: primeChoice === "h" ? null : prime,
    }),
    [data, plan, prime, primeChoice],
  )

  const inputs = useMemo(() => {
    if (!data || !estate || !plan) return null
    const specific = mode === "specific" && flat ? flat : null
    return {
      saleable_area: specific?.saleable_area ?? parsed(area),
      price_per_ft: estate.price_per_ft,
      rent_per_ft: estate.rent_per_ft,
      price: parsed(price),
      monthly_rent: parsed(rent),
      valuation: parsed(valuation) ?? specific?.valuation,
      first_time: firstTime,
      monthly_income: parsed(income),
      mortgage_rate: primeChoice === "h" ? undefined : prime,
      hibor: data.rates.hibor_1m,
      prime,
      hibor_spread: plan.hibor_spread,
      prime_discount: plan.prime_discount,
      rate_shift: Number(shift),
      ltv: ltv === null ? undefined : ltv / 100,
      mortgage_years: term,
      horizon_years: horizon,
      investment_return: (investMode === "custom" ? parsed(invest) : etf?.value) ?? data.investment_return.value,
      cash_rebate_pct: parsed(rebate) ?? plan.cash_rebate_pct,
    }
  }, [data, estate, plan, prime, primeChoice, mode, flat, area, price, rent, valuation, firstTime, income, shift, ltv, term, horizon, invest, investMode, etf, rebate])

  useEffect(() => {
    if (!inputs || !data || !inputs.saleable_area) return
    let current = true
    compareForecast(inputs, data.market_benchmark ?? null, data.scenarios)
      .then((next) => current && setReply(next))
      .catch((error) => console.error(error))
    return () => {
      current = false
    }
  }, [inputs, data])

  const results = reply?.results
  const result = results?.neutral
  const used = result?.inputs
  const investmentSource = investMode === "deposit"
    ? data?.investment_return.bank
      ? t("investDepositHint", { bank: data.investment_return.bank })
      : t("investFallbackHint")
    : etf
      ? t(etf.dividend_tax ? "etfTaxHint" : "etfHint", { years: etf.years, to: etf.prices_to }) +
        " " +
        t("etfWorst", {
          worst: etf.worst.toFixed(2).replace("-", "−"),
          from: etf.worst_from,
          to: etf.worst_to,
          share: etf.losing_share,
          since: etf.history_from.slice(0, 4),
        })
      : t("reportCustomInvestment")
  // Region -> district -> Estate, each list in the order the Estates are listed.
  const regions = REGION_ORDER.filter((r) => data?.estates.some((e) => e.region_zh === r))
  const districts = unique((data?.estates ?? []).filter((e) => e.region_zh === estate?.region_zh), (e) => e.district_zh)
  const estatesHere = (data?.estates ?? []).filter((e) => e.district_zh === estate?.district_zh)

  function chooseRegion(region: string) {
    const first = data?.estates.find((e) => e.region_zh === region)
    if (first) chooseEstate(first.id)
  }

  function chooseDistrict(district: string) {
    const first = data?.estates.find((e) => e.district_zh === district)
    if (first) chooseEstate(first.id)
  }

  function chooseEstate(id: string) {
    setEstateId(id)
    setFlat(null)
    setPrice("")
    setRent("")
    setValuation("")
  }

  function printReport() {
    const previousTitle = document.title
    document.title = `${t("reportTitle")} - ${lang === "en" ? estate?.name_en : estate?.name_zh}`
    const restoreTitle = () => {
      document.title = previousTitle
    }
    window.addEventListener("afterprint", restoreTitle, { once: true })
    window.print()
  }

  return (
    <div className="mx-auto max-w-6xl px-4 pt-6 pb-16 sm:px-6 sm:pt-10">
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4 sm:mb-8">
        <div>
          <h1 className="text-[34px] leading-tight font-bold tracking-tight">
            {tool === "comparison" ? t("title") : t("affordabilityTitle")}
          </h1>
          <p className="mt-1 max-w-xl text-[17px] text-muted-foreground">
            {tool === "comparison" ? t("subtitle") : t("affordabilitySubtitle")}
          </p>
        </div>
        <Segmented
          label="Language"
          value={lang}
          onChange={setLang}
          options={Object.entries(LANGUAGES).map(([value, label]) => ({ value: value as Lang, label }))}
        />
      </header>

      {status === "loading" && <p className="py-24 text-center text-muted-foreground">{t("loading")}</p>}
      {status === "error" && <p className="py-24 text-center text-destructive">{t("loadError")}</p>}

      {status === "ready" && data && (
        <>
          <div className="mb-6 max-w-sm">
            <Segmented
              label={t("toolComparison")}
              value={tool}
              onChange={setTool}
              options={[
                { value: "comparison", label: t("toolComparison") },
                { value: "affordability", label: t("toolAffordability") },
              ]}
            />
          </div>
          {tool === "affordability" ? (
            <Affordability lang={lang} rates={planRates} />
          ) : estate && plan ? (
            <>
            <div className="grid gap-8 lg:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
          {/* ---------- Inputs ---------- */}
          <div className="space-y-7">
            <Section
              title={t("home")}
              footer={
                <>
                  {estate.price_source === "centaline"
                    ? t("estateFactsAsking", {
                        price: money(estate.price_per_ft),
                        rent: "$" + estate.rent_per_ft.toFixed(1),
                        n: estate.listings ?? "–",
                      })
                    : t("estateFacts", {
                        price: money(estate.price_per_ft),
                        rent: "$" + estate.rent_per_ft.toFixed(1),
                        tx: estate.transactions ?? "–",
                      })}{" "}
                  <a href={estate.source} target="_blank" rel="noreferrer" className="inline-flex items-center gap-0.5 text-primary">
                    {estate.price_source === "centaline" ? "Centaline" : "Midland"} <ExternalLink className="size-3" />
                  </a>
                </>
              }
            >
              <div className="space-y-2 py-3">
                <span className="text-[17px]">{t("region")}</span>
                <Segmented
                  label={t("region")}
                  value={estate.region_zh}
                  onChange={chooseRegion}
                  options={regions.map((r) => ({
                    value: r,
                    label: lang === "en" ? REGION_SHORT_EN[r] : r,
                  }))}
                />
              </div>
              <Row label={t("district")}>
                <Select value={estate.district_zh} onValueChange={chooseDistrict}>
                  <SelectTrigger aria-label={t("district")} className="h-8 max-w-56 border-none bg-transparent pr-0 text-[17px] shadow-none focus-visible:ring-0">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {districts.map((e) => (
                      <SelectItem key={e.district_zh} value={e.district_zh}>
                        {lang === "en" ? e.district_en : e.district_zh}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Row>
              <Row label={t("estate")}>
                <Select value={estateId} onValueChange={chooseEstate}>
                  <SelectTrigger aria-label={t("estate")} className="h-8 max-w-56 border-none bg-transparent pr-0 text-[17px] shadow-none focus-visible:ring-0">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {estatesHere.map((e) => (
                      <SelectItem key={e.id} value={e.id}>
                        {lang === "en" ? e.name_en : e.name_zh}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Row>
              <div className="py-2.5">
                <Segmented
                  label={t("flatMode")}
                  value={mode}
                  onChange={(next) => {
                    setMode(next)
                    setPrice("")
                    setValuation("")
                  }}
                  options={[
                    { value: "typical", label: t("typicalFlat") },
                    { value: "specific", label: t("specificFlat") },
                  ]}
                />
              </div>
              {mode === "specific" && (
                <FlatPicker key={estate.id} estate={estate} lang={lang} onFlat={setFlat} />
              )}
              {mode === "specific" && flat?.saleable_area ? (
                <Row label={t("area")}>
                  <span className="text-foreground tabular-nums">{flat.saleable_area}</span> {t("sqft")}
                </Row>
              ) : (
                <Row label={t("area")} htmlFor="area">
                  <NumberField id="area" value={area} onChange={setArea} suffix={t("sqft")} />
                </Row>
              )}
              <Row
                label={t("price")}
                hint={price ? undefined : mode === "specific" && flat ? t("hsbcValuation") : t("typical")}
                htmlFor="price"
              >
                <NumberField id="price" value={price} onChange={setPrice} prefix="$" placeholder={digits(used?.price)} />
              </Row>
              <Row label={t("rent")} hint={rent ? undefined : t("typical")} htmlFor="rent">
                <NumberField id="rent" value={rent} onChange={setRent} prefix="$" placeholder={digits(used?.monthly_rent)} />
              </Row>
              <Row label={t("valuation")} hint={t("optional")} htmlFor="valuation">
                <NumberField id="valuation" value={valuation} onChange={setValuation} prefix="$" placeholder={digits(used?.price)} />
              </Row>
            </Section>

            <Section title={t("you")}>
              <Row label={t("firstTime")} hint={t("firstTimeHint")}>
                <Switch checked={firstTime} onCheckedChange={setFirstTime} className="data-[state=checked]:bg-success" aria-label={t("firstTime")} />
              </Row>
              <Row label={t("permanentResident")} hint={t("permanentResidentHint")}>
                <Switch checked={permanent} onCheckedChange={setPermanent} className="data-[state=checked]:bg-success" aria-label={t("permanentResident")} />
              </Row>
              <Row label={t("income")} hint={t("incomeHint")} htmlFor="income">
                <NumberField id="income" value={income} onChange={setIncome} prefix="$" placeholder="—" />
              </Row>
            </Section>

            <Section
              title={t("mortgage")}
              footer={
                used && (
                  <span className="inline-flex flex-wrap items-center gap-1.5">
                    {primeChoice === "h"
                      ? t("rateFormula", {
                          hibor: data.rates.hibor_1m.toFixed(2),
                          spread: plan.hibor_spread,
                          prime: prime.toFixed(2),
                          discount: plan.prime_discount,
                        })
                      : t("pRateFormula", { prime: prime.toFixed(2) })}{" "}
                    {bankPrime && primeBank ? (
                      <a
                        href={PRIME_SOURCE_URLS[primeBank]}
                        target="_blank"
                        rel="noreferrer"
                        className="underline decoration-dotted underline-offset-2"
                      >
                        {t("primeFromBank", { bank: primeBank, date: bankPrime.date })}
                        <ExternalLink className="ml-1 inline size-3" />
                      </a>
                    ) : t("primeFromHkma")}
                    {plan.provisional && <ProvisionalBadge lang={lang} />}
                  </span>
                )
              }
            >
              <Row label={t("bank")}>
                <Select
                  value={String(bank)}
                  onValueChange={(v) => {
                    setBank(Number(v))
                    setRebate("")
                  }}
                >
                  <SelectTrigger className="h-8 border-none bg-transparent pr-0 text-[17px] shadow-none focus-visible:ring-0">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {data.bank_plans.map((p, i) => (
                      <SelectItem key={p.bank} value={String(i)}>
                        {p.bank}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Row>
              {used && (
                <div className="space-y-3 py-3">
                  <div className="flex items-baseline justify-between">
                    <span className="text-[17px]">{t("ltv")}</span>
                    <span className="text-[17px] text-muted-foreground tabular-nums">{percent(used.ltv, 0)}</span>
                  </div>
                  <Slider
                    min={50}
                    max={Math.round(used.max_ltv * 100)}
                    step={1}
                    value={[Math.round(used.ltv * 100)]}
                    onValueChange={([v]) => setLtv(v)}
                    aria-label={t("ltv")}
                  />
                  <p className="text-[13px] text-muted-foreground">{t("ltvMax", { max: percent(used.max_ltv, 0) })}</p>
                </div>
              )}
              <div className="space-y-2 py-3">
                <div>
                  <p className="text-[17px]">{t("pRateChoice")}</p>
                  <p className="text-[13px] leading-snug text-muted-foreground">{t("pRateChoiceHint")}</p>
                </div>
                <Segmented
                  label={t("pRateChoice")}
                  value={primeChoice}
                  onChange={setPrimeChoice}
                  options={[
                    { value: "h", label: t("pRateH") },
                    { value: "small", label: t("pRateSmall") },
                    { value: "big", label: t("pRateBig") },
                  ]}
                  className="w-full"
                />
              </div>
              <Row label={t("term")}>
                <Segmented
                  label={t("term")}
                  value={String(term)}
                  onChange={(v) => setTerm(Number(v))}
                  options={["20", "25", "30"].map((v) => ({ value: v, label: v }))}
                />
              </Row>
              <Row label={t("rate")}>
                <span className="text-foreground tabular-nums">{used ? used.mortgage_rate.toFixed(2) + "%" : "–"}</span>
              </Row>
              <Row label={t("cashRebate")} hint={t("cashRebateHint")} htmlFor="rebate">
                <NumberField id="rebate" value={rebate} onChange={setRebate} suffix="%" placeholder={String(plan.cash_rebate_pct)} />
              </Row>
              <div className="space-y-2 py-3">
                <span className="text-[15px] text-muted-foreground">{t("ratesMove")}</span>
                <Segmented
                  label={t("ratesMove")}
                  value={shift}
                  onChange={setShift}
                  options={[
                    { value: "-1", label: t("rateDown") },
                    { value: "0", label: t("rateNow") },
                    { value: "1", label: t("rateUp") },
                  ]}
                />
              </div>
            </Section>

            <Section
              title={t("assumptions")}
              footer={
                <span className="inline-flex flex-wrap items-center gap-1.5">
                  {reply &&
                    (() => {
                      const { pessimistic: low, neutral: mid, optimistic: high } = reply.scenarios
                      const growth = {
                        years: horizon,
                        price: mid.price_growth,
                        rent: mid.rent_growth,
                        priceLow: low.price_growth,
                        priceHigh: high.price_growth,
                        rentLow: low.rent_growth,
                        rentHigh: high.rent_growth,
                      }
                      const benchmark = data.market_benchmark
                      return reply.source === "forecast" && benchmark ? (
                        t("marketBenchmark", {
                          ...growth,
                          from: benchmark.price.history_from,
                          to: benchmark.price.history_to,
                        })
                      ) : (
                        <>
                          {t("scenarioRange", growth)}
                          <ProvisionalBadge lang={lang} />
                        </>
                      )
                    })()}
                </span>
              }
            >
              <div className="space-y-3 py-3">
                <div className="flex items-baseline justify-between">
                  <span className="text-[17px]">{t("horizon")}</span>
                  <span className="text-[17px] text-muted-foreground tabular-nums">
                    {horizon} {t("years")}
                  </span>
                </div>
                <Slider min={1} max={30} step={1} value={[horizon]} onValueChange={([v]) => setHorizon(v)} aria-label={t("horizon")} />
              </div>
              <div className="space-y-2 py-3">
                <span className="text-[17px]">{t("invest")}</span>
                <p className="text-[13px] leading-snug text-muted-foreground">{t("investHint")}</p>
                <Segmented
                  label={t("invest")}
                  value={investMode}
                  onChange={setInvestMode}
                  options={[
                    { value: "deposit", label: t("investDeposit") },
                    ...(data.etf_returns?.[ETF_TICKER.hk] ? [{ value: "hk" as const, label: t("investHk") }] : []),
                    ...(data.etf_returns?.[ETF_TICKER.us] ? [{ value: "us" as const, label: t("investUs") }] : []),
                    { value: "custom", label: t("investCustom") },
                  ]}
                />
              </div>
              {investMode === "deposit" ? (
                <Row
                  label={t("investDepositRate")}
                  hint={
                    data.investment_return.bank
                      ? t("investDepositHint", { bank: data.investment_return.bank })
                      : t("investFallbackHint")
                  }
                >
                  <span className="text-foreground tabular-nums">{data.investment_return.value.toFixed(2)}%</span>
                </Row>
              ) : etf && (investMode === "hk" || investMode === "us") ? (
                <Row
                  label={t("etfRate", { name: t(investMode === "hk" ? "etf2800" : "etfSpy"), ticker: ETF_TICKER[investMode] })}
                  hint={
                    t(etf.dividend_tax ? "etfTaxHint" : "etfHint", { years: etf.years, to: etf.prices_to }) +
                    " " +
                    t("etfWorst", {
                      worst: etf.worst.toFixed(2).replace("-", "−"),
                      from: etf.worst_from,
                      to: etf.worst_to,
                      share: etf.losing_share,
                      since: etf.history_from.slice(0, 4),
                    })
                  }
                >
                  <span className="text-foreground tabular-nums">{etf.value.toFixed(2)}%</span>
                </Row>
              ) : (
                <Row label={t("investCustomRate")} htmlFor="invest">
                  <NumberField
                    id="invest"
                    value={invest}
                    onChange={setInvest}
                    suffix="%"
                    placeholder={String(data.investment_return.value)}
                  />
                </Row>
              )}
            </Section>
          </div>

          {/* ---------- Results ---------- */}
          <div className="space-y-7 lg:sticky lg:top-6 lg:self-start">
            {reply && result && results && used && (
              <>
                {(() => {
                  // Python's outcome_range: the smallest and largest gap, and who leads in every scenario.
                  const { verdict, low_gap: low, high_gap: high } = reply.range
                  const short = (n: number) => shortMoney(Math.abs(n), lang)
                  const years = used.horizon_years
                  const rangeText =
                    verdict === "buy"
                      ? t("outcomeIntervalBuy", { low: short(low), high: short(high), years })
                      : verdict === "rent"
                        ? t("outcomeIntervalRent", { low: short(high), high: short(low), years })
                        : t("outcomeIntervalMixed", { rentLead: short(low), buyLead: short(high), years })
                  return (
                    <div className="rounded-[var(--radius)] bg-card p-5">
                      <p className="text-[13px] font-semibold tracking-wide text-muted-foreground uppercase">
                        {t("marketBenchmarkLabel")}
                      </p>
                      <p
                        className={cn(
                          "mt-1 text-[28px] leading-tight font-bold tracking-tight",
                          verdict === "buy" ? "text-chart-1" : verdict === "rent" ? "text-chart-2" : "text-foreground",
                        )}
                      >
                        {t(verdict === "buy" ? "buyWins" : verdict === "rent" ? "rentWins" : "dependsOnMarket")}
                      </p>
                      <p className="mt-1 text-[17px]">{rangeText}</p>
                      <p className="mt-1 text-[15px] text-muted-foreground">
                        {result.break_even_year !== null
                          ? t("breakEven", { year: result.break_even_year })
                          : t("neverBreakEven", { years })}
                      </p>
                      <button
                        type="button"
                        onClick={printReport}
                        className="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
                      >
                        <FileDown className="size-4" />
                        {t("reportAction")}
                      </button>
                      <p className="mt-1 text-[12px] text-muted-foreground">{t("reportActionHint")}</p>
                    </div>
                  )
                })()}

                <Section
                  title={t("netWorth")}
                  footer={t("netWorthHint")}
                >
                  <div className="py-4">
                    <div className="mb-2 flex gap-4 text-[13px]">
                      <span className="flex items-center gap-1.5">
                        <span className="size-2.5 rounded-full bg-chart-1" />
                        {t("buyingRange")}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="size-2.5 rounded-full bg-chart-2" />
                        {t("rentingRange")}
                      </span>
                    </div>
                    <p className="mb-2 text-[12px] leading-snug text-muted-foreground">
                      {t("rangeLegend")}
                    </p>
                    <NetWorthChart
                      point={results.neutral}
                      low={results.pessimistic}
                      high={results.optimistic}
                      lang={lang}
                    />
                  </div>
                </Section>

                <div className="grid gap-7 xl:grid-cols-2">
                  <Section title={t("dayOne")}>
                    <Row label={t("downPayment")}>{money(result.upfront.down_payment)}</Row>
                    <Row label={t("stampDuty")}>{money(result.upfront.stamp_duty)}</Row>
                    <Row label={t("agentFee")}>{money(result.upfront.agent_fee)}</Row>
                    <Row label={t("legalFee")}>{money(result.upfront.legal_fee)}</Row>
                    <Row label={<span className="inline-flex items-center gap-1.5">{t("insurance")} <ProvisionalBadge lang={lang} /></span>}>
                      {money(result.upfront.insurance_premium)}
                    </Row>
                    {result.upfront.cash_rebate > 0 && (
                      <Row label={t("cashRebate")}>
                        <span className="text-success">−{money(result.upfront.cash_rebate)}</span>
                      </Row>
                    )}
                    <Row label={<span className="font-semibold">{t("cashNeeded")}</span>}>
                      <span className="font-semibold text-foreground">{money(result.upfront.total_cash)}</span>
                    </Row>
                    <Row label={t("loan")}>{money(result.upfront.loan)}</Row>
                  </Section>

                  <div className="space-y-7">
                    <Section title={t("firstYear")} footer={t("firstYearHint")}>
                      <Row label={t("repayment")}>{money(result.yearly_costs[0].mortgage)}</Row>
                      <Row label={t("managementFee")} hint={t("managementFeeHint", { fee: used.management_fee_per_ft })}>
                        {money(result.yearly_costs[0].management_fee)}
                      </Row>
                      <Row label={t("rates")} hint={t("ratesHint", { pct: used.rates_pct })}>
                        {money(result.yearly_costs[0].rates)}
                      </Row>
                      <Row label={t("governmentRent")} hint={t("ratesHint", { pct: used.government_rent_pct })}>
                        {money(result.yearly_costs[0].government_rent)}
                      </Row>
                      <Row label={t("repairs")} hint={t("repairsHint", { pct: used.repair_pct })}>
                        {money(result.yearly_costs[0].repairs)}
                      </Row>
                      <Row label={<span className="font-semibold">{t("ownerTotal")}</span>}>
                        <span className="font-semibold text-chart-1">{money(result.yearly_costs[0].owner_monthly)}</span>
                      </Row>
                      <Row label={<span className="font-semibold">{t("renterCosts")}</span>}>
                        <span className="font-semibold text-chart-2">{money(result.yearly_costs[0].rent_monthly)}</span>
                      </Row>
                    </Section>
                    <DepositRanking data={data} lang={lang} />
                    <Section title={t("reference")}>
                      <Row label={t("rentalYield")}>{percent(result.rental_yield, 2)}</Row>
                      {result.debt_servicing_ratio !== null && (
                        <Row label={t("dsr")} hint={result.dsr_too_high ? t("dsrTooHigh") : undefined}>
                          <span className={cn(result.dsr_too_high && "text-destructive")}>
                            {result.dsr_too_high && <AlertTriangle className="mr-1 inline size-4" />}
                            {percent(result.debt_servicing_ratio, 0)}
                          </span>
                        </Row>
                      )}
                    </Section>
                  </div>
                </div>

                <Section title={t("howTitle")}>
                  <ol className="list-decimal space-y-1.5 py-3 pl-5 text-[15px] leading-snug">
                    {STRINGS[lang].how.map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ol>
                </Section>

                <Section title={t("limitsTitle")}>
                  <ul className="list-disc space-y-1.5 py-3 pl-4 text-[15px] leading-snug">
                    {STRINGS[lang].limits.map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                </Section>

                <Section title={t("dataTitle")}>
                  <div className="space-y-1.5 py-3 text-[15px] leading-snug">
                    {estate.price_source === "centaline" ? (
                      <p className="text-warning">{t("dataEstateCentaline", { date: estate.scraped ?? data.date })}</p>
                    ) : (
                      <p>
                        {t("dataEstate", { date: estate.scraped ?? data.date })}
                        {(estate.scraped ?? data.date) !== data.date && (
                          <span className="text-warning"> {t("dataEstateStale")}</span>
                        )}
                      </p>
                    )}
                    <p>{t("dataHsbc")}</p>
                    <p>
                      {t("dataRates", { date: data.rates.hibor_date })}
                      {data.rates.stale && <span className="text-warning"> {t("dataStale")}</span>}
                    </p>
                    {data.etf_returns?.SPY && <p>{t("dataEtf", { date: data.etf_returns.SPY.prices_to })}</p>}
                    {data.market_benchmark && (
                      <p>
                        {t("dataForecast", {
                          from: data.market_benchmark.price.history_from,
                          to: data.market_benchmark.price.history_to,
                          low: data.market_benchmark.price.past_ten_year_growth.low,
                          high: data.market_benchmark.price.past_ten_year_growth.high,
                        })}
                      </p>
                    )}
                    <p className="text-muted-foreground">{t("dataManual")}</p>
                  </div>
                </Section>
              </>
            )}
          </div>
          </div>
        {result && results && (
          <PdfReport
            lang={lang}
            estate={estate}
            data={data}
            flat={mode === "specific" ? flat : null}
            reply={reply}
            plan={plan}
            prime={prime}
            primeChoice={primeChoice}
            primeBank={primeBank ?? plan.bank}
            bankPrimeDate={bankPrime?.date}
            investmentSource={investmentSource}
          />
        )}
            </>
          ) : null}
        </>
      )}

      <footer className="mt-12 text-center text-[13px] text-muted-foreground">{t("footer")}</footer>
    </div>
  )
}

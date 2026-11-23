import { useEffect, useMemo, useState } from "react"
import { AlertTriangle, ExternalLink } from "lucide-react"
import { DepositRanking } from "@/components/DepositRanking"
import { FlatPicker } from "@/components/FlatPicker"
import { NetWorthChart } from "@/components/NetWorthChart"
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
import { money, percent } from "@/lib/format"
import { compareScenarios, loadCalculator, recommendEstates } from "@/lib/python"
import {
  SCENARIO_NAMES,
  type Estate,
  type Flat,
  type Recommendation,
  type Result,
  type ScenarioName,
  type Snapshot,
} from "@/lib/types"
import { cn } from "@/lib/utils"

type Shift = "-1" | "0" | "1"
type InvestMode = "deposit" | "hk" | "us" | "custom"

// The ETF behind each stock choice (returns worked out in rentorbuy/etf_returns.py).
const ETF_TICKER = { hk: "2800.HK", us: "SPY" } as const

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
  const t = (key: Parameters<typeof translate>[1], values?: Record<string, string | number>) =>
    translate(lang, key, values)

  const [data, setData] = useState<Snapshot | null>(null)
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading")
  const [results, setResults] = useState<Record<ScenarioName, Result> | null>(null)

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
  const [takeHome, setTakeHome] = useState("")
  const [monthlyDebt, setMonthlyDebt] = useState("")
  const [downPaymentBudget, setDownPaymentBudget] = useState("")
  const [otherSavings, setOtherSavings] = useState("")
  const [preferredPayment, setPreferredPayment] = useState("")
  const [comfortablePct, setComfortablePct] = useState("30")
  const [recommendationRegion, setRecommendationRegion] = useState("")
  const [recommendationDistrict, setRecommendationDistrict] = useState("")
  const [bedrooms, setBedrooms] = useState("")
  const [recommendationMode, setRecommendationMode] = useState<"both" | "buy" | "rent">("both")
  const [recommendations, setRecommendations] = useState<Recommendation[] | null>(null)
  const [recommendationError, setRecommendationError] = useState(false)
  const [savedRecommendations, setSavedRecommendations] = useState<Recommendation[]>([])
  const [bank, setBank] = useState(0)
  const [ltv, setLtv] = useState<number | null>(null)
  const [term, setTerm] = useState(30)
  const [shift, setShift] = useState<Shift>("0")
  const [horizon, setHorizon] = useState(10)
  const [invest, setInvest] = useState("")
  const [investMode, setInvestMode] = useState<InvestMode>("deposit")
  const [rebate, setRebate] = useState("")
  const [scenario, setScenario] = useState<ScenarioName>("neutral")

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
    try {
      const saved = JSON.parse(localStorage.getItem("saved-estate-recommendations") ?? "[]")
      if (Array.isArray(saved)) {
        setSavedRecommendations(saved.filter((item): item is Recommendation =>
          item && typeof item.id === "string" && typeof item.estate_id === "string" &&
          (item.mode === "buy" || item.mode === "rent") &&
          (item.label === "comfortable" || item.label === "stretch" || item.label === "risky") &&
          typeof item.source === "string" && item.monthly_costs && typeof item.monthly_costs.total === "number",
        ))
      }
    } catch {
      // Storage can be blocked or contain data from an older app version.
    }
  }, [])

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
  // The bank's own prime if we could read it; otherwise HKMA's (Standard Chartered).
  const bankPrime = plan ? data?.bank_primes?.[plan.bank] : undefined
  const prime = bankPrime?.prime ?? data?.rates.prime ?? 0
  const etf = investMode === "hk" || investMode === "us" ? data?.etf_returns?.[ETF_TICKER[investMode]] : undefined

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
  }, [data, estate, plan, prime, mode, flat, area, price, rent, valuation, firstTime, income, shift, ltv, term, horizon, invest, investMode, etf, rebate])

  useEffect(() => {
    if (!inputs || !data || !inputs.saleable_area) return
    let current = true
    compareScenarios(inputs, data.scenarios)
      .then((next) => current && setResults(next))
      .catch((error) => console.error(error))
    return () => {
      current = false
    }
  }, [inputs, data])

  const result = results?.[scenario]
  const used = result?.inputs
  // Region -> district -> Estate, each list in the order the Estates are listed.
  const regions = REGION_ORDER.filter((r) => data?.estates.some((e) => e.region_zh === r))
  const districts = unique((data?.estates ?? []).filter((e) => e.region_zh === estate?.region_zh), (e) => e.district_zh)
  const estatesHere = (data?.estates ?? []).filter((e) => e.district_zh === estate?.district_zh)
  const recommendationRegions = unique(data?.estates ?? [], (e) => e.region_en)
  const recommendationDistricts = unique(
    (data?.estates ?? []).filter((e) => !recommendationRegion || e.region_en === recommendationRegion),
    (e) => e.district_en,
  )
  const bedroomOptions = [...new Set((data?.estates ?? []).flatMap((e) => Object.keys(e.by_room ?? {})))].sort()

  const recommendationInputs = useMemo(() => {
    if (!data || !parsed(takeHome)) return null
    return {
      monthly_income: parsed(takeHome),
      monthly_debt: parsed(monthlyDebt) ?? 0,
      down_payment: parsed(downPaymentBudget) ?? 0,
      savings: parsed(otherSavings) ?? 0,
      preferred_payment: parsed(preferredPayment),
      saleable_area: parsed(area),
      mortgage_years: term,
      first_time: firstTime,
      comfortable_pct: parsed(comfortablePct) ?? 30,
      hibor: data.rates.hibor_1m,
      prime,
      hibor_spread: plan?.hibor_spread,
      prime_discount: plan?.prime_discount,
      rate_shift: Number(shift),
      region: recommendationRegion,
      district: recommendationDistrict,
      bedrooms,
      mode: recommendationMode,
    }
  }, [
    data, takeHome, monthlyDebt, downPaymentBudget, otherSavings, preferredPayment, area, term, firstTime,
    comfortablePct, prime, plan, shift, recommendationRegion, recommendationDistrict,
    bedrooms, recommendationMode,
  ])

  useEffect(() => {
    if (!data || !recommendationInputs) return
    let current = true
    recommendEstates(data.estates, recommendationInputs)
      .then((next) => {
        if (current) {
          setRecommendations(next)
          setRecommendationError(false)
        }
      })
      .catch((error) => {
        console.error(error)
        if (current) setRecommendationError(true)
      })
    return () => {
      current = false
    }
  }, [data, recommendationInputs])

  function removeSavedRecommendation(id: string) {
    setSavedRecommendations((current) => {
      const next = current.filter((item) => item.id !== id)
      try {
        localStorage.setItem("saved-estate-recommendations", JSON.stringify(next))
      } catch {
        // Saving is optional when browser storage is unavailable.
      }
      return next
    })
  }

  function saveRecommendation(recommendation: Recommendation) {
    setSavedRecommendations((current) => {
      if (current.some((item) => item.id === recommendation.id)) return current
      const next = [...current, recommendation]
      try {
        localStorage.setItem("saved-estate-recommendations", JSON.stringify(next))
      } catch {
        // Saving is optional when browser storage is unavailable.
      }
      return next
    })
  }

  function recommendationName(recommendation: Recommendation) {
    return lang === "en" ? recommendation.estate_name : recommendation.estate_name_zh
  }

  function recommendationLocation(recommendation: Recommendation) {
    return lang === "en"
      ? `${recommendation.region} · ${recommendation.district}`
      : `${recommendation.region_zh} · ${recommendation.district_zh}`
  }

  function recommendationExplanation(recommendation: Recommendation) {
    const values = {
      cost: money(recommendation.monthly_costs.total),
      ratio: recommendation.housing_pct.toFixed(1),
      limit: money(recommendation.comfortable_budget),
      pct: recommendation.comfortable_pct,
      stretch: recommendation.stretch_limit_pct.toFixed(1),
      stretchBudget: money(recommendation.stretch_budget),
      shortfall: money(recommendation.cash_shortfall),
      debt: money(recommendation.monthly_debt),
    }
    const key =
      recommendation.label === "comfortable"
        ? "recommendationExplanationComfortable"
        : recommendation.label === "stretch"
          ? "recommendationExplanationStretch"
          : "recommendationExplanationRisky"
    return t(key, values)
  }

  function recommendationCard(recommendation: Recommendation, saved = false) {
    const labelClass = {
      comfortable: "bg-success/15 text-success",
      stretch: "bg-warning/15 text-warning",
      risky: "bg-destructive/10 text-destructive",
    }[recommendation.label]
    return (
      <article key={recommendation.id} className="space-y-3 rounded-xl bg-secondary/40 p-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h3 className="font-semibold">{recommendationName(recommendation)}</h3>
            <p className="text-[13px] text-muted-foreground">
              {recommendationLocation(recommendation)}
              {recommendation.bedrooms ? ` · ${recommendation.bedrooms} ${t("bedrooms").toLowerCase()}` : ""}
              {" · "}{t(recommendation.mode === "buy" ? "recommendationBuy" : "recommendationRent")}
            </p>
          </div>
          <span className={cn("rounded-full px-2.5 py-1 text-[12px] font-semibold", labelClass)}>
            {t(recommendation.label)}
          </span>
        </div>
        <p className="text-[14px] leading-snug">{recommendationExplanation(recommendation)}</p>
        <div className="grid gap-x-4 gap-y-1 text-[13px] sm:grid-cols-2">
          <p>{t("recommendationMonthly")}: <strong>{money(recommendation.monthly_costs.total)}</strong></p>
          {recommendation.mode === "buy" ? (
            <>
              <p>{t("recommendationPrice")}: <strong>{money(recommendation.price)}</strong></p>
              <p>{t("recommendationRate")}: {recommendation.mortgage_rate.toFixed(2)}%</p>
              <p>{t("recommendationUpfront")}: <strong>{money(recommendation.upfront?.total_cash ?? 0)}</strong></p>
              <p>{t("recommendationCashAvailable")}: <strong>{money(recommendation.cash_available)}</strong></p>
              <p>{t("stampDuty")}: {money(recommendation.upfront?.stamp_duty ?? 0)}</p>
              <p>{t("recommendationInsurance")}: {money(recommendation.upfront?.insurance_premium ?? 0)}</p>
              <p>{t("recommendationMortgage")}: {money(recommendation.monthly_costs.mortgage ?? 0)}</p>
              <p>{t("recommendationManagement")}: {money(recommendation.monthly_costs.management_fee ?? 0)}</p>
              <p>{t("recommendationRates")}: {money(recommendation.monthly_costs.rates ?? 0)}</p>
              <p>{t("recommendationGovRent")}: {money(recommendation.monthly_costs.government_rent ?? 0)}</p>
              <p>{t("recommendationRepairs")}: {money(recommendation.monthly_costs.repairs ?? 0)}</p>
              {recommendation.cash_shortfall > 0 && (
                <p className="text-destructive">{t("recommendationShortfall")}: {money(recommendation.cash_shortfall)}</p>
              )}
            </>
          ) : (
            <p>{t("recommendationPrice")}: {money(recommendation.price)}</p>
          )}
        </div>
        <div className="rounded-lg bg-background/70 p-3 text-[13px]">
          <p className="font-medium">
            {t("recommendationStress")}: {recommendation.mode === "buy" ? t("recommendationStressBuy") : t("recommendationStressRent")}
          </p>
          <p className="mt-1 text-muted-foreground">
            {t("recommendationStressResult", {
              label: t(recommendation.stress.label ?? "risky"),
              cost: money(recommendation.stress.monthly_cost),
              income: money(recommendation.stress.monthly_income),
            })}
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2 text-[12px] text-muted-foreground">
          <a href={recommendation.source} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-primary">
            {recommendation.price_source === "centaline" ? "Centaline" : "Midland"}
            {recommendation.source_date ? ` · ${recommendation.source_date}` : ""}
            <ExternalLink className="size-3" />
          </a>
          {saved ? (
            <button onClick={() => removeSavedRecommendation(recommendation.id)} className="text-destructive">
              {t("recommendationRemove")}
            </button>
          ) : (
            <button
              onClick={() => saveRecommendation(recommendation)}
              disabled={savedRecommendations.some((item) => item.id === recommendation.id)}
              className="text-primary disabled:cursor-default disabled:text-muted-foreground"
            >
              {savedRecommendations.some((item) => item.id === recommendation.id)
                ? t("recommendationSaved")
                : t("recommendationSave")}
            </button>
          )}
        </div>
      </article>
    )
  }

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

  return (
    <div className="mx-auto max-w-6xl px-4 pt-6 pb-16 sm:px-6 sm:pt-10">
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4 sm:mb-8">
        <div>
          <h1 className="text-[34px] leading-tight font-bold tracking-tight">{t("title")}</h1>
          <p className="mt-1 max-w-xl text-[17px] text-muted-foreground">{t("subtitle")}</p>
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

      {status === "ready" && data && estate && plan && (
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

            <Section title={t("recommendationTitle")}>
              <p className="py-2 text-[13px] text-muted-foreground">{t("recommendationCashHint")}</p>
              <Row label={t("takeHome")} htmlFor="take-home">
                <NumberField id="take-home" value={takeHome} onChange={setTakeHome} prefix="$" placeholder="—" />
              </Row>
              <Row label={t("monthlyDebt")} htmlFor="monthly-debt">
                <NumberField id="monthly-debt" value={monthlyDebt} onChange={setMonthlyDebt} prefix="$" placeholder="0" />
              </Row>
              <Row label={t("downPaymentBudget")} htmlFor="down-payment-budget">
                <NumberField id="down-payment-budget" value={downPaymentBudget} onChange={setDownPaymentBudget} prefix="$" placeholder="0" />
              </Row>
              <Row label={t("otherSavings")} htmlFor="other-savings">
                <NumberField id="other-savings" value={otherSavings} onChange={setOtherSavings} prefix="$" placeholder="0" />
              </Row>
              <Row label={t("preferredPayment")} htmlFor="preferred-payment">
                <NumberField id="preferred-payment" value={preferredPayment} onChange={setPreferredPayment} prefix="$" placeholder={t("optional")} />
              </Row>
              <Row label={t("comfortLimit")} hint={t("comfortLimitHint")} htmlFor="comfortable-pct">
                <NumberField id="comfortable-pct" value={comfortablePct} onChange={setComfortablePct} suffix="%" />
              </Row>
              <Row label={t("recommendationMode")}>
                <Segmented
                  label={t("recommendationMode")}
                  value={recommendationMode}
                  onChange={setRecommendationMode}
                  options={[
                    { value: "both", label: t("recommendationBoth") },
                    { value: "buy", label: t("recommendationBuy") },
                    { value: "rent", label: t("recommendationRent") },
                  ]}
                />
              </Row>
              <Row label={t("region")}>
                <Select
                  value={recommendationRegion || "all"}
                  onValueChange={(value) => {
                    setRecommendationRegion(value === "all" ? "" : value)
                    setRecommendationDistrict("")
                  }}
                >
                  <SelectTrigger aria-label={t("region")} className="h-8 max-w-56 border-none bg-transparent pr-0 text-[15px] shadow-none focus-visible:ring-0">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t("locationAll")}</SelectItem>
                    {recommendationRegions.map((e) => (
                      <SelectItem key={e.region_en} value={e.region_en}>
                        {lang === "en" ? e.region_en : e.region_zh}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Row>
              <Row label={t("district")}>
                <Select
                  value={recommendationDistrict || "all"}
                  onValueChange={(value) => setRecommendationDistrict(value === "all" ? "" : value)}
                >
                  <SelectTrigger aria-label={t("district")} className="h-8 max-w-56 border-none bg-transparent pr-0 text-[15px] shadow-none focus-visible:ring-0">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t("locationAll")}</SelectItem>
                    {recommendationDistricts.map((e) => (
                      <SelectItem key={e.district_en} value={e.district_en}>
                        {lang === "en" ? e.district_en : e.district_zh}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Row>
              <Row label={t("bedrooms")}>
                <Select value={bedrooms || "all"} onValueChange={(value) => setBedrooms(value === "all" ? "" : value)}>
                  <SelectTrigger aria-label={t("bedrooms")} className="h-8 max-w-56 border-none bg-transparent pr-0 text-[15px] shadow-none focus-visible:ring-0">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t("bedroomsAny")}</SelectItem>
                    {bedroomOptions.map((count) => (
                      <SelectItem key={count} value={count}>{count}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Row>
              <p className="py-2 text-[13px] leading-snug text-muted-foreground">{t("recommendationUnavailable")}</p>
            </Section>

            <Section
              title={t("mortgage")}
              footer={
                used && (
                  <span className="inline-flex flex-wrap items-center gap-1.5">
                    {t("rateFormula", {
                      hibor: data.rates.hibor_1m.toFixed(2),
                      spread: plan.hibor_spread,
                      prime: prime.toFixed(2),
                      discount: plan.prime_discount,
                    })}{" "}
                    {bankPrime ? t("primeFromBank", { bank: plan.bank }) : t("primeFromHkma")}
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
                  {t("scenarioGrowth", {
                    price: data.scenarios[scenario].price_growth,
                    rent: data.scenarios[scenario].rent_growth,
                  })}
                  <ProvisionalBadge lang={lang} />
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
              <div className="space-y-2 py-3">
                <span className="text-[17px]">{t("scenario")}</span>
                <Segmented
                  label={t("scenario")}
                  value={scenario}
                  onChange={setScenario}
                  options={SCENARIO_NAMES.map((name) => ({ value: name, label: t(name) }))}
                />
              </div>
            </Section>
          </div>

          {/* ---------- Results ---------- */}
          <div className="space-y-7 lg:sticky lg:top-6 lg:self-start">
            <Section title={t("recommendationResults")}>
              {!recommendationInputs && (
                <p className="py-3 text-[14px] text-muted-foreground">{t("recommendationEnterIncome")}</p>
              )}
              {recommendationInputs && recommendationError && (
                <p className="py-3 text-[14px] text-destructive">{t("recommendationError")}</p>
              )}
              {recommendationInputs && recommendations && recommendations.length === 0 && (
                <p className="py-3 text-[14px] text-muted-foreground">{t("recommendationNone")}</p>
              )}
              {recommendationInputs && recommendations && recommendations.length > 0 && (
                <div className="space-y-3 py-3">
                  {recommendations.map((recommendation) => recommendationCard(recommendation))}
                </div>
              )}
              <p className="border-t border-border/60 py-3 text-[12px] leading-snug text-muted-foreground">
                {t("recommendationDisclaimer")}
              </p>
              <div className="border-t border-border/60 pt-3">
                <h3 className="mb-2 text-[15px] font-semibold">{t("recommendationShortlist")}</h3>
                {savedRecommendations.length === 0 ? (
                  <p className="text-[13px] text-muted-foreground">{t("recommendationShortlistEmpty")}</p>
                ) : (
                  <div className="space-y-3">
                    {savedRecommendations.map((recommendation) => recommendationCard(recommendation, true))}
                  </div>
                )}
              </div>
            </Section>

            {result && results && used && (
              <>
                <div className="rounded-[var(--radius)] bg-card p-5">
                  <p className="text-[13px] font-semibold tracking-wide text-muted-foreground uppercase">{t(scenario)}</p>
                  <p
                    className={cn(
                      "mt-1 text-[28px] leading-tight font-bold tracking-tight",
                      result.verdict === "buy" ? "text-chart-1" : "text-chart-2",
                    )}
                  >
                    {t(result.verdict === "buy" ? "buyWins" : "rentWins")}
                  </p>
                  <p className="mt-1 text-[17px]">
                    {t("by", { gap: money(Math.abs(result.gap)), years: used.horizon_years })}
                  </p>
                  <p className="mt-1 text-[15px] text-muted-foreground">
                    {result.break_even_year !== null
                      ? t("breakEven", { year: result.break_even_year })
                      : t("neverBreakEven", { years: used.horizon_years })}
                  </p>
                  <div className="mt-4 grid grid-cols-3 gap-2">
                    {SCENARIO_NAMES.map((name) => {
                      const r = results[name]
                      return (
                        <button
                          key={name}
                          onClick={() => setScenario(name)}
                          className={cn(
                            "rounded-xl bg-secondary/60 px-3 py-2 text-left transition-colors",
                            name === scenario && "ring-2 ring-primary",
                          )}
                        >
                          <div className="text-[12px] text-muted-foreground">{t(name)}</div>
                          <div className={cn("text-[15px] font-semibold", r.verdict === "buy" ? "text-chart-1" : "text-chart-2")}>
                            {t(r.verdict === "buy" ? "buying" : "renting")}
                          </div>
                          <div className="text-[12px] text-muted-foreground tabular-nums">+{money(Math.abs(r.gap))}</div>
                        </button>
                      )
                    })}
                  </div>
                </div>

                <Section
                  title={t("netWorth")}
                  footer={t("netWorthHint")}
                >
                  <div className="py-4">
                    <div className="mb-2 flex gap-4 text-[13px]">
                      <span className="flex items-center gap-1.5">
                        <span className="size-2.5 rounded-full bg-chart-1" />
                        {t("buying")}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="size-2.5 rounded-full bg-chart-2" />
                        {t("renting")}
                      </span>
                    </div>
                    <NetWorthChart result={result} lang={lang} />
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
                    <p className="text-muted-foreground">{t("dataManual")}</p>
                  </div>
                </Section>
              </>
            )}
          </div>
        </div>
      )}

      <footer className="mt-12 text-center text-[13px] text-muted-foreground">{t("footer")}</footer>
    </div>
  )
}

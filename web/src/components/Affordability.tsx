import { useEffect, useMemo, useState } from "react"
import { NumberField, Row, Section, parsed } from "@/components/grouped"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { translate, type Lang } from "@/i18n"
import { calculateAffordability, recommendEstates, type PlanRates } from "@/lib/python"
import type { AffordabilityResult, Estate, EstateRecommendation } from "@/lib/types"
import { money, percent } from "@/lib/format"
import { cn } from "@/lib/utils"

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function isEstateRecommendation(value: unknown): value is EstateRecommendation {
  if (!isRecord(value) || !isRecord(value.monthly_costs) || !isRecord(value.stress)) return false
  const numberFields = [
    "saleable_area",
    "monthly_debt",
    "gross_monthly_income",
    "price",
    "monthly_rent",
    "price_per_ft",
    "rent_per_ft",
    "mortgage_rate",
    "cash_available",
    "cash_shortfall",
    "housing_pct",
    "comfortable_pct",
    "comfortable_budget",
    "stretch_budget",
  ]
  const textFields = [
    "id",
    "estate_id",
    "estate_name",
    "estate_name_zh",
    "region",
    "region_zh",
    "district",
    "district_zh",
    "source",
  ]
  return (
    textFields.every((field) => typeof value[field] === "string") &&
    typeof value.source === "string" && value.source.startsWith("https://") &&
    numberFields.every((field) => typeof value[field] === "number") &&
    (value.debt_servicing_ratio === null || typeof value.debt_servicing_ratio === "number") &&
    (value.bedrooms === null || typeof value.bedrooms === "string") &&
    (value.source_date === undefined || value.source_date === null || typeof value.source_date === "string") &&
    (value.price_source === "midland" || value.price_source === "centaline") &&
    (value.mode === "buy" || value.mode === "rent") &&
    (value.label === "comfortable" || value.label === "stretch" || value.label === "risky") &&
    Object.values(value.monthly_costs).every((cost) => typeof cost === "number") &&
    (value.upfront === null ||
      (isRecord(value.upfront) && Object.values(value.upfront).every((cost) => typeof cost === "number"))) &&
    typeof value.stress.monthly_cost === "number" &&
    typeof value.stress.monthly_income === "number" &&
    typeof value.stress.housing_pct === "number" &&
    (value.stress.debt_servicing_ratio === null || typeof value.stress.debt_servicing_ratio === "number") &&
    typeof value.stress.income_reduction_pct === "number" &&
    typeof value.stress.rate_increase_pct === "number" &&
    (value.stress.label === "comfortable" || value.stress.label === "stretch" || value.stress.label === "risky")
  )
}

export function Affordability({
  lang,
  rates,
  estates,
  snapshotDate,
}: {
  lang: Lang
  rates: PlanRates
  estates: Estate[]
  snapshotDate: string
}) {
  const t = (key: Parameters<typeof translate>[1], values?: Record<string, string | number>) =>
    translate(lang, key, values)
  const [income, setIncome] = useState("")
  const [existingPayments, setExistingPayments] = useState("0")
  const [downPayment, setDownPayment] = useState("")
  const [takeHomeIncome, setTakeHomeIncome] = useState("")
  const [saleableArea, setSaleableArea] = useState("")
  const [savings, setSavings] = useState("0")
  const [rentDepositMonths, setRentDepositMonths] = useState("2")
  const [rentAgentFeePct, setRentAgentFeePct] = useState("50")
  const [preferredPayment, setPreferredPayment] = useState("")
  const [comfortablePct, setComfortablePct] = useState("30")
  const [region, setRegion] = useState("")
  const [district, setDistrict] = useState("")
  const [bedrooms, setBedrooms] = useState("")
  const [firstTime, setFirstTime] = useState(false)
  const [result, setResult] = useState<AffordabilityResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [recommendations, setRecommendations] = useState<EstateRecommendation[] | null>(null)
  const [recommendationError, setRecommendationError] = useState<string | null>(null)
  const [recommendationLoading, setRecommendationLoading] = useState(false)
  const [savedRecommendations, setSavedRecommendations] = useState<EstateRecommendation[]>([])
  const [storageStatus, setStorageStatus] = useState<"unavailable" | "invalid" | null>(null)

  useEffect(() => {
    let stored: string | null
    try {
      stored = window.localStorage.getItem("saved-estate-recommendations")
    } catch (cause) {
      console.error(cause)
      setStorageStatus("unavailable")
      return
    }
    if (stored === null) return

    let parsedItems: unknown
    try {
      parsedItems = JSON.parse(stored)
    } catch (cause) {
      console.error(cause)
      setStorageStatus("invalid")
      return
    }
    if (!Array.isArray(parsedItems)) {
      setStorageStatus("invalid")
      return
    }
    const validItems = parsedItems.filter(isEstateRecommendation)
    setSavedRecommendations(validItems)
    if (validItems.length !== parsedItems.length) setStorageStatus("invalid")
  }, [])

  const monthlyIncome = parsed(income)
  const monthlyDebt = parsed(existingPayments)
  const downPaymentFunds = parsed(downPayment)
  const recommendationIncome = parsed(takeHomeIncome)
  const recommendationArea = parsed(saleableArea)
  const savingsFunds = parsed(savings)
  const rentalDepositMonths = parsed(rentDepositMonths)
  const rentalAgentFeePct = parsed(rentAgentFeePct)
  const comfortableBoundary = parsed(comfortablePct)
  const preferredMonthlyPayment = parsed(preferredPayment)

  const regionOptions = useMemo(
    () => Array.from(new Map(estates.map((estate) => [estate.region_en, estate])).values()),
    [estates],
  )
  const districtOptions = useMemo(
    () => Array.from(
      new Map(
        estates
          .filter((estate) => !region || estate.region_en === region)
          .map((estate) => [estate.district_en, estate]),
      ).values(),
    ),
    [estates, region],
  )
  const bedroomOptions = useMemo(
    () => [...new Set(
      estates
        .filter((estate) =>
          (!region || estate.region_en === region) &&
          (!district || estate.district_en === district),
        )
        .flatMap((estate) => Object.keys(estate.by_room ?? {})),
    )].sort((a, b) => a.localeCompare(b, undefined, { numeric: true })),
    [estates, region, district],
  )

  const recommendationInputs = useMemo(() => {
    if (
      recommendationIncome === undefined ||
      recommendationIncome <= 0 ||
      monthlyIncome === undefined ||
      monthlyIncome <= 0 ||
      monthlyDebt === undefined ||
      downPaymentFunds === undefined ||
      savingsFunds === undefined ||
      recommendationArea === undefined ||
      comfortableBoundary === undefined
    ) {
      return null
    }

    return {
      monthly_income: recommendationIncome,
      gross_monthly_income: monthlyIncome,
      monthly_debt: monthlyDebt,
      down_payment: downPaymentFunds,
      savings: savingsFunds,
      saleable_area: recommendationArea,
      // A P rate is used as it is; with none, Python works out the H-plan rate from these.
      mortgage_rate: rates.p_rate,
      hibor: rates.hibor,
      prime: rates.prime,
      hibor_spread: rates.hibor_spread,
      prime_discount: rates.prime_discount,
      preferred_payment: preferredMonthlyPayment,
      comfortable_pct: comfortableBoundary,
      first_time: firstTime,
      rent_deposit_months: rentalDepositMonths ?? 2,
      rent_agent_fee_pct: rentalAgentFeePct ?? 50,
      region,
      district,
      bedrooms,
    }
  }, [
    recommendationIncome,
    monthlyIncome,
    monthlyDebt,
    downPaymentFunds,
    savingsFunds,
    recommendationArea,
    rates,
    preferredMonthlyPayment,
    comfortableBoundary,
    firstTime,
    rentalDepositMonths,
    rentalAgentFeePct,
    region,
    district,
    bedrooms,
  ])

  useEffect(() => {
    if (!monthlyIncome || monthlyDebt === undefined || downPaymentFunds === undefined) {
      setResult(null)
      setError(null)
      return
    }

    let current = true
    setResult(null)
    setError(null)
    calculateAffordability(monthlyIncome, monthlyDebt, downPaymentFunds, rates)
      .then((next) => current && setResult(next))
      .catch((cause: unknown) => {
        console.error(cause)
        if (current) setError(cause instanceof Error ? cause.message : String(cause))
      })
    return () => {
      current = false
    }
  }, [monthlyIncome, monthlyDebt, downPaymentFunds, rates])

  useEffect(() => {
    if (!recommendationInputs) {
      setRecommendations(null)
      setRecommendationError(null)
      setRecommendationLoading(false)
      return
    }

    let current = true
    setRecommendationLoading(true)
    setRecommendationError(null)
    recommendEstates(estates, recommendationInputs)
      .then((next) => {
        if (current) {
          setRecommendations(next)
          setRecommendationLoading(false)
        }
      })
      .catch((cause: unknown) => {
        console.error(cause)
        if (current) {
          setRecommendationError(cause instanceof Error ? cause.message : String(cause))
          setRecommendationLoading(false)
        }
      })
    return () => {
      current = false
    }
  }, [estates, recommendationInputs])

  function optionName(english: string, traditional: string) {
    return lang === "en" ? english : traditional
  }

  function recommendationName(item: EstateRecommendation) {
    return optionName(item.estate_name, item.estate_name_zh)
  }

  function recommendationLocation(item: EstateRecommendation) {
    return `${optionName(item.region, item.region_zh)} · ${optionName(item.district, item.district_zh)}`
  }

  function persistSavedRecommendations(items: EstateRecommendation[]) {
    setSavedRecommendations(items)
    try {
      window.localStorage.setItem("saved-estate-recommendations", JSON.stringify(items))
      setStorageStatus(null)
    } catch (cause) {
      console.error(cause)
      setStorageStatus("unavailable")
    }
  }

  function saveRecommendation(item: EstateRecommendation) {
    if (savedRecommendations.some((saved) => saved.id === item.id)) return
    persistSavedRecommendations([...savedRecommendations, item])
  }

  function removeSavedRecommendation(id: string) {
    persistSavedRecommendations(savedRecommendations.filter((item) => item.id !== id))
  }

  function recommendationCard(item: EstateRecommendation, saved = false) {
    const labelClass = {
      comfortable: "bg-success/15 text-success",
      stretch: "bg-warning/15 text-warning",
      risky: "bg-destructive/10 text-destructive",
    }[item.label]
    const sourceName = item.price_source === "centaline" ? "Centaline" : "Midland"

    return (
      <article key={item.id} className="space-y-3 rounded-xl bg-secondary/40 p-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h3 className="font-semibold">{recommendationName(item)}</h3>
            <p className="text-[13px] text-muted-foreground">
              {recommendationLocation(item)}
              {item.bedrooms ? ` · ${t("bedroomCount", { n: item.bedrooms })}` : ""}
              {" · "}{t(item.mode === "buy" ? "recommendationBuy" : "recommendationRent")}
            </p>
          </div>
          <span className={cn("rounded-full px-2.5 py-1 text-[12px] font-semibold", labelClass)}>
            {t(item.label)}
          </span>
        </div>
        <p className="text-[13px] leading-snug text-muted-foreground">
          {t("recommendationEstimateFormula", {
            value: money(item.mode === "buy" ? item.price_per_ft : item.rent_per_ft),
            area: item.saleable_area,
          })}
        </p>
        <p className="text-[13px] leading-snug">
          {t(
            item.label === "comfortable"
              ? "recommendationStatusComfortable"
              : item.label === "stretch"
                ? "recommendationStatusStretch"
                : "recommendationStatusRisky",
            {
              cost: money(item.monthly_costs.total),
              ratio: item.housing_pct.toFixed(1),
              comfort: money(item.comfortable_budget),
              stretch: money(item.stretch_budget),
            },
          )}
        </p>
        <div className="grid gap-x-4 gap-y-1 text-[13px] sm:grid-cols-2">
          <p>
            {t(item.mode === "buy" ? "recommendationPrice" : "recommendationRentEstimate")}:{" "}
            <strong>{money(item.mode === "buy" ? item.price : item.monthly_rent)}</strong>
          </p>
          {item.mode === "buy" && (
            <p>{t("recommendationMonthly")}: <strong>{money(item.monthly_costs.total)}</strong></p>
          )}
          {item.mode === "buy" && item.upfront && (
            <>
              <p>{t("recommendationUpfront")}: <strong>{money(item.upfront.total_cash)}</strong></p>
              <p>{t("recommendationCashAvailable")}: <strong>{money(item.cash_available)}</strong></p>
              <p>{t("downPayment")}: {money(item.upfront.down_payment)}</p>
              <p>{t("stampDuty")}: {money(item.upfront.stamp_duty)}</p>
              <p>{t("agentFee")}: {money(item.upfront.agent_fee)}</p>
              <p>{t("legalFee")}: {money(item.upfront.legal_fee)}</p>
              <p>{t("insurance")}: {money(item.upfront.insurance_premium)}</p>
              {item.cash_shortfall > 0 && (
                <p className="text-destructive">
                  {t("recommendationShortfall")}: {money(item.cash_shortfall)}
                </p>
              )}
              <p>{t("recommendationMortgage")}: {money(item.monthly_costs.mortgage)}</p>
              <p>{t("managementFee")}: {money(item.monthly_costs.management_fee)}</p>
              <p>{t("rates")}: {money(item.monthly_costs.rates)}</p>
              <p>{t("governmentRent")}: {money(item.monthly_costs.government_rent)}</p>
              <p>{t("repairs")}: {money(item.monthly_costs.repairs)}</p>
            </>
          )}
          {item.mode === "rent" && item.upfront && (
            <>
              <p>{t("recommendationRentUpfront")}: <strong>{money(item.upfront.total_cash)}</strong></p>
              <p>
                {t("recommendationRentDeposit", { months: item.upfront.rent_deposit_months })}:{" "}
                {money(item.upfront.security_deposit)}
              </p>
              <p>
                {t("recommendationRentAgentFee", { pct: item.upfront.rent_agent_fee_pct })}:{" "}
                {money(item.upfront.agent_fee)}
              </p>
            </>
          )}
          <p>{t("recommendationHousingShare")}: {item.housing_pct.toFixed(1)}%</p>
          {item.mode === "buy" && item.debt_servicing_ratio !== null && (
            <p>{t("recommendationDsr")}: {percent(item.debt_servicing_ratio, 1)}</p>
          )}
          <p>{t("recommendationComfortLimit")}: {money(item.comfortable_budget)}</p>
          <p>{t("recommendationStretchLimit")}: {money(item.stretch_budget)}</p>
          {item.mode === "buy" && <p>{t("recommendationRate")}: {item.mortgage_rate.toFixed(2)}%</p>}
        </div>
        <div className="rounded-lg bg-background/70 p-3 text-[13px]">
          <p className="font-medium">{t("recommendationStressTitle")}</p>
          <p className="mt-1 text-muted-foreground">
            {t(item.mode === "buy" ? "recommendationStressBuy" : "recommendationStressRent", {
              rate: item.stress.rate_increase_pct,
              income: item.stress.income_reduction_pct,
            })}
          </p>
          <p className="mt-1 text-muted-foreground">
            {t("recommendationStressResult", {
              label: t(item.stress.label),
              cost: money(item.stress.monthly_cost),
              income: money(item.stress.monthly_income),
              ratio: item.stress.housing_pct.toFixed(1),
            })}
          </p>
          {item.mode === "buy" && item.stress.debt_servicing_ratio !== null && (
            <p className="mt-1 text-muted-foreground">
              {t("recommendationStressDsr")}: {percent(item.stress.debt_servicing_ratio, 1)}
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2 text-[12px] text-muted-foreground">
          <a href={item.source} target="_blank" rel="noreferrer" className="text-primary">
            {sourceName}
          </a>
          <span>{t("recommendationSnapshotDate", { date: item.source_date ?? snapshotDate })}</span>
          {saved ? (
            <button type="button" onClick={() => removeSavedRecommendation(item.id)} className="text-destructive">
              {t("recommendationRemove")}
            </button>
          ) : (
            <button
              type="button"
              onClick={() => saveRecommendation(item)}
              disabled={savedRecommendations.some((recommendation) => recommendation.id === item.id)}
              className="text-primary disabled:cursor-default disabled:text-muted-foreground"
            >
              {savedRecommendations.some((recommendation) => recommendation.id === item.id)
                ? t("recommendationSaved")
                : t("recommendationSave")}
            </button>
          )}
        </div>
      </article>
    )
  }

  return (
    <div className="mx-auto grid max-w-5xl gap-8 lg:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
      <div className="space-y-7">
        <Section title={t("affordabilityTitle")} footer={t("affordabilitySubtitle")}>
          <Row label={t("income")} hint={t("affordabilityIncomeHint")} htmlFor="affordability-income">
            <NumberField id="affordability-income" value={income} onChange={setIncome} prefix="$" />
          </Row>
          <Row label={t("monthlyExistingPayments")} htmlFor="affordability-debt">
            <NumberField id="affordability-debt" value={existingPayments} onChange={setExistingPayments} prefix="$" />
          </Row>
          <Row label={t("downPaymentFunds")} hint={t("downPaymentFundsHint")} htmlFor="affordability-down-payment">
            <NumberField id="affordability-down-payment" value={downPayment} onChange={setDownPayment} prefix="$" />
          </Row>
        </Section>
        <Section title={t("assumptions")}>
          <Row label={t("affordabilityRate")}>
            <span className="tabular-nums text-foreground">{result ? `${result.mortgage_rate.toFixed(2)}%` : "—"}</span>
          </Row>
          <p className="py-3 text-[13px] leading-snug text-muted-foreground">{t("affordabilityAssumptions")}</p>
          <p className="py-3 text-[13px] leading-snug text-muted-foreground">{t("affordabilityLimits")}</p>
        </Section>
        <Section title={t("estateRecommendationsTitle")} footer={t("recommendationInputHint")}>
          <Row label={t("takeHome")} hint={t("takeHomeHint")} htmlFor="recommendation-take-home">
            <NumberField id="recommendation-take-home" value={takeHomeIncome} onChange={setTakeHomeIncome} prefix="$" />
          </Row>
          <Row label={t("area")} htmlFor="recommendation-area">
            <NumberField id="recommendation-area" value={saleableArea} onChange={setSaleableArea} suffix={t("sqft")} />
          </Row>
          <Row label={t("recommendationSavings")} htmlFor="recommendation-savings">
            <NumberField id="recommendation-savings" value={savings} onChange={setSavings} prefix="$" />
          </Row>
          <Row
            label={t("recommendationPreferredPayment")}
            hint={t("recommendationPreferredPaymentHint")}
            htmlFor="recommendation-preferred"
          >
            <NumberField id="recommendation-preferred" value={preferredPayment} onChange={setPreferredPayment} prefix="$" />
          </Row>
          <Row label={t("recommendationComfort")} htmlFor="recommendation-comfort">
            <NumberField id="recommendation-comfort" value={comfortablePct} onChange={setComfortablePct} suffix="%" />
          </Row>
          <Row label={t("firstTime")} hint={t("firstTimeHint")} htmlFor="recommendation-first-time">
            <Switch
              id="recommendation-first-time"
              checked={firstTime}
              onCheckedChange={setFirstTime}
              aria-label={t("firstTime")}
            />
          </Row>
          <Row label={t("recommendationRentDepositMonths")} htmlFor="recommendation-rent-deposit">
            <NumberField
              id="recommendation-rent-deposit"
              value={rentDepositMonths}
              onChange={setRentDepositMonths}
              suffix={t("monthsUnit")}
            />
          </Row>
          <Row label={t("recommendationRentAgentFeePct")} htmlFor="recommendation-rent-agent-fee">
            <NumberField
              id="recommendation-rent-agent-fee"
              value={rentAgentFeePct}
              onChange={setRentAgentFeePct}
              suffix="%"
            />
          </Row>
          <Row label={t("recommendationRegion")} htmlFor="recommendation-region">
            <Select
              value={region || "all"}
              onValueChange={(value) => {
                setRegion(value === "all" ? "" : value)
                setDistrict("")
                setBedrooms("")
              }}
            >
              <SelectTrigger id="recommendation-region" className="h-8 border-0 px-1 shadow-none">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("locationAll")}</SelectItem>
                {regionOptions.map((estate) => (
                  <SelectItem key={estate.region_en} value={estate.region_en}>
                    {optionName(estate.region_en, estate.region_zh)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Row>
          <Row label={t("recommendationDistrict")} htmlFor="recommendation-district">
            <Select
              value={district || "all"}
              onValueChange={(value) => {
                setDistrict(value === "all" ? "" : value)
                setBedrooms("")
              }}
            >
              <SelectTrigger id="recommendation-district" className="h-8 border-0 px-1 shadow-none">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("locationAll")}</SelectItem>
                {districtOptions.map((estate) => (
                  <SelectItem key={estate.district_en} value={estate.district_en}>
                    {optionName(estate.district_en, estate.district_zh)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Row>
          <Row label={t("recommendationBedrooms")} htmlFor="recommendation-bedrooms">
            <Select
              value={bedrooms || "all"}
              onValueChange={(value) => setBedrooms(value === "all" ? "" : value)}
            >
              <SelectTrigger id="recommendation-bedrooms" className="h-8 border-0 px-1 shadow-none">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("locationAll")}</SelectItem>
                {bedroomOptions.map((bedroom) => (
                  <SelectItem key={bedroom} value={bedroom}>
                    {t("bedroomCount", { n: bedroom })}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Row>
        </Section>
      </div>

      <div className="space-y-7">
        {result ? (
          <>
            <Section title={t("maxHomePrice")}>
              <Row label={t("maxHomePrice")}>
                <span className="text-[22px] font-bold text-foreground">{money(result.maximum_property_price)}</span>
              </Row>
              <Row label={t("maxMortgage")}>{money(result.maximum_mortgage)}</Row>
              <Row label={t("monthlyMortgage")}>{money(result.monthly_mortgage_payment)}</Row>
              <Row label={t("debtToIncome")}>{percent(result.debt_to_income_ratio, 1)}</Row>
            </Section>
            <Section title={t("stressTest")}>
              <p className="py-3 text-[13px] leading-snug text-muted-foreground">
                {t("stressHint", { rate: result.stress_rate.toFixed(2) })}
              </p>
              <Row label={t("stressPrice", { rate: result.stress_rate.toFixed(2) })}>
                {money(result.stress_maximum_property_price)}
              </Row>
              <Row label={t("stressDti", { rate: result.stress_rate.toFixed(2) })}>
                <span className={cn(result.stress_debt_to_income_ratio > 0.5 && "text-destructive")}>
                  {percent(result.stress_debt_to_income_ratio, 1)}
                </span>
              </Row>
            </Section>
          </>
        ) : (
          <p className="rounded-[var(--radius)] bg-card p-5 text-[15px] text-muted-foreground">
            {error ? t("affordabilityCalculationError", { error }) : t("affordabilityEnterInputs")}
          </p>
        )}

        <Section title={t("recommendationResults")} footer={t("recommendationDisclaimer")}>
          <div className="space-y-3 py-3">
            {recommendationLoading ? (
              <p className="text-[14px] text-muted-foreground">{t("loading")}</p>
            ) : recommendationError ? (
              <p className="text-[14px] text-destructive">
                {t("recommendationError", { error: recommendationError })}
              </p>
            ) : !recommendationInputs ? (
              <p className="text-[14px] text-muted-foreground">{t("recommendationEnterInputs")}</p>
            ) : recommendations?.length ? (
              recommendations.map((item) => recommendationCard(item))
            ) : (
              <p className="text-[14px] text-muted-foreground">{t("recommendationNoMatches")}</p>
            )}
          </div>
          <p className="pb-3 text-[13px] leading-snug text-muted-foreground">{t("recommendationUnsupported")}</p>
        </Section>
        <Section title={t("recommendationShortlist")}>
          <div className="space-y-3 py-3">
            {storageStatus && (
              <p className="text-[13px] text-muted-foreground">
                {t(storageStatus === "unavailable" ? "recommendationStorageUnavailable" : "recommendationStorageInvalid")}
              </p>
            )}
            {savedRecommendations.length
              ? savedRecommendations.map((item) => recommendationCard(item, true))
              : <p className="text-[13px] text-muted-foreground">{t("recommendationShortlistEmpty")}</p>}
          </div>
        </Section>
      </div>
    </div>
  )
}

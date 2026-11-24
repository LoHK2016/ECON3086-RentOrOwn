import { useEffect, useState } from "react"
import { NumberField, Row, Section, parsed } from "@/components/grouped"
import { translate, type Lang } from "@/i18n"
import { calculateAffordability, type PlanRates } from "@/lib/python"
import type { AffordabilityResult } from "@/lib/types"
import { money, percent } from "@/lib/format"
import { cn } from "@/lib/utils"

export function Affordability({ lang, rates }: { lang: Lang; rates: PlanRates }) {
  const t = (key: Parameters<typeof translate>[1], values?: Record<string, string | number>) =>
    translate(lang, key, values)
  const [income, setIncome] = useState("")
  const [existingPayments, setExistingPayments] = useState("0")
  const [downPayment, setDownPayment] = useState("")
  const [result, setResult] = useState<AffordabilityResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const monthlyIncome = parsed(income)
  const monthlyDebt = parsed(existingPayments)
  const downPaymentFunds = parsed(downPayment)

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
      </div>
    </div>
  )
}

import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it } from "vitest"
import { PdfReport } from "@/components/PdfReport"
import type { BankPlan, Estate, Flat, Result, ScenarioName, Snapshot } from "@/lib/types"

const estate: Estate = {
  id: "harbour-view",
  name_en: "Harbour View",
  name_zh: "海景花園",
  region_en: "Hong Kong Island",
  region_zh: "香港島",
  district_en: "Eastern",
  district_zh: "東區",
  price_per_ft: 12_000,
  rent_per_ft: 40,
  transactions: 12,
  source: "https://example.com/estate",
  price_source: "midland",
  hsbc: null,
}

const plan: BankPlan = {
  bank: "Example Bank",
  hibor_spread: 1.3,
  prime_discount: 1.75,
  cash_rebate_pct: 0,
  provisional: true,
}

const flat: Flat = {
  address: "Block 2, 10/F, Flat A",
  valuation: 5_900_000,
  saleable_area: 500,
  gross_area: 600,
  age: 20,
  date: "2026-11-18",
}

function comparison(verdict: "buy" | "rent", gap: number): Result {
  const buyEnd = 1_200_000
  const rentEnd = buyEnd - gap
  return {
    inputs: {
      price: 6_000_000,
      monthly_rent: 20_000,
      saleable_area: 500,
      mortgage_rate: 3.25,
      ltv: 0.7,
      max_ltv: 0.9,
      horizon_years: 2,
      price_growth: 2,
      rent_growth: 1,
      investment_return: 2,
      mortgage_years: 30,
      first_time: true,
      monthly_income: 50_000,
      management_fee_per_ft: 3,
      rates_pct: 5,
      government_rent_pct: 3,
      repair_pct: 0.2,
    },
    verdict,
    gap,
    break_even_year: verdict === "buy" ? 2 : null,
    years: [0, 1, 2],
    buy_net_worth: [1_000_000, 1_100_000, buyEnd],
    rent_net_worth: [1_050_000, 1_100_000, rentEnd],
    upfront: {
      loan: 4_200_000,
      down_payment: 1_800_000,
      stamp_duty: 100_000,
      agent_fee: 60_000,
      legal_fee: 10_000,
      insurance_premium: 0,
      cash_rebate: 0,
      total_cash: 1_970_000,
    },
    monthly_payment: 18_271,
    yearly_costs: [{
      year: 1,
      mortgage: 18_271,
      management_fee: 1_500,
      rates: 1_000,
      government_rent: 600,
      repairs: 1_000,
      owner_monthly: 22_371,
      rent_monthly: 20_000,
    }],
    rental_yield: 0.04,
    debt_servicing_ratio: 0.36542,
    dsr_too_high: false,
  }
}

const scenarios: Record<ScenarioName, Result> = {
  pessimistic: comparison("rent", -250_000),
  neutral: comparison("rent", -50_000),
  optimistic: comparison("buy", 125_000),
}

const snapshot: Snapshot = {
  date: "2026-11-18",
  rates: { hibor_1m: 2.6, hibor_date: "2026-11-18", prime: 5 },
  estates: [estate],
  bank_plans: [plan],
  scenarios: {
    pessimistic: { price_growth: -2, rent_growth: 0 },
    neutral: { price_growth: 2, rent_growth: 1 },
    optimistic: { price_growth: 5, rent_growth: 3 },
  },
  investment_return: { value: 2, provisional: false, bank: "Example Bank" },
}

describe("PDF report", () => {
  it("includes the selected result, assumptions, scenario comparisons, chart, and source context", () => {
    const markup = renderToStaticMarkup(
      <PdfReport
        lang="en"
        estate={estate}
        data={snapshot}
        flat={null}
        result={scenarios.neutral}
        results={scenarios}
        scenario="neutral"
        plan={plan}
        prime={5}
        investmentSource="Example Bank, HKD new funds."
      />,
    )

    assertContains(markup, [
      "Rent or Buy decision report",
      "Renting comes out ahead",
      "$1,250,000",
      "Net worth over time",
      "Example Bank",
      "Assumptions and limitations",
      "Midland Realty",
      "<svg",
    ])
  })

  it("renders a Traditional Chinese report with localized decision and data labels", () => {
    const markup = renderToStaticMarkup(
      <PdfReport
        lang="zh-Hant"
        estate={estate}
        data={snapshot}
        flat={null}
        result={scenarios.neutral}
        results={scenarios}
        scenario="neutral"
        plan={plan}
        prime={5}
        investmentSource="Example Bank"
      />,
    )

    assertContains(markup, ["租定買比較報告", "租樓較著數", "淨資產走勢", "數據來源同更新情況"])
  })

  it("includes the HSBC valuation and date when a specific flat was selected", () => {
    const markup = renderToStaticMarkup(
      <PdfReport
        lang="en"
        estate={estate}
        data={snapshot}
        flat={flat}
        result={scenarios.neutral}
        results={scenarios}
        scenario="neutral"
        plan={plan}
        prime={5}
        investmentSource="Example Bank"
      />,
    )

    assertContains(markup, ["Block 2, 10/F, Flat A", "Bank valuation date", "$5,900,000", "2026-11-18"])
  })
})

function assertContains(markup: string, expected: string[]) {
  for (const text of expected) {
    expect(markup).toContain(text)
  }
}

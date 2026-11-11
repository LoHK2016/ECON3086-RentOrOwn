// Shapes of data/latest.json and of the dict that rentorbuy.compare() returns.

export type Estate = {
  id: string
  name_zh: string
  name_en: string
  district_zh: string
  district_en: string
  price_per_ft: number
  rent_per_ft: number
  transactions: number | null
  source: string
  hsbc: { zoneId: string; districtId: string; estateId: string; name: string } | null
}

/** One choice in HSBC's lookup chain: a block, floor or flat. */
export type Option = { id: string; name: string }

/** A specific Flat as valued by HSBC (rentorbuy.valuation.parse_valuation). */
export type Flat = {
  address: string
  valuation: number
  saleable_area: number | null
  gross_area: number | null
  age: number | null
  date: string
}

export type BankPlan = {
  bank: string
  hibor_spread: number
  prime_discount: number
  provisional: boolean
}

export type Growth = { price_growth: number; rent_growth: number }
export type ScenarioName = "pessimistic" | "neutral" | "optimistic"
export const SCENARIO_NAMES: ScenarioName[] = ["pessimistic", "neutral", "optimistic"]

export type Snapshot = {
  date: string
  rates: { hibor_1m: number; hibor_date: string; prime: number; stale?: boolean }
  estates: Estate[]
  bank_plans: BankPlan[]
  scenarios: Record<ScenarioName, Growth>
  investment_return: { value: number; provisional: boolean }
}

export type Result = {
  inputs: {
    price: number
    monthly_rent: number
    mortgage_rate: number
    ltv: number
    max_ltv: number
    horizon_years: number
    price_growth: number
    rent_growth: number
  }
  verdict: "buy" | "rent"
  gap: number
  break_even_year: number | null
  years: number[]
  buy_net_worth: number[]
  rent_net_worth: number[]
  upfront: {
    loan: number
    down_payment: number
    stamp_duty: number
    agent_fee: number
    legal_fee: number
    insurance_premium: number
    total_cash: number
  }
  monthly_payment: number
  yearly_costs: { year: number; owner_monthly: number; rent_monthly: number }[]
  rental_yield: number
  debt_servicing_ratio: number | null
  dsr_too_high: boolean
}

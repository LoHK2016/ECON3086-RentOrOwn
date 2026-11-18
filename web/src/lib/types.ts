// Shapes of data/latest.json and of the dict that rentorbuy.compare() returns.

export type Estate = {
  id: string
  name_zh: string
  name_en: string
  region_zh: string
  region_en: string
  district_zh: string // one of the 18 districts
  district_en: string
  price_per_ft: number
  rent_per_ft: number
  transactions: number | null
  source: string
  scraped?: string // date of these figures; older than the snapshot if every source failed since
  price_source?: "midland" | "centaline" // Midland: transactions; Centaline: asking prices of listings
  listings?: number // Centaline: how many sale listings the median is taken from
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
  cash_rebate_pct: number
  provisional: boolean
}

export type Growth = { price_growth: number; rent_growth: number }
export type ScenarioName = "pessimistic" | "neutral" | "optimistic"
export const SCENARIO_NAMES: ScenarioName[] = ["pessimistic", "neutral", "optimistic"]

export type Snapshot = {
  date: string
  rates: { hibor_1m: number; hibor_date: string; prime: number; stale?: boolean }
  bank_primes?: Record<string, { prime: number; date: string }>
  estates: Estate[]
  bank_plans: BankPlan[]
  scenarios: Record<ScenarioName, Growth>
  market_benchmark?: {
    source: string
    history_from: string
    history_to: string
    method: string
    observations: number
  }
  investment_return: { value: number; provisional: boolean; bank?: string; months?: string }
  deposits?: Record<string, { rates: Record<string, number>; url: string; date: string }>
  deposit_ranking?: Record<string, { bank: string; rate: number; url: string }[]>
  etf_returns?: Record<string, EtfReturn>
}

/** An index ETF's past return, worked out in rentorbuy/etf_returns.py. */
export type EtfReturn = {
  name: string
  value: number // average % a year over the last `years` years
  years: number
  dividend_tax: number
  worst: number // worst 10-year stretch, % a year
  worst_from: string
  worst_to: string
  losing_share: number // % of 10-year stretches that lost money
  history_from: string
  prices_to: string
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
    management_fee_per_ft: number
    rates_pct: number
    government_rent_pct: number
    repair_pct: number
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
    cash_rebate: number
    total_cash: number
  }
  monthly_payment: number
  yearly_costs: {
    year: number
    mortgage: number
    management_fee: number
    rates: number
    government_rent: number
    repairs: number
    owner_monthly: number
    rent_monthly: number
  }[]
  rental_yield: number
  debt_servicing_ratio: number | null
  dsr_too_high: boolean
}

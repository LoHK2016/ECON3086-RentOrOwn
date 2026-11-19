import type { Lang } from "@/i18n"
import type { Estate, Flat, Result, ScenarioName } from "@/lib/types"

export type ExportData = {
  results: Record<ScenarioName, Result>
  selected: Result
  scenario: ScenarioName
  estate?: Estate
  flat?: Flat | null
  lang: Lang
}

function csvCell(value: unknown): string {
  if (value === null || value === undefined) return ""
  let text = String(value)
  if (/^[=+@-]/.test(text)) text = `'${text}`
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}

function csvTable(headers: string[], rows: unknown[][]): string {
  return [
    headers.map(csvCell).join(","),
    ...rows.map((row) => row.map(csvCell).join(",")),
  ].join("\r\n")
}

function downloadBlob(contents: BlobPart, type: string, filename: string) {
  const url = URL.createObjectURL(new Blob([contents], { type }))
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

function filename(kind: "csv" | "xlsx"): string {
  const date = new Date().toISOString().slice(0, 10)
  return `rent-or-buy-hk-${date}.${kind}`
}

function labels(lang: Lang) {
  const zh = lang === "zh-Hant"
  return {
    year: zh ? "年份" : "Year",
    buy: zh ? "買樓淨資產" : "Buying net worth",
    rent: zh ? "租樓淨資產" : "Renting net worth",
    scenario: zh ? "市況" : "Scenario",
    verdict: zh ? "結果" : "Verdict",
    gap: zh ? "淨資產差距" : "Net worth gap",
    breakEven: zh ? "打和年期" : "Break-even year",
    item: zh ? "項目" : "Item",
    value: zh ? "數值" : "Value",
  }
}

export function exportCsv(data: ExportData) {
  const l = labels(data.lang)
  const zh = data.lang === "zh-Hant"
  const title = zh ? "租買比較報告" : "Rent or Buy Analysis"
  const exportDate = zh ? "匯出日期" : "Export date"
  const property = zh ? "物業資料" : "Property"
  const estateLabel = zh ? "屋苑" : "Estate"
  const addressLabel = zh ? "單位地址" : "Flat address"
  const flatAreaLabel = zh ? "實用面積（平方呎）" : "Saleable area (sq ft)"
  const valuationLabel = zh ? "銀行估價" : "Bank valuation"
  const assumptions = zh ? "輸入假設" : "Input assumptions"
  const summary = zh ? "分析摘要" : "Analysis summary"
  const netWorth = zh ? "淨資產走勢" : "Net worth over time"
  const dayOne = zh ? "上會當日成本" : "Day-one costs"
  const yearlyCosts = zh ? "年度成本" : "Yearly costs"
  const item = zh ? "項目" : "Item"
  const value = zh ? "數值" : "Value"

  const blocks: string[] = [
    csvTable([title], [[title]]),
    csvTable([exportDate, new Date().toISOString().slice(0, 10)], []),
    "",
    csvTable([property], [[property]]),
    csvTable([item, value], [
      [estateLabel, data.estate?.name_zh ?? data.estate?.name_en ?? ""],
      [zh ? "屋苑英文名稱" : "Estate (English)", data.estate?.name_en ?? ""],
      [addressLabel, data.flat?.address ?? ""],
      [flatAreaLabel, data.flat?.saleable_area ?? ""],
      [valuationLabel, data.flat?.valuation ?? data.selected.inputs.price],
    ]),
    "",
    csvTable([assumptions], [[assumptions]]),
    csvTable([item, value], [
      [zh ? "選定市況" : "Selected scenario", data.scenario],
      [zh ? "成交價" : "Purchase price", data.selected.inputs.price],
      [zh ? "月租" : "Monthly rent", data.selected.inputs.monthly_rent],
      [zh ? "按揭利率（%）" : "Mortgage rate (%)", data.selected.inputs.mortgage_rate],
      [zh ? "按揭成數" : "Loan-to-value", data.selected.inputs.ltv],
      [zh ? "最高按揭成數" : "Maximum LTV", data.selected.inputs.max_ltv],
      [zh ? "持有年期" : "Horizon years", data.selected.inputs.horizon_years],
      [zh ? "樓價年增長（%）" : "Price growth (%)", data.selected.inputs.price_growth],
      [zh ? "租金年增長（%）" : "Rent growth (%)", data.selected.inputs.rent_growth],
      [zh ? "管理費每呎" : "Management fee per sq ft", data.selected.inputs.management_fee_per_ft],
      [zh ? "差餉（%）" : "Rates (%)", data.selected.inputs.rates_pct],
      [zh ? "地租（%）" : "Government rent (%)", data.selected.inputs.government_rent_pct],
      [zh ? "維修（%）" : "Repairs (%)", data.selected.inputs.repair_pct],
    ]),
    "",
    csvTable([summary], [[summary]]),
    csvTable([l.scenario, l.verdict, l.gap, l.breakEven], [
      ...(["pessimistic", "neutral", "optimistic"] as ScenarioName[]).map((name) => {
        const result = data.results[name]
        return [name, result.verdict, result.gap, result.break_even_year ?? ""]
      }),
    ]),
    "",
    csvTable([netWorth], [[netWorth]]),
    csvTable([l.year, l.buy, l.rent], [
      ...data.selected.years.map((year, index) => [
        year,
        data.selected.buy_net_worth[index],
        data.selected.rent_net_worth[index],
      ]),
    ]),
    "",
    csvTable([dayOne], [[dayOne]]),
    csvTable([item, value], [
      [zh ? "首期" : "Down payment", data.selected.upfront.down_payment],
      [zh ? "印花稅" : "Stamp duty", data.selected.upfront.stamp_duty],
      [zh ? "代理佣金" : "Agent fee", data.selected.upfront.agent_fee],
      [zh ? "律師費" : "Legal fee", data.selected.upfront.legal_fee],
      [zh ? "按揭保險" : "Mortgage insurance", data.selected.upfront.insurance_premium],
      [zh ? "現金回贈" : "Cash rebate", data.selected.upfront.cash_rebate],
      [zh ? "合共要預備" : "Cash needed", data.selected.upfront.total_cash],
      [zh ? "貸款額" : "Loan", data.selected.upfront.loan],
      [zh ? "每月供款" : "Monthly mortgage payment", data.selected.monthly_payment],
      [zh ? "租金回報率" : "Rental yield", data.selected.rental_yield],
      [zh ? "供款與入息比率" : "Debt servicing ratio", data.selected.debt_servicing_ratio],
    ]),
    "",
    csvTable([yearlyCosts], [[yearlyCosts]]),
    csvTable([l.year, "Mortgage", "Management", "Rates", "Government rent", "Repairs", "Owner monthly", "Rent monthly"], [
      ...data.selected.yearly_costs.map((cost) => [
        cost.year,
        cost.mortgage,
        cost.management_fee,
        cost.rates,
        cost.government_rent,
        cost.repairs,
        cost.owner_monthly,
        cost.rent_monthly,
      ]),
    ]),
  ]

  const csv = blocks.join("\r\n")
  downloadBlob("\uFEFF" + csv, "text/csv;charset=utf-8", filename("csv"))
}

export async function exportXlsx(data: ExportData) {
  const XLSX = await import("xlsx")
  const l = labels(data.lang)
  const workbook = XLSX.utils.book_new()

  const summary = [
    [l.scenario, l.verdict, l.gap, l.breakEven],
    ...(["pessimistic", "neutral", "optimistic"] as ScenarioName[]).map((name) => {
      const result = data.results[name]
      return [
        name,
        result.verdict,
        result.gap,
        result.break_even_year ?? "",
      ]
    }),
  ]
  XLSX.utils.book_append_sheet(workbook, XLSX.utils.aoa_to_sheet(summary), "Summary")

  const netWorthHeaders = [
    l.year,
    `${l.buy} - Pessimistic`,
    `${l.rent} - Pessimistic`,
    `${l.buy} - Neutral`,
    `${l.rent} - Neutral`,
    `${l.buy} - Optimistic`,
    `${l.rent} - Optimistic`,
  ]
  const first = data.results.neutral
  const netWorthRows = first.years.map((year, index) => [
    year,
    data.results.pessimistic.buy_net_worth[index],
    data.results.pessimistic.rent_net_worth[index],
    data.results.neutral.buy_net_worth[index],
    data.results.neutral.rent_net_worth[index],
    data.results.optimistic.buy_net_worth[index],
    data.results.optimistic.rent_net_worth[index],
  ])
  XLSX.utils.book_append_sheet(
    workbook,
    XLSX.utils.aoa_to_sheet([netWorthHeaders, ...netWorthRows]),
    "Net Worth",
  )

  const costHeaders = [
    l.year,
    "Mortgage",
    "Management",
    "Rates",
    "Government rent",
    "Repairs",
    "Owner monthly",
    "Rent monthly",
  ]
  const costRows = data.selected.yearly_costs.map((cost) => [
    cost.year,
    cost.mortgage,
    cost.management_fee,
    cost.rates,
    cost.government_rent,
    cost.repairs,
    cost.owner_monthly,
    cost.rent_monthly,
  ])
  XLSX.utils.book_append_sheet(
    workbook,
    XLSX.utils.aoa_to_sheet([costHeaders, ...costRows]),
    "Yearly Costs",
  )

  const assumptions = [
    [l.item, l.value],
    ["Estate", data.estate?.name_en ?? data.estate?.name_zh ?? ""],
    ["Estate (Traditional Chinese)", data.estate?.name_zh ?? ""],
    ["Flat address", data.flat?.address ?? ""],
    ["Saleable area (sq ft)", data.flat?.saleable_area ?? ""],
    ["Bank valuation", data.flat?.valuation ?? ""],
    ["Purchase price", data.selected.inputs.price],
    ["Monthly rent", data.selected.inputs.monthly_rent],
    ["Mortgage rate", data.selected.inputs.mortgage_rate],
    ["LTV", data.selected.inputs.ltv],
    ["Horizon years", data.selected.inputs.horizon_years],
    ["Price growth", data.selected.inputs.price_growth],
    ["Rent growth", data.selected.inputs.rent_growth],
  ]
  XLSX.utils.book_append_sheet(
    workbook,
    XLSX.utils.aoa_to_sheet(assumptions),
    "Assumptions",
  )

  XLSX.writeFile(workbook, filename("xlsx"))
}

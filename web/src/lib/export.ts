import type { Lang } from "@/i18n"
import type { Estate, Result, ScenarioName } from "@/lib/types"

export type ExportData = {
  results: Record<ScenarioName, Result>
  selected: Result
  scenario: ScenarioName
  estate?: Estate
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
  const headers = [l.year, l.buy, l.rent]
  const rows = data.selected.years.map((year, index) => [
    year,
    data.selected.buy_net_worth[index],
    data.selected.rent_net_worth[index],
  ])
  const csv = csvTable(headers, rows)
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

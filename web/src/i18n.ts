// Every word on the page, in each language. To add a language, add one more block
// with the same keys and list it in LANGUAGES.

export const LANGUAGES = {
  en: "English",
  "zh-Hant": "繁體中文",
} as const

export type Lang = keyof typeof LANGUAGES

const en = {
  title: "Rent or Buy?",
  subtitle: "Should you buy this Hong Kong home, or rent it and invest the difference?",
  loading: "Loading the calculator…",
  loadError: "The calculator could not load. Check your connection and refresh the page.",

  home: "The home",
  estate: "Estate",
  area: "Saleable area",
  sqft: "sq ft",
  price: "Purchase price",
  rent: "Monthly rent",
  valuation: "Bank valuation",
  optional: "Optional",
  typical: "Typical",
  reset: "Reset",
  perFt: "/ sq ft",
  estateFacts: "{price} per sq ft · {rent} rent per sq ft · {tx} recent transactions",
  flatMode: "Flat",
  typicalFlat: "Typical flat",
  specificFlat: "Specific flat",
  block: "Block",
  floor: "Floor",
  flat: "Flat",
  choose: "Choose",
  askingHsbc: "Asking HSBC…",
  hsbcError: "HSBC did not answer.",
  retry: "Try again",
  hsbcValuation: "HSBC valuation",
  flatFacts: "{area} sq ft saleable · {gross} sq ft gross · {age} years old · valued {date}",
  noHsbc: "This estate is not in HSBC's valuation tool.",

  you: "You",
  firstTime: "First-time buyer",
  firstTimeHint: "Own no other HK home and are salaried. Allows a 90% mortgage under $10M.",
  permanentResident: "Permanent resident",
  permanentResidentHint: "Stamp duty has been the same for everyone since Feb 2024.",
  income: "Monthly income",
  incomeHint: "Optional. Used to check the 50% debt servicing ratio.",

  mortgage: "Mortgage",
  bank: "Bank",
  ltv: "Loan-to-value",
  ltvMax: "Max {max} for this price",
  term: "Term",
  years: "years",
  rate: "Interest rate",
  rateFormula: "1M HIBOR {hibor}% + {spread}%, capped at prime {prime}% − {discount}%",
  ratesMove: "If rates…",
  rateDown: "Fall 1%",
  rateNow: "Stay",
  rateUp: "Rise 1%",

  assumptions: "Assumptions",
  horizon: "Compare over",
  invest: "Investment return",
  investHint: "What the renter earns on money not spent on the home.",
  scenario: "Market",
  pessimistic: "Pessimistic",
  neutral: "Neutral",
  optimistic: "Optimistic",
  scenarioGrowth: "Prices {price}% a year, rent {rent}% a year",

  buyWins: "Buying comes out ahead",
  rentWins: "Renting comes out ahead",
  by: "by {gap} after {years} years",
  breakEven: "Buying overtakes renting in year {year}.",
  neverBreakEven: "Buying does not catch up within {years} years.",
  inEachScenario: "In each market",
  netWorth: "Net worth over time",
  netWorthHint: "If you sold the home at the end, after paying off the mortgage.",
  buying: "Buying",
  renting: "Renting",
  year: "Year {n}",

  dayOne: "Day one",
  downPayment: "Down payment",
  stampDuty: "Stamp duty",
  agentFee: "Agent fee",
  legalFee: "Legal fee",
  insurance: "Mortgage insurance",
  cashNeeded: "Cash needed",
  loan: "Loan",

  firstYear: "Each month, year 1",
  repayment: "Mortgage repayment",
  ownerCosts: "Owner's total (incl. management fee, rates, repairs)",
  renterCosts: "Rent",

  reference: "For reference",
  rentalYield: "Rental yield",
  dsr: "Debt servicing ratio",
  dsrTooHigh: "Above the 50% limit: banks would likely refuse this loan.",

  provisional: "Provisional",
  limitsTitle: "What this can't tell you",
  limits: [
    "The future. Price and rent growth are three fixed scenarios, not a forecast.",
    "What you would really pay. A typical flat uses estate-wide averages; a specific flat uses HSBC's valuation, and the price you agree can differ from both.",
    "Bank offers change weekly. Cash rebates and special terms are not included.",
    "Taxes on investment returns, moving costs and renovation are left out.",
    "Rates are held fixed for the whole period, apart from the rise / fall buttons.",
  ],
  dataTitle: "Where the numbers come from",
  dataEstate: "Estate prices and rents: Midland Realty, scraped {date}.",
  dataRates: "HIBOR and prime rate: HKMA open API ({date}).",
  dataHsbc: "Specific flats: HSBC's online valuation tool, asked live from your browser. Rent is still the estate's average per sq ft.",
  dataStale: "The HKMA API was unavailable today, so these are the last known rates.",
  dataManual: "Bank plan terms, mortgage insurance premiums and the market scenarios are provisional and still being checked.",
  footer: "An ECON3086 group project. Not financial advice.",
}

export type Strings = typeof en

const zhHant: Strings = {
  title: "租定買？",
  subtitle: "呢個香港單位，應該買，定係租住然後將差額拎去投資？",
  loading: "載入計算機中…",
  loadError: "計算機載入唔到，請檢查網絡再重新整理。",

  home: "單位",
  estate: "屋苑",
  area: "實用面積",
  sqft: "平方呎",
  price: "成交價",
  rent: "月租",
  valuation: "銀行估價",
  optional: "選填",
  typical: "參考",
  reset: "還原",
  perFt: "／呎",
  estateFacts: "實用呎價 {price} · 呎租 {rent} · 近期成交 {tx} 宗",
  flatMode: "單位",
  typicalFlat: "屋苑平均",
  specificFlat: "指定單位",
  block: "座數",
  floor: "樓層",
  flat: "單位",
  choose: "請選擇",
  askingHsbc: "正向滙豐查詢…",
  hsbcError: "滙豐冇回應。",
  retry: "再試",
  hsbcValuation: "滙豐估價",
  flatFacts: "實用 {area} 呎 · 建築 {gross} 呎 · 樓齡 {age} 年 · 估價日期 {date}",
  noHsbc: "滙豐估價工具冇呢個屋苑。",

  you: "你",
  firstTime: "首次置業",
  firstTimeHint: "名下冇其他香港住宅並受薪。一千萬以下可借九成。",
  permanentResident: "香港永久居民",
  permanentResidentHint: "2024 年 2 月起，所有買家印花稅一樣。",
  income: "每月收入",
  incomeHint: "選填，用嚟檢查 50% 供款與入息比率。",

  mortgage: "按揭",
  bank: "銀行",
  ltv: "按揭成數",
  ltvMax: "呢個價錢最高 {max}",
  term: "年期",
  years: "年",
  rate: "按揭利率",
  rateFormula: "一個月 HIBOR {hibor}% + {spread}%，上限為最優惠利率 {prime}% − {discount}%",
  ratesMove: "如果利率…",
  rateDown: "跌 1%",
  rateNow: "不變",
  rateUp: "升 1%",

  assumptions: "假設",
  horizon: "比較年期",
  invest: "投資回報率",
  investHint: "租客將冇用嚟買樓嘅錢拎去投資，每年賺幾多。",
  scenario: "市況",
  pessimistic: "悲觀",
  neutral: "中性",
  optimistic: "樂觀",
  scenarioGrowth: "樓價每年 {price}%，租金每年 {rent}%",

  buyWins: "買樓較著數",
  rentWins: "租樓較著數",
  by: "{years} 年後多 {gap}",
  breakEven: "第 {year} 年起買樓超越租樓。",
  neverBreakEven: "{years} 年內買樓都追唔上租樓。",
  inEachScenario: "唔同市況下",
  netWorth: "淨資產走勢",
  netWorthHint: "假設最後賣出單位、還清按揭後計。",
  buying: "買樓",
  renting: "租樓",
  year: "第 {n} 年",

  dayOne: "上會當日",
  downPayment: "首期",
  stampDuty: "印花稅",
  agentFee: "代理佣金",
  legalFee: "律師費",
  insurance: "按揭保險",
  cashNeeded: "合共要預備",
  loan: "貸款額",

  firstYear: "第一年每月",
  repayment: "按揭供款",
  ownerCosts: "業主總開支（包括管理費、差餉地租、維修）",
  renterCosts: "租金",

  reference: "參考數字",
  rentalYield: "租金回報率",
  dsr: "供款與入息比率",
  dsrTooHigh: "超過 50% 上限，銀行好可能唔批呢筆貸款。",

  provisional: "暫定",
  limitsTitle: "呢個工具答唔到嘅嘢",
  limits: [
    "將來。樓價同租金升幅只係三個固定情景，唔係預測。",
    "你實際要俾幾多錢。屋苑平均用全屋苑每呎平均價，指定單位用滙豐估價，真正成交價可以同兩者都唔同。",
    "銀行優惠每星期都變，現金回贈同特別條款冇計入。",
    "投資回報嘅稅、搬屋同裝修費用冇計入。",
    "除咗升跌掣，利率喺整段時間都當作不變。",
  ],
  dataTitle: "數字嘅來源",
  dataEstate: "屋苑呎價同呎租：美聯物業，{date} 擷取。",
  dataRates: "HIBOR 同最優惠利率：金管局開放 API（{date}）。",
  dataHsbc: "指定單位：由你嘅瀏覽器即時查詢滙豐網上估價。租金仍然用屋苑每呎平均。",
  dataStale: "今日金管局 API 用唔到，以下係最近一次嘅利率。",
  dataManual: "銀行按揭計劃條款、按揭保險保費同市況情景係暫定數字，仲喺度核對。",
  footer: "ECON3086 小組專題。並非投資建議。",
}

export const STRINGS: Record<Lang, Strings> = { en, "zh-Hant": zhHant }

type TextKey = { [K in keyof Strings]: Strings[K] extends string ? K : never }[keyof Strings]

/** Look up a phrase and fill in {placeholders}. */
export function translate(lang: Lang, key: TextKey, values: Record<string, string | number> = {}): string {
  let text = STRINGS[lang][key]
  for (const [name, value] of Object.entries(values)) {
    text = text.replace(`{${name}}`, String(value))
  }
  return text
}

export function defaultLang(): Lang {
  try {
    const saved = localStorage.getItem("lang")
    if (saved && saved in LANGUAGES) return saved as Lang
  } catch {
    // Storage can be blocked; fall back to the browser language.
  }
  return navigator.language.toLowerCase().startsWith("zh") ? "zh-Hant" : "en"
}

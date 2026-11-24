import type { Lang } from "@/i18n"

export function money(value: number): string {
  const sign = value < 0 ? "−" : ""
  return sign + "$" + Math.round(Math.abs(value)).toLocaleString("en-HK")
}

/** Short money for chart axes: $6.3M in English, 630萬 in Chinese. */
export function shortMoney(value: number, lang: Lang): string {
  const sign = value < 0 ? "−" : ""
  const v = Math.abs(value)
  if (lang === "zh-Hant") {
    if (v >= 1e8) return `${sign}${(v / 1e8).toFixed(1)}億`
    if (v >= 1e4) return `${sign}${Math.round(v / 1e4)}萬`
    return sign + String(Math.round(v))
  }
  if (v >= 1e6) return `${sign}$${(v / 1e6).toFixed(1)}M`
  if (v >= 1e3) return `${sign}$${Math.round(v / 1e3)}K`
  return `${sign}$${Math.round(v)}`
}

export function percent(value: number, digits = 1): string {
  return (value * 100).toFixed(digits) + "%"
}

export function formatWan(amount: number): string {
  const abs = Math.abs(amount);
  if (abs >= 10_000) {
    const wan = Math.round(abs / 10_000);
    return `$${wan.toLocaleString()} 萬`;
  }
  return `$${abs.toLocaleString()}`;
}

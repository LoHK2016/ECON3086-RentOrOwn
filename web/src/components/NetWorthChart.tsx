import { Area, CartesianGrid, ComposedChart, Line, ReferenceLine, Tooltip, XAxis, YAxis } from "recharts"
import { ChartContainer, type ChartConfig } from "@/components/ui/chart"
import { translate, type Lang } from "@/i18n"
import { money, shortMoney } from "@/lib/format"
import type { Result } from "@/lib/types"

type Point = {
  year: number
  buy: [number, number]
  rent: [number, number]
  buyPoint: number
  rentPoint: number
}

function ChartTip({ active, payload, lang }: { active?: boolean; payload?: { payload: Point }[]; lang: Lang }) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  return (
    <div className="rounded-xl border bg-popover px-3 py-2 text-[13px] shadow-lg">
      <div className="mb-1 font-semibold">{translate(lang, "year", { n: point.year })}</div>
      <div className="flex items-center justify-between gap-4">
        <span className="flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-chart-1" />
          {translate(lang, "buying")}
        </span>
        <span className="tabular-nums">{money(point.buy[0])}–{money(point.buy[1])}</span>
      </div>
      <div className="flex items-center justify-between gap-4">
        <span className="flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-chart-2" />
          {translate(lang, "renting")}
        </span>
        <span className="tabular-nums">{money(point.rent[0])}–{money(point.rent[1])}</span>
      </div>
    </div>
  )
}

export function NetWorthChart({
  point,
  low,
  high,
  lang,
}: {
  point: Result
  low: Result
  high: Result
  lang: Lang
}) {
  const config: ChartConfig = {
    buy: { label: translate(lang, "buying"), color: "var(--chart-1)" },
    rent: { label: translate(lang, "renting"), color: "var(--chart-2)" },
  }
  const data: Point[] = point.years.map((year, i) => ({
    year,
    buy: [
      Math.min(low.buy_net_worth[i], high.buy_net_worth[i]),
      Math.max(low.buy_net_worth[i], high.buy_net_worth[i]),
    ],
    rent: [
      Math.min(low.rent_net_worth[i], high.rent_net_worth[i]),
      Math.max(low.rent_net_worth[i], high.rent_net_worth[i]),
    ],
    buyPoint: point.buy_net_worth[i],
    rentPoint: point.rent_net_worth[i],
  }))
  return (
    <ChartContainer config={config} className="aspect-auto h-64 w-full">
      <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="year" tickLine={false} axisLine={false} tickMargin={8} />
        <YAxis
          width={56}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value: number) => shortMoney(value, lang)}
        />
        {point.break_even_year !== null && (
          <ReferenceLine x={point.break_even_year} stroke="var(--muted-foreground)" strokeDasharray="4 4" />
        )}
        <Tooltip content={<ChartTip lang={lang} />} />
        <Area dataKey="buy" type="monotone" stroke="none" fill="var(--color-buy)" fillOpacity={0.16} />
        <Area dataKey="rent" type="monotone" stroke="none" fill="var(--color-rent)" fillOpacity={0.16} />
        <Line dataKey="buyPoint" type="monotone" stroke="var(--color-buy)" strokeWidth={2.5} dot={false} />
        <Line dataKey="rentPoint" type="monotone" stroke="var(--color-rent)" strokeWidth={2.5} dot={false} />
      </ComposedChart>
    </ChartContainer>
  )
}

import { CartesianGrid, Line, LineChart, ReferenceLine, Tooltip, XAxis, YAxis } from "recharts"
import { ChartContainer, type ChartConfig } from "@/components/ui/chart"
import { translate, type Lang } from "@/i18n"
import { money, shortMoney } from "@/lib/format"
import type { Result } from "@/lib/types"

type Point = { year: number; buy: number; rent: number }

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
        <span className="tabular-nums">{money(point.buy)}</span>
      </div>
      <div className="flex items-center justify-between gap-4">
        <span className="flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-chart-2" />
          {translate(lang, "renting")}
        </span>
        <span className="tabular-nums">{money(point.rent)}</span>
      </div>
    </div>
  )
}

export function NetWorthChart({ result, lang }: { result: Result; lang: Lang }) {
  const config: ChartConfig = {
    buy: { label: translate(lang, "buying"), color: "var(--chart-1)" },
    rent: { label: translate(lang, "renting"), color: "var(--chart-2)" },
  }
  const data: Point[] = result.years.map((year, i) => ({
    year,
    buy: result.buy_net_worth[i],
    rent: result.rent_net_worth[i],
  }))
  return (
    <ChartContainer config={config} className="aspect-auto h-64 w-full">
      <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="year" tickLine={false} axisLine={false} tickMargin={8} />
        <YAxis
          width={56}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value: number) => shortMoney(value, lang)}
        />
        {result.break_even_year !== null && (
          <ReferenceLine x={result.break_even_year} stroke="var(--muted-foreground)" strokeDasharray="4 4" />
        )}
        <Tooltip content={<ChartTip lang={lang} />} />
        <Line dataKey="buy" type="monotone" stroke="var(--color-buy)" strokeWidth={2.5} dot={false} />
        <Line dataKey="rent" type="monotone" stroke="var(--color-rent)" strokeWidth={2.5} dot={false} />
      </LineChart>
    </ChartContainer>
  )
}

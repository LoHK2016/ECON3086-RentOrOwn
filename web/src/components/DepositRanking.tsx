// Banks' HKD new-fund time deposit rates, best first. The ranking itself is
// done in Python (rentorbuy/calc/deposits.py) when the data is scraped.

import { useState } from "react"
import { ExternalLink } from "lucide-react"
import { Row, Section, Segmented } from "@/components/grouped"
import { translate, type Lang } from "@/i18n"
import type { Snapshot } from "@/lib/types"
import { cn } from "@/lib/utils"

const TENORS = ["3", "6", "12"]

export function DepositRanking({ data, lang }: { data: Snapshot; lang: Lang }) {
  const t = (key: Parameters<typeof translate>[1], values?: Record<string, string | number>) => translate(lang, key, values)
  const [months, setMonths] = useState("12")
  const offers = data.deposit_ranking?.[months] ?? []
  if (!data.deposit_ranking) return null

  return (
    <Section title={t("depositTitle")} footer={t("depositFooter")}>
      <div className="py-2.5">
        <Segmented
          label={t("depositTitle")}
          value={months}
          onChange={setMonths}
          options={TENORS.map((m) => ({ value: m, label: t("months", { n: m }) }))}
        />
      </div>
      {offers.length === 0 && <Row label={<span className="text-muted-foreground">{t("noOffers")}</span>} />}
      {offers.map((offer, i) => (
        <Row
          key={offer.bank}
          label={
            <a href={offer.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1">
              {i === 0 && <span className="mr-1 rounded-full bg-success/15 px-2 py-0.5 text-[11px] font-semibold text-success">{t("best")}</span>}
              {offer.bank}
              <ExternalLink className="size-3 text-muted-foreground" />
            </a>
          }
          hint={t("readOn", { date: data.deposits?.[offer.bank]?.date ?? data.date })}
        >
          <span className={cn("tabular-nums", i === 0 ? "font-semibold text-success" : "text-foreground")}>
            {offer.rate.toFixed(2)}%
          </span>
        </Row>
      ))}
    </Section>
  )
}

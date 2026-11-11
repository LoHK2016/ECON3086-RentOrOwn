// Pick block, floor and flat from HSBC's valuation tool, then show HSBC's valuation.
// The lookups themselves are Python (rentorbuy/valuation.py), called through lib/python.ts.
// Give it key={estate.id} so a new Estate starts it afresh.

import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"
import { Row } from "@/components/grouped"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { translate, type Lang } from "@/i18n"
import { money } from "@/lib/format"
import { hsbcOptions, hsbcValuation, type Chosen } from "@/lib/python"
import type { Estate, Flat, Option } from "@/lib/types"

type Level = "blockId" | "floor" | "flat"
const LEVELS: Level[] = ["blockId", "floor", "flat"]

function Picker({
  label,
  options,
  value,
  onChange,
  loading,
  placeholder,
}: {
  label: string
  options: Option[] | null
  value: string
  onChange: (id: string) => void
  loading: boolean
  placeholder: string
}) {
  return (
    <Row label={label}>
      {loading && <Loader2 className="size-4 animate-spin" aria-label="loading" />}
      <Select value={value} onValueChange={onChange} disabled={!options || options.length === 0}>
        <SelectTrigger
          aria-label={label}
          className="h-8 max-w-56 border-none bg-transparent pr-0 text-[17px] shadow-none focus-visible:ring-0"
        >
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {(options ?? []).map((option) => (
            <SelectItem key={option.id} value={option.id}>
              {option.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </Row>
  )
}

export function FlatPicker({ estate, lang, onFlat }: { estate: Estate; lang: Lang; onFlat: (flat: Flat | null) => void }) {
  const t = (key: Parameters<typeof translate>[1], values?: Record<string, string | number>) => translate(lang, key, values)
  const locale = lang === "zh-Hant" ? "zh_HK" : "en_HK"
  const base: Chosen = estate.hsbc
    ? { zoneId: estate.hsbc.zoneId, districtId: estate.hsbc.districtId, estateId: estate.hsbc.estateId }
    : {}

  const [picked, setPicked] = useState<Partial<Record<Level, string>>>({})
  const [lists, setLists] = useState<Partial<Record<Level, Option[]>>>({})
  const [busy, setBusy] = useState<Level | "valuation" | null>(null)
  const [failed, setFailed] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const [flat, setFlat] = useState<Flat | null>(null)

  // Ask HSBC for the next list (or the valuation) whenever a choice is made.
  useEffect(() => {
    if (!estate.hsbc) return
    const chosen: Chosen = { ...base }
    let next: Level | "valuation" = "blockId"
    for (const level of LEVELS) {
      if (!picked[level]) {
        next = level
        break
      }
      chosen[level] = picked[level]!
      next = "valuation"
    }
    let current = true
    setFailed(false)
    setBusy(next)
    const request =
      next === "valuation"
        ? hsbcValuation(chosen, locale).then((result) => {
            if (!current) return
            setFlat(result)
            onFlat(result)
          })
        : hsbcOptions(chosen, locale).then((options) => {
            if (current) setLists((old) => ({ ...old, [next]: options }))
          })
    request
      .catch(() => current && setFailed(true))
      .finally(() => current && setBusy(null))
    return () => {
      current = false
    }
  }, [picked, locale, attempt]) // eslint-disable-line react-hooks/exhaustive-deps

  function choose(level: Level, id: string) {
    // Choosing a block clears the floor and flat below it.
    const index = LEVELS.indexOf(level)
    const next: Partial<Record<Level, string>> = {}
    for (const l of LEVELS.slice(0, index)) next[l] = picked[l]
    next[level] = id
    setPicked(next)
    setFlat(null)
    onFlat(null)
  }

  if (!estate.hsbc) {
    return <Row label={<span className="text-muted-foreground">{t("noHsbc")}</span>} />
  }

  const labels: Record<Level, string> = { blockId: t("block"), floor: t("floor"), flat: t("flat") }
  return (
    <>
      {LEVELS.map((level, i) =>
        i === 0 || picked[LEVELS[i - 1]] ? (
          <Picker
            key={level}
            label={labels[level]}
            options={lists[level] ?? null}
            value={picked[level] ?? ""}
            onChange={(id) => choose(level, id)}
            loading={busy === level}
            placeholder={t("choose")}
          />
        ) : null,
      )}
      {busy === "valuation" && (
        <Row label={t("hsbcValuation")}>
          <Loader2 className="size-4 animate-spin" />
          <span className="text-[15px]">{t("askingHsbc")}</span>
        </Row>
      )}
      {failed && (
        <Row label={<span className="text-destructive">{t("hsbcError")}</span>}>
          <button onClick={() => setAttempt((n) => n + 1)} className="text-primary">
            {t("retry")}
          </button>
        </Row>
      )}
      {flat && (
        <Row
          label={t("hsbcValuation")}
          hint={
            <>
              {flat.address}
              <br />
              {t("flatFacts", {
                area: flat.saleable_area ?? "–",
                gross: flat.gross_area ?? "–",
                age: flat.age ?? "–",
                date: flat.date,
              })}
            </>
          }
        >
          <span className="font-semibold text-foreground">{money(flat.valuation)}</span>
        </Row>
      )}
    </>
  )
}

// iOS-style grouped list: a header, a rounded card, and rows separated by hairlines.

import type { ReactNode } from "react"
import { ToggleGroup as ToggleGroupPrimitive } from "radix-ui"
import { cn } from "@/lib/utils"

export function Section({ title, footer, children }: { title?: ReactNode; footer?: ReactNode; children: ReactNode }) {
  return (
    <section className="space-y-1.5">
      {title && <h2 className="px-4 text-[13px] font-normal uppercase tracking-wide text-muted-foreground">{title}</h2>}
      <div className="divide-y divide-border/70 overflow-hidden rounded-[var(--radius)] bg-card [&>*]:ml-4 [&>*]:pr-4 [&>*:first-child]:border-none">
        {children}
      </div>
      {footer && <p className="px-4 text-[13px] leading-snug text-muted-foreground">{footer}</p>}
    </section>
  )
}

export function Row({
  label,
  hint,
  children,
  htmlFor,
}: {
  label: ReactNode
  hint?: ReactNode
  children?: ReactNode
  htmlFor?: string
}) {
  return (
    <div className="flex min-h-11 items-center justify-between gap-4 py-2 pl-0">
      <div className="min-w-0">
        <label htmlFor={htmlFor} className="block text-[17px] leading-snug">
          {label}
        </label>
        {hint && <p className="mt-0.5 text-[13px] leading-snug text-muted-foreground">{hint}</p>}
      </div>
      <div className="flex shrink-0 items-center gap-2 text-[17px] text-muted-foreground">{children}</div>
    </div>
  )
}

export function Segmented<T extends string>({
  value,
  options,
  onChange,
  label,
  className,
}: {
  value: T
  options: { value: T; label: ReactNode }[]
  onChange: (value: T) => void
  label: string
  className?: string
}) {
  return (
    <ToggleGroupPrimitive.Root
      type="single"
      value={value}
      aria-label={label}
      onValueChange={(next) => next && onChange(next as T)}
      className={cn("grid auto-cols-fr grid-flow-col rounded-[9px] bg-secondary p-0.5", className)}
    >
      {options.map((option) => (
        <ToggleGroupPrimitive.Item
          key={option.value}
          value={option.value}
          className="rounded-[7px] px-3 py-1 text-[13px] font-medium text-foreground transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring data-[state=on]:bg-card data-[state=on]:shadow-[0_3px_8px_rgba(0,0,0,0.12),0_3px_1px_rgba(0,0,0,0.04)]"
        >
          {option.label}
        </ToggleGroupPrimitive.Item>
      ))}
    </ToggleGroupPrimitive.Root>
  )
}

/** A number typed by the user, or empty to use the placeholder (the typical value). */
export function NumberField({
  id,
  value,
  placeholder,
  onChange,
  prefix,
  suffix,
}: {
  id: string
  value: string
  placeholder?: string
  onChange: (value: string) => void
  prefix?: string
  suffix?: string
}) {
  return (
    <span className="flex items-center gap-1">
      {prefix && <span>{prefix}</span>}
      <input
        id={id}
        inputMode="decimal"
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value.replace(/[^0-9.]/g, ""))}
        // Grow with the number so a "$" before it stays next to it.
        style={{ width: `${Math.max((value || placeholder || "").length, 2) + 0.5}ch` }}
        className={cn(
          "max-w-40 min-w-0 bg-transparent text-right text-foreground tabular-nums outline-none placeholder:text-muted-foreground focus:placeholder:text-muted-foreground/50",
        )}
      />
      {suffix && <span>{suffix}</span>}
    </span>
  )
}

/** "1,234,567" for showing a number inside an input placeholder. */
export function digits(value: number | undefined): string {
  return value === undefined ? "" : Math.round(value).toLocaleString("en-HK")
}

/** The typed number, or undefined if the box is empty. */
export function parsed(value: string): number | undefined {
  if (value.trim() === "") return undefined
  const number = Number(value)
  return Number.isFinite(number) ? number : undefined
}

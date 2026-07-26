import type { DealPriority, DealStage, DealStatus } from '~/types/deals'

/** Badge color per pipeline stage (Nuxt UI v4 semantic color aliases). */
export function dealStageColor(stage: DealStage) {
  return ({
    lead: 'neutral',
    qualified: 'info',
    proposal: 'warning',
    won: 'success',
    lost: 'error',
  } as const)[stage] ?? 'neutral'
}

/** Badge color per deal status. */
export function dealStatusColor(status: DealStatus) {
  return ({
    open: 'info',
    won: 'success',
    lost: 'error',
    abandoned: 'neutral',
  } as const)[status] ?? 'neutral'
}

/** Badge color per priority. */
export function dealPriorityColor(priority: DealPriority) {
  return ({
    low: 'neutral',
    medium: 'warning',
    high: 'error',
  } as const)[priority] ?? 'neutral'
}

/**
 * Format a decimal money string for display.
 *
 * The amount stays a string end-to-end (backend Numeric -> JSON string); it is
 * only converted to a number here, at the very edge, purely to render it. Any
 * value too large or malformed to represent exactly falls back to the raw
 * string rather than showing a silently rounded figure.
 */
export function formatMoney(value: string | null | undefined, currency = 'IDR', locale = 'id-ID'): string {
  if (value === null || value === undefined || value === '') return '-'
  const n = Number(value)
  if (!Number.isFinite(n) || !Number.isSafeInteger(Math.trunc(n))) return `${currency} ${value}`
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(n)
  }
  catch {
    // Unknown/invalid ISO code — Intl throws rather than degrading.
    return `${currency} ${value}`
  }
}

/**
 * Sum a list of decimal money strings, returned as a string.
 *
 * Works in integer "cents" so adding a column of 2dp values can't accumulate
 * binary floating-point drift (0.1 + 0.2 style) across a pipeline column.
 */
export function sumMoney(values: (string | null | undefined)[]): string {
  let cents = 0
  for (const v of values) {
    if (v === null || v === undefined || v === '') continue
    const n = Number(v)
    if (!Number.isFinite(n)) continue
    cents += Math.round(n * 100)
  }
  return (cents / 100).toFixed(2)
}

/**
 * Client-side preview of the server's weighted_value (value * probability/100).
 *
 * Display only — the stored figure always comes from the backend; this just
 * avoids a round-trip to show the user what they are about to save.
 */
export function computeWeightedValue(value: string, probability: number): string {
  const n = Number(value)
  if (!Number.isFinite(n) || !Number.isFinite(probability)) return '0.00'
  return ((n * probability) / 100).toFixed(2)
}

/** True when the deal is closed (won/lost) or abandoned — i.e. not in play. */
export function isDealClosed(status: DealStatus): boolean {
  return status !== 'open'
}

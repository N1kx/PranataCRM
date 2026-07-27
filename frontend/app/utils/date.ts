/**
 * Date formatting helpers.
 *
 * The API returns two different kinds of temporal value, and they must be
 * rendered differently:
 *
 *  - **Calendar date** (`Date` column, serialized as `"2026-09-01"`) — a date
 *    on a calendar, with no time and no timezone: an expected close date, a
 *    next-step date. "1 September" means the same day to everyone, so it must
 *    render identically no matter where the viewer is.
 *
 *  - **Instant** (`DateTime(timezone=True)` column, serialized as
 *    `"2026-07-27T02:41:47+00:00"`) — an actual point in time: when a stage
 *    changed, when a row was created. Converting it into the viewer's local
 *    timezone is exactly right.
 *
 * Mixing them up is a real bug, not a nitpick: `new Date("2026-09-01")` parses
 * as UTC midnight, so a viewer in a negative-offset zone (New York, Los
 * Angeles) sees the *previous day*.
 */

/**
 * Format a calendar date string (`yyyy-mm-dd`) for display.
 *
 * The parts are pulled out of the string and fed to the local-time `Date`
 * constructor, so the value can never be shifted by the viewer's timezone.
 * Anything that isn't a plain calendar date is returned unchanged rather than
 * guessed at.
 */
export function formatCalendarDate(
  value: string | null | undefined,
  locale = 'id-ID',
  fallback = '-',
): string {
  if (!value) return fallback
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  if (!match) return value
  const [, year, month, day] = match
  // Local-time constructor (not Date.parse) — no UTC round-trip, no shift.
  const date = new Date(Number(year), Number(month) - 1, Number(day))
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString(locale)
}

/**
 * Format an instant (ISO 8601 with offset) in the viewer's local timezone.
 *
 * This one *should* convert: the underlying value is a moment in time, so a
 * stage change at 09:00 Jakarta is correctly shown as 22:00 the previous day
 * in New York — same moment, different wall clock.
 */
export function formatInstant(
  value: string | null | undefined,
  locale = 'id-ID',
  fallback = '-',
): string {
  if (!value) return fallback
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString(locale)
}

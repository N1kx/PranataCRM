/**
 * Shared acquisition-channel picklist for company.source / contact.lead_source
 * (issue #40). Deliberately NOT a DB enum/CHECK constraint — channels are
 * tenant-specific and change often — this is a frontend-only bounded set so
 * reporting can group cleanly. 'other' pairs with a free-text companion field
 * (source_other / lead_source_other) so detail isn't lost to a catch-all.
 */
export const SOURCE_VALUES = [
  'web',
  'referral',
  'event',
  'cold_call',
  'ad',
  'social',
  'partner',
  'other',
] as const

export type SourceValue = typeof SOURCE_VALUES[number]

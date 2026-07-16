export type ContactStatus = 'lead' | 'qualified' | 'customer' | 'churned'

export type LifecycleStage =
  | 'subscriber'
  | 'lead'
  | 'mql'
  | 'sql'
  | 'opportunity'
  | 'customer'
  | 'evangelist'

export type PreferredContactMethod = 'email' | 'phone' | 'sms' | 'whatsapp'

export interface Contact {
  id: string
  owner_id?: string | null
  first_name: string
  last_name?: string | null
  email?: string | null
  phone?: string | null
  mobile_phone?: string | null
  job_title?: string | null
  department?: string | null
  status: ContactStatus
  lifecycle_stage?: LifecycleStage | null
  lead_source?: string | null
  /** geo_cities.id (issue #26) — resolve the display name via useGeo(), not stored as text. */
  city?: string | null
  /** geo_states.id (issue #26) — resolve the display name via useGeo(), not stored as text. */
  state?: string | null
  /** ISO 3166-1 alpha-2 code, e.g. "ID" (issue #26) — not a free-text country name. */
  country?: string | null
  description?: string | null
  created_at: string
}

export interface ContactCreatePayload {
  owner_id?: string | null
  first_name: string
  last_name?: string
  email?: string
  phone?: string
  mobile_phone?: string
  job_title?: string
  department?: string
  status?: ContactStatus
  lifecycle_stage?: LifecycleStage
  lead_source?: string
  // Nullable (not just optional): AppLocationSelect's cascade reset needs to
  // explicitly clear a previously-set state/city when the parent changes —
  // see ContactsForm.vue's buildPayload.
  city?: string | null
  state?: string | null
  country?: string | null
  description?: string
}

export type ContactUpdatePayload = Partial<ContactCreatePayload>

export interface ContactListResponse {
  items: Contact[]
  total: number
  page: number
  page_size: number
}

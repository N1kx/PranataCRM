import type { SourceValue } from '~/types/source'

export type CompanyType = 'prospect' | 'customer' | 'partner' | 'vendor' | 'competitor' | 'other'
export type CompanySize = '1-10' | '11-50' | '51-200' | '201-500' | '500+'
export type CompanyStatus = 'active' | 'inactive'

export interface Company {
  id: string
  owner_id?: string | null
  name: string
  legal_name?: string | null
  domain?: string | null
  website?: string | null
  email?: string | null
  phone?: string | null
  industry?: string | null
  size?: CompanySize | null
  employee_count?: number | null
  company_type: CompanyType
  status: CompanyStatus
  source?: SourceValue | null
  /** Free-text detail, only meaningful when source === 'other' (issue #40). */
  source_other?: string | null
  /** geo_cities.id (issue #26) — resolve the display name via useGeo(), not stored as text. */
  city?: string | null
  /** geo_states.id (issue #26) — resolve the display name via useGeo(), not stored as text. */
  state?: string | null
  /** ISO 3166-1 alpha-2 code, e.g. "ID" (issue #26) — not a free-text country name. */
  country?: string | null
  linkedin_url?: string | null
  description?: string | null
  created_at: string
  updated_at: string
}

export interface CompanyCreatePayload {
  owner_id?: string | null
  name: string
  legal_name?: string
  domain?: string
  website?: string
  email?: string
  phone: string
  industry?: string
  size?: CompanySize
  employee_count?: number
  company_type?: CompanyType
  status?: CompanyStatus
  source?: SourceValue
  source_other?: string
  // Nullable (not just optional): AppLocationSelect's cascade reset needs to
  // explicitly clear a previously-set state/city when the parent changes —
  // see CompaniesForm.vue's buildPayload (mirrors ContactsForm.vue).
  city?: string | null
  state?: string | null
  country: string
  linkedin_url?: string
  description?: string
}

export type CompanyUpdatePayload = Partial<CompanyCreatePayload>

export interface CompanyListResponse {
  items: Company[]
  total: number
  page: number
  page_size: number
}

/** Lightweight shape returned by /companies/search + /companies/lookup. */
export interface CompanySummary {
  id: string
  name: string
  domain?: string | null
}

export interface CompanyListQuery {
  page?: number
  pageSize?: number
  status?: CompanyStatus
  companyType?: CompanyType
  size?: CompanySize
  industry?: string
  ownerId?: string
  q?: string
  sort?: 'created_at' | 'name' | 'company_type' | 'status' | 'employee_count'
  order?: 'asc' | 'desc'
}

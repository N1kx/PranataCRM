export type DealStage = 'lead' | 'qualified' | 'proposal' | 'won' | 'lost'
export type DealStatus = 'open' | 'won' | 'lost' | 'abandoned'
export type DealType = 'new_business' | 'renewal' | 'upsell' | 'expansion' | 'cross_sell'
export type DealPriority = 'low' | 'medium' | 'high'

/** Pipeline column order for the kanban board. */
export const DEAL_STAGES: DealStage[] = ['lead', 'qualified', 'proposal', 'won', 'lost']
export const DEAL_TYPES: DealType[] = [
  'new_business',
  'renewal',
  'upsell',
  'expansion',
  'cross_sell',
]
export const DEAL_PRIORITIES: DealPriority[] = ['low', 'medium', 'high']
export const DEAL_STATUSES: DealStatus[] = ['open', 'won', 'lost', 'abandoned']

export interface Deal {
  id: string
  title: string
  description?: string | null
  contact_id?: string | null
  company_id?: string | null
  owner_id?: string | null
  stage: DealStage
  status: DealStatus
  deal_type?: DealType | null
  /** Decimal serialized as a string — never round-trip money through a JS number. */
  value: string
  /** ISO 4217, defaults to IDR. */
  currency: string
  probability: number
  /** Server-computed (value * probability / 100) — read-only, never sent. */
  weighted_value?: string | null
  expected_close_date: string
  actual_close_date?: string | null
  priority?: DealPriority | null
  source?: string | null
  next_step?: string | null
  next_step_date?: string | null
  competitor?: string | null
  close_reason?: string | null
  lost_reason?: string | null
  created_at: string
  updated_at: string
}

/**
 * Create payload. Deliberately carries no `stage`, `status`, `weighted_value`
 * or `ai_*`: stage moves only through PATCH /deals/{id}/stage, status only
 * through the abandon/reopen action, and the rest are server-managed.
 */
export interface DealCreatePayload {
  title: string
  expected_close_date: string
  description?: string | null
  contact_id?: string | null
  company_id?: string | null
  owner_id?: string | null
  deal_type?: DealType | null
  value?: string
  currency?: string
  probability?: number
  priority?: DealPriority | null
  source?: string | null
  next_step?: string | null
  next_step_date?: string | null
  competitor?: string | null
}

export type DealUpdatePayload = Partial<DealCreatePayload>

/**
 * The one status transition the generic PATCH accepts (open <-> abandoned).
 * Kept separate from DealUpdatePayload so `status` can never leak into a
 * normal form submit — the backend 422s on anything else.
 */
export interface DealStatusPayload {
  status: Extract<DealStatus, 'open' | 'abandoned'>
}

export interface DealListResponse {
  items: Deal[]
  total: number
  page: number
  page_size: number
}

export type DealSortField =
  | 'created_at'
  | 'title'
  | 'value'
  | 'expected_close_date'
  | 'probability'
  | 'stage'
  | 'status'

export interface DealListQuery {
  page?: number
  pageSize?: number
  stage?: DealStage
  status?: DealStatus
  dealType?: DealType
  priority?: DealPriority
  ownerId?: string
  contactId?: string
  companyId?: string
  q?: string
  sort?: DealSortField
  order?: 'asc' | 'desc'
}

/** Body for PATCH /deals/{id}/stage — `lost_reason` is required when stage is 'lost'. */
export interface StageChangePayload {
  stage: DealStage
  close_reason?: string
  lost_reason?: string
}

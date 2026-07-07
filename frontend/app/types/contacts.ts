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
  city?: string | null
  country?: string | null
  description?: string | null
  created_at: string
}

export interface ContactCreatePayload {
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
  city?: string
  country?: string
  description?: string
}

export type ContactUpdatePayload = Partial<ContactCreatePayload>

export interface ContactListResponse {
  items: Contact[]
  total: number
  page: number
  page_size: number
}

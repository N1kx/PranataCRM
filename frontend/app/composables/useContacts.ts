import type {
  Contact,
  ContactCreatePayload,
  ContactListParams,
  ContactListResponse,
  ContactSummary,
  ContactUpdatePayload,
} from '~/types/contacts'

export function useContacts() {
  const api = useApiClient()

  function list(params: ContactListParams = {}) {
    const query = new URLSearchParams()
    query.set('page', String(params.page ?? 1))
    query.set('page_size', String(params.pageSize ?? 20))
    if (params.status) query.set('status', params.status)
    if (params.lifecycleStage) query.set('lifecycle_stage', params.lifecycleStage)
    if (params.ownerId) query.set('owner_id', params.ownerId)
    if (params.companyId) query.set('company_id', params.companyId)
    if (params.q) query.set('q', params.q)
    if (params.sort) query.set('sort', params.sort)
    if (params.order) query.set('order', params.order)
    return api.get<ContactListResponse>(`/contacts?${query.toString()}`)
  }

  const get = (id: string) => api.get<Contact>(`/contacts/${id}`)

  const create = (payload: ContactCreatePayload) =>
    api.post<Contact>('/contacts', payload)

  const update = (id: string, payload: ContactUpdatePayload) =>
    api.patch<Contact>(`/contacts/${id}`, payload)

  const remove = (id: string) => api.del<void>(`/contacts/${id}`)

  /** Autocomplete source for AppContactSelect; optionally scoped to a company. */
  function search(q: string, limit = 20, companyId?: string | null) {
    const params = new URLSearchParams({ q, limit: String(limit) })
    if (companyId) params.set('company_id', companyId)
    return api.get<ContactSummary[]>(`/contacts/search?${params.toString()}`)
  }

  /** Batched id -> label resolution, so lists never fetch one contact per row. */
  function lookup(ids: string[]) {
    if (!ids.length) return Promise.resolve([] as ContactSummary[])
    return api.get<ContactSummary[]>(`/contacts/lookup?ids=${ids.map(encodeURIComponent).join(',')}`)
  }

  return { list, get, create, update, remove, search, lookup }
}

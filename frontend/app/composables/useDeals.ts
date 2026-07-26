import type {
  Deal,
  DealCreatePayload,
  DealListQuery,
  DealListResponse,
  DealStatusPayload,
  DealUpdatePayload,
  StageChangePayload,
} from '~/types/deals'

export function useDeals() {
  const api = useApiClient()

  function list(query: DealListQuery = {}) {
    const params = new URLSearchParams()
    params.set('page', String(query.page ?? 1))
    params.set('page_size', String(query.pageSize ?? 20))
    if (query.stage) params.set('stage', query.stage)
    if (query.status) params.set('status', query.status)
    if (query.dealType) params.set('deal_type', query.dealType)
    if (query.priority) params.set('priority', query.priority)
    if (query.ownerId) params.set('owner_id', query.ownerId)
    if (query.contactId) params.set('contact_id', query.contactId)
    if (query.companyId) params.set('company_id', query.companyId)
    if (query.q) params.set('q', query.q)
    if (query.sort) params.set('sort', query.sort)
    if (query.order) params.set('order', query.order)
    return api.get<DealListResponse>(`/deals?${params.toString()}`)
  }

  const get = (id: string) => api.get<Deal>(`/deals/${id}`)

  const create = (payload: DealCreatePayload) => api.post<Deal>('/deals', payload)

  const update = (id: string, payload: DealUpdatePayload) =>
    api.patch<Deal>(`/deals/${id}`, payload)

  const remove = (id: string) => api.del<void>(`/deals/${id}`)

  /**
   * The ONLY way to change a deal's stage — the generic PATCH 422s on `stage`.
   * Applies the backend's side effects (status, actual_close_date, probability,
   * stage_changed_at) atomically and returns the updated deal.
   */
  const moveStage = (id: string, body: StageChangePayload) =>
    api.patch<Deal>(`/deals/${id}/stage`, body)

  /**
   * Abandon / reopen. Deliberately narrower than `update`: the backend only
   * accepts open <-> abandoned here, won/lost go through moveStage.
   */
  const setStatus = (id: string, body: DealStatusPayload) =>
    api.patch<Deal>(`/deals/${id}`, body)

  return { list, get, create, update, remove, moveStage, setStatus }
}

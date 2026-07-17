import type {
  Contact,
  ContactCreatePayload,
  ContactListParams,
  ContactListResponse,
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

  return { list, get, create, update, remove }
}

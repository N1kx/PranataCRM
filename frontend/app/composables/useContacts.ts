import type {
  Contact,
  ContactCreatePayload,
  ContactListResponse,
  ContactUpdatePayload,
} from '~/types/contacts'

export function useContacts() {
  const api = useApiClient()

  function list(page = 1, pageSize = 20) {
    return api.get<ContactListResponse>(
      `/contacts?page=${page}&page_size=${pageSize}`,
    )
  }

  const get = (id: string) => api.get<Contact>(`/contacts/${id}`)

  const create = (payload: ContactCreatePayload) =>
    api.post<Contact>('/contacts', payload)

  const update = (id: string, payload: ContactUpdatePayload) =>
    api.patch<Contact>(`/contacts/${id}`, payload)

  const remove = (id: string) => api.del<void>(`/contacts/${id}`)

  return { list, get, create, update, remove }
}

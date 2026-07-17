import type {
  Company,
  CompanyCreatePayload,
  CompanyListQuery,
  CompanyListResponse,
  CompanySummary,
  CompanyUpdatePayload,
} from '~/types/companies'

export function useCompanies() {
  const api = useApiClient()

  function list(query: CompanyListQuery = {}) {
    const params = new URLSearchParams()
    params.set('page', String(query.page ?? 1))
    params.set('page_size', String(query.pageSize ?? 20))
    if (query.status) params.set('status', query.status)
    if (query.companyType) params.set('company_type', query.companyType)
    if (query.size) params.set('size', query.size)
    if (query.industry) params.set('industry', query.industry)
    if (query.ownerId) params.set('owner_id', query.ownerId)
    if (query.q) params.set('q', query.q)
    if (query.sort) params.set('sort', query.sort)
    if (query.order) params.set('order', query.order)
    return api.get<CompanyListResponse>(`/companies?${params.toString()}`)
  }

  const get = (id: string) => api.get<Company>(`/companies/${id}`)

  const create = (payload: CompanyCreatePayload) =>
    api.post<Company>('/companies', payload)

  const update = (id: string, payload: CompanyUpdatePayload) =>
    api.patch<Company>(`/companies/${id}`, payload)

  const remove = (id: string) => api.del<void>(`/companies/${id}`)

  function search(q: string, limit = 20) {
    return api.get<CompanySummary[]>(`/companies/search?q=${encodeURIComponent(q)}&limit=${limit}`)
  }

  function lookup(ids: string[]) {
    if (!ids.length) return Promise.resolve([] as CompanySummary[])
    return api.get<CompanySummary[]>(`/companies/lookup?ids=${ids.map(encodeURIComponent).join(',')}`)
  }

  return { list, get, create, update, remove, search, lookup }
}

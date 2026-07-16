import type {
  GeoCity,
  GeoCityCreatePayload,
  GeoCityUpdatePayload,
  GeoCountry,
  GeoOption,
  GeoState,
  GeoStateCreatePayload,
  GeoStateUpdatePayload,
} from '~/types/geo'

/**
 * Geo reference data (issue #26): countries/states/cities. The backend
 * already serves each scope from a Redis per-parent cache (see
 * backend/app/modules/geo/cache.py), so the frontend fetches a scope's full
 * list ONCE per selection and lets USelectMenu's own client-side filtering
 * handle "search as you type" — no debounced backend search here, unlike
 * useUsers()/useCompanies() search endpoints.
 */
export function useGeo() {
  const api = useApiClient()
  const { locale } = useI18n()

  function countryLabel(c: GeoCountry): string {
    return locale.value === 'id' && c.name_id ? c.name_id : c.name_en
  }

  async function listCountries(): Promise<GeoOption[]> {
    const items = await api.get<GeoCountry[]>('/geo/countries')
    return items
      .map(c => ({ label: countryLabel(c), value: c.code }))
      .sort((a, b) => a.label.localeCompare(b.label))
  }

  async function listStates(countryCode: string): Promise<GeoOption[]> {
    const items = await api.get<GeoState[]>(
      `/geo/states?country=${encodeURIComponent(countryCode)}`,
    )
    return items.map(s => ({ label: s.name, value: s.id }))
  }

  async function listCities(stateId: string): Promise<GeoOption[]> {
    const items = await api.get<GeoCity[]>(`/geo/cities?state=${encodeURIComponent(stateId)}`)
    return items.map(c => ({ label: c.name, value: c.id }))
  }

  // ── admin (platform-admin only — backend enforces, this just calls it) ────

  const adminUpdateCountry = (code: string, payload: { name_en?: string, name_id?: string | null, is_active?: boolean }) =>
    api.patch<GeoCountry>(`/admin/geo/countries/${encodeURIComponent(code)}`, payload)

  const adminCreateState = (payload: GeoStateCreatePayload) =>
    api.post<GeoState>('/admin/geo/states', payload)

  const adminUpdateState = (id: string, payload: GeoStateUpdatePayload) =>
    api.patch<GeoState>(`/admin/geo/states/${id}`, payload)

  const adminDeleteState = (id: string) =>
    api.del<{ message: string }>(`/admin/geo/states/${id}`)

  const adminCreateCity = (payload: GeoCityCreatePayload) =>
    api.post<GeoCity>('/admin/geo/cities', payload)

  const adminUpdateCity = (id: string, payload: GeoCityUpdatePayload) =>
    api.patch<GeoCity>(`/admin/geo/cities/${id}`, payload)

  const adminDeleteCity = (id: string) =>
    api.del<{ message: string }>(`/admin/geo/cities/${id}`)

  return {
    listCountries,
    listStates,
    listCities,
    adminUpdateCountry,
    adminCreateState,
    adminUpdateState,
    adminDeleteState,
    adminCreateCity,
    adminUpdateCity,
    adminDeleteCity,
  }
}

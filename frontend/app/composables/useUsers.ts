import type { UserSummary } from '~/types/user'

export function useUsers() {
  const api = useApiClient()

  function search(q: string, limit = 20) {
    return api.get<UserSummary[]>(`/users/search?q=${encodeURIComponent(q)}&limit=${limit}`)
  }

  function lookup(ids: string[]) {
    if (!ids.length) return Promise.resolve([] as UserSummary[])
    return api.get<UserSummary[]>(`/users/lookup?ids=${ids.map(encodeURIComponent).join(',')}`)
  }

  return { search, lookup }
}

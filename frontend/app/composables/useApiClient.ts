import type { ApiError } from '~/types/auth'

type FetchOptions = Parameters<typeof $fetch>[1]
/** The body type ofetch/$fetch accepts, so wrappers stay in sync with it. */
type FetchBody = NonNullable<FetchOptions>['body']

export class ApiRequestError extends Error {
  constructor(
    public code: string,
    message: string,
    public statusCode: number,
  ) {
    super(message)
    this.name = 'ApiRequestError'
  }
}

export function useApiClient() {
  const config = useRuntimeConfig()
  const nuxtApp = useNuxtApp()

  function tenantSlug(): string | undefined {
    if (config.public.appEnv === 'development') {
      const authStore = useAuthStore()
      return authStore.tenantSlug || undefined
    }
    return undefined
  }

  async function request<T>(
    path: string,
    options: Parameters<typeof $fetch>[1] = {},
  ): Promise<T> {
    const slug = tenantSlug()
    const headers: Record<string, string> = {
      'Accept-Language': nuxtApp.$i18n.locale.value,
      ...(slug ? { 'X-Tenant-Slug': slug } : {}),
      ...(options.headers as Record<string, string> || {}),
    }

    try {
      return await $fetch<T>(`${config.public.apiBase}${path}`, {
        ...options,
        credentials: 'include',
        headers,
      })
    }
    catch (err: unknown) {
      const fetchError = err as { data?: ApiError; status?: number }
      const errData = fetchError?.data?.error
      throw new ApiRequestError(
        errData?.code ?? 'INTERNAL_ERROR',
        errData?.message ?? 'Terjadi kesalahan.',
        fetchError?.status ?? 500,
      )
    }
  }

  return {
    get: <T>(path: string, opts?: FetchOptions) =>
      request<T>(path, { method: 'GET', ...opts }),
    post: <T>(path: string, body?: FetchBody, opts?: FetchOptions) =>
      request<T>(path, { method: 'POST', body, ...opts }),
    patch: <T>(path: string, body?: FetchBody, opts?: FetchOptions) =>
      request<T>(path, { method: 'PATCH', body, ...opts }),
    del: <T>(path: string, opts?: FetchOptions) =>
      request<T>(path, { method: 'DELETE', ...opts }),
  }
}

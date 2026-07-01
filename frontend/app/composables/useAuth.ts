import type {
  AcceptInvitePayload,
  AuthUser,
  CreateUserPayload,
  InviteUserPayload,
  LoginPayload,
  RegisterTenantPayload,
} from '~/types/auth'

export function useAuth() {
  const store = useAuthStore()
  const api = useApiClient()
  const router = useRouter()

  async function login(slug: string, payload: LoginPayload): Promise<void> {
    store.setTenantSlug(slug)
    const user = await api.post<AuthUser>('/auth/login', payload)
    store.setUser(user)
    await router.push('/app')
  }

  async function logout(): Promise<void> {
    // Clear local state immediately — don't block on network
    store.clear()
    await navigateTo('/login')
    try {
      await api.post('/auth/logout')
    }
    catch {
      // Idempotent — ignore error
    }
  }

  async function registerTenant(payload: RegisterTenantPayload): Promise<void> {
    await api.post('/auth/register-tenant', payload)
    // Server does not auto-login on register — redirect to login
    await router.push({ path: '/login', query: { slug: payload.slug, registered: '1' } })
  }

  async function acceptInvite(slug: string, payload: AcceptInvitePayload): Promise<AuthUser> {
    store.setTenantSlug(slug)
    const user = await api.post<AuthUser>('/auth/accept-invite', payload)
    store.setUser(user)
    return user
  }

  async function createUser(payload: CreateUserPayload): Promise<AuthUser> {
    return api.post<AuthUser>('/users', payload)
  }

  async function inviteUser(payload: InviteUserPayload): Promise<void> {
    await api.post('/users/invite', payload)
  }

  async function restoreSession(): Promise<boolean> {
    store.restoreSlug()
    try {
      const user = await api.get<AuthUser>('/auth/me')
      store.setUser(user)
      return true
    }
    catch {
      store.clear()
      return false
    }
  }

  return {
    user: computed(() => store.user),
    isAuthenticated: computed(() => store.isAuthenticated),
    isOwnerOrAdmin: computed(() => store.isOwnerOrAdmin),
    tenantSlug: computed(() => store.tenantSlug),
    login,
    logout,
    registerTenant,
    acceptInvite,
    createUser,
    inviteUser,
    restoreSession,
  }
}

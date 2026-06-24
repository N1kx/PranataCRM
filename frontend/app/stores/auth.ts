import { defineStore } from 'pinia'
import type { AuthUser } from '~/types/auth'

const SLUG_KEY = 'pranata_tenant_slug'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as AuthUser | null,
    tenantSlug: null as string | null,
  }),

  getters: {
    isAuthenticated: state => !!state.user,
    isOwnerOrAdmin: state =>
      state.user?.suite_role === 'tenant_owner' || state.user?.suite_role === 'tenant_admin',
  },

  actions: {
    setUser(user: AuthUser) {
      this.user = user
    },
    setTenantSlug(slug: string) {
      this.tenantSlug = slug
      if (import.meta.client) {
        localStorage.setItem(SLUG_KEY, slug)
      }
    },
    restoreSlug() {
      if (import.meta.client) {
        const stored = localStorage.getItem(SLUG_KEY)
        if (stored) this.tenantSlug = stored
      }
    },
    clear() {
      this.user = null
      this.tenantSlug = null
      if (import.meta.client) {
        localStorage.removeItem(SLUG_KEY)
      }
    },
  },
})

export default defineNuxtRouteMiddleware(async () => {
  const store = useAuthStore()
  store.restoreSlug()

  if (!store.isAuthenticated) {
    try {
      const { restoreSession } = useAuth()
      const restored = await restoreSession()
      if (!restored) {
        return navigateTo('/login')
      }
    }
    catch (err) {
      console.error('[auth middleware] restoreSession failed', err)
      return navigateTo('/login')
    }
  }
})

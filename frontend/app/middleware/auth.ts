export default defineNuxtRouteMiddleware(() => {
  const store = useAuthStore()
  store.restoreSlug()

  if (!store.isAuthenticated) {
    return navigateTo('/login')
  }
})

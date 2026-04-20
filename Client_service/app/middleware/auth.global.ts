import { APP_ROUTES } from '@/constants/navigation'
import { AUTH_REDIRECT_QUERY, getAuthRedirectTarget } from '@/utils/auth-redirect'

export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()
  const publicRoutes = [APP_ROUTES.home, APP_ROUTES.authLogin, APP_ROUTES.authRegister]
  const isOrganizationPublicRoute = /^\/org\/[^/]+\/public\/?$/.test(to.path)
  const isPublicRoute = publicRoutes.includes(to.path) || isOrganizationPublicRoute

  if (!auth.isReady) {
    await auth.hydrate()
  }

  if (!auth.isAuthenticated && !isPublicRoute) {
    return navigateTo({
      path: APP_ROUTES.authLogin,
      query: {
        [AUTH_REDIRECT_QUERY]: to.fullPath
      }
    })
  }

  if (auth.isAuthenticated && [APP_ROUTES.authLogin, APP_ROUTES.authRegister].includes(to.path)) {
    return navigateTo(getAuthRedirectTarget(to.query[AUTH_REDIRECT_QUERY]))
  }
})

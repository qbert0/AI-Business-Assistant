import { APP_ROUTES } from '@/constants/navigation'
import { useAuthStore } from '@/stores/auth/useAuthStore'
import { AUTH_REDIRECT_QUERY, getAuthRedirectTarget } from '@/utils/auth-redirect'
import { hasClientAuthToken } from '@/utils/auth-token'

export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()
  const publicRoutes = [APP_ROUTES.home, APP_ROUTES.authLogin, APP_ROUTES.authRegister, APP_ROUTES.authGoogleCallback] as string[]
  const isOrganizationPublicRoute = /^\/org\/[^/]+\/public\/?$/.test(to.path)
  const isOrganizationDashboardRoute = /^\/org\/[^/]+\/dashboard\/?$/.test(to.path)
  const isOrganizationGuestChatRoute = /^\/org\/[^/]+\/chat\/?$/.test(to.path)
  const isOrganizationDocumentsRoute = /^\/org\/[^/]+\/documents\/?$/.test(to.path)
  const isOrganizationSearchRoute = /^\/org\/search\/?$/.test(to.path)
  const isPublicRoute = publicRoutes.includes(to.path) || isOrganizationPublicRoute || isOrganizationDashboardRoute || isOrganizationGuestChatRoute || isOrganizationDocumentsRoute || isOrganizationSearchRoute

  if (!auth.isReady && (!isPublicRoute || hasClientAuthToken())) {
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

  if (auth.isAuthenticated && ([APP_ROUTES.authLogin, APP_ROUTES.authRegister] as string[]).includes(to.path)) {
    return navigateTo(getAuthRedirectTarget(to.query[AUTH_REDIRECT_QUERY]))
  }
})

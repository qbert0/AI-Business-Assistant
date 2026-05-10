import type { LoginInput, RegisterInput } from '@/schemas/auth'
import { APP_ROUTES } from '@/constants/navigation'
import { useAuthStore } from '@/stores/auth/useAuthStore'
import { AUTH_REDIRECT_QUERY, getAuthRedirectTarget } from '@/utils/auth-redirect'

export const useAuth = () => {
  const auth = useAuthStore()
  const route = useRoute()

  const login = async (payload: LoginInput = { email: 'chau@example.com', password: 'demo123456' }) => {
    const ok = await auth.login(payload)
    if (ok) {
      return navigateTo(getAuthRedirectTarget(route.query[AUTH_REDIRECT_QUERY]))
    }
    return false
  }

  const register = async (payload: RegisterInput) => {
    const ok = await auth.register(payload)
    if (ok) {
      return navigateTo(getAuthRedirectTarget(route.query[AUTH_REDIRECT_QUERY]))
    }
    return false
  }

  const logout = async () => {
    await auth.logout()
    return navigateTo(APP_ROUTES.authLogin)
  }

  return {
    user: computed(() => auth.user ?? {
      id: '',
      name: '',
      email: '',
      title: '',
      role: 'user' as const
    }),
    isAuthenticated: computed(() => auth.isAuthenticated),
    isReady: computed(() => auth.isReady),
    isLoading: computed(() => auth.isLoading),
    error: computed(() => auth.error),
    hydrate: auth.hydrate,
    login,
    register,
    logout
  }
}

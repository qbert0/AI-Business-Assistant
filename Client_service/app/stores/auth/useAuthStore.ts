import type { AuthUser } from '@/types/auth'
import { loginSchema, registerSchema, type LoginInput, type RegisterInput } from '@/schemas/auth'
import { hasClientAuthToken } from '@/utils/auth-token'

import { useApiAuth } from '@/composables/api/auth/useApiAuth'

export const useAuthStore = defineStore('auth', () => {
  const api = useApiAuth()
  const user = ref<AuthUser | null>(null)
  const isReady = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => Boolean(user.value))

  const hydrate = async () => {
    if (isReady.value) {
      return
    }

    if (!hasClientAuthToken()) {
      user.value = null
      error.value = null
      isReady.value = true
      isLoading.value = false
      return
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await api.me()
      user.value = response.user
    } catch {
      user.value = null
    } finally {
      isReady.value = true
      isLoading.value = false
    }
  }

  const login = async (payload: LoginInput) => {
    const parsed = loginSchema.safeParse(payload)
    if (!parsed.success) {
      error.value = parsed.error.issues[0]?.message ?? 'Invalid login input'
      return false
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await api.login(parsed.data)
      persistClientAuthToken(response.token)
      user.value = response.user
      isReady.value = true
      return true
    } catch (err) {
      error.value = getAuthErrorMessage(err, 'Email hoặc mật khẩu không đúng.')
      user.value = null
      return false
    } finally {
      isLoading.value = false
    }
  }

  const register = async (payload: RegisterInput) => {
    const parsed = registerSchema.safeParse(payload)
    if (!parsed.success) {
      error.value = parsed.error.issues[0]?.message ?? 'Invalid register input'
      return false
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await api.register(parsed.data)
      persistClientAuthToken(response.token)
      user.value = response.user
      isReady.value = true
      return true
    } catch (err) {
      error.value = getAuthErrorMessage(err, 'Register failed')
      user.value = null
      return false
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    await api.logout()
    clearClientAuthToken()
    user.value = null
    isReady.value = true
  }

  return {
    user,
    isReady,
    isLoading,
    error,
    isAuthenticated,
    hydrate,
    login,
    register,
    logout
  }
})

const getAuthErrorMessage = (err: unknown, fallback: string) => {
  if (err && typeof err === 'object' && 'data' in err) {
    const data = (err as { data?: { detail?: string, message?: string, statusMessage?: string } }).data
    return data?.detail || data?.message || data?.statusMessage || fallback
  }

  if (err && typeof err === 'object' && 'statusMessage' in err) {
    return String((err as { statusMessage?: string }).statusMessage || fallback)
  }

  return fallback
}

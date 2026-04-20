import type { AuthUser } from '@/types/auth'
import type { LoginInput } from '@/schemas/auth'

export const useApiAuth = () => {
  const apiFetch = useApiFetch()

  const login = (payload: LoginInput) =>
    apiFetch<{ token: string, user: AuthUser }>('/api/auth/login', {
      method: 'POST',
      body: payload
    })

  const me = () => apiFetch<{ user: AuthUser }>('/api/auth/me')

  const logout = () =>
    apiFetch<{ ok: boolean }>('/api/auth/logout', {
      method: 'POST'
    })

  return {
    login,
    me,
    logout
  }
}

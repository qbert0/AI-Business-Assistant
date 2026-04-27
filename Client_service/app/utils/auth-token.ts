import { AUTH_CLIENT_TOKEN_COOKIE, AUTH_STORAGE_KEY, AUTH_TOKEN_MAX_AGE } from '@/constants/auth'

export const persistClientAuthToken = (token: string) => {
  const authCookie = useCookie(AUTH_CLIENT_TOKEN_COOKIE, {
    maxAge: AUTH_TOKEN_MAX_AGE,
    sameSite: 'lax',
    path: '/'
  })

  authCookie.value = token

  if (import.meta.client) {
    localStorage.setItem(AUTH_STORAGE_KEY, token)
  }
}

export const clearClientAuthToken = () => {
  const authCookie = useCookie(AUTH_CLIENT_TOKEN_COOKIE, {
    maxAge: AUTH_TOKEN_MAX_AGE,
    sameSite: 'lax',
    path: '/'
  })

  authCookie.value = null

  if (import.meta.client) {
    localStorage.removeItem(AUTH_STORAGE_KEY)
  }
}

export const getClientAuthToken = () => {
  const authCookie = useCookie<string | null>(AUTH_CLIENT_TOKEN_COOKIE)

  if (authCookie.value) {
    return authCookie.value
  }

  if (import.meta.client) {
    return localStorage.getItem(AUTH_STORAGE_KEY)
  }

  return null
}

export const hasClientAuthToken = () => Boolean(getClientAuthToken())

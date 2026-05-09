import { APP_ROUTES } from '@/constants/navigation'

export const AUTH_REDIRECT_QUERY = 'redirect'

const isSafeInternalPath = (value: string) =>
  value.startsWith('/') && !value.startsWith('//') && !value.startsWith('/\\')

export const getAuthRedirectTarget = (redirect?: unknown, fallback = APP_ROUTES.dashboard) => {
  const target = Array.isArray(redirect) ? redirect[0] : redirect

  if (typeof target !== 'string' || !isSafeInternalPath(target)) {
    return fallback
  }

  if ([APP_ROUTES.authLogin, APP_ROUTES.authRegister].includes(target)) {
    return fallback
  }

  return target
}


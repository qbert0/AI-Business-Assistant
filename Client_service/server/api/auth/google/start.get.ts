import { randomUUID } from 'node:crypto'
import { AUTH_GOOGLE_STATE_COOKIE } from '../../../../app/constants/auth'
import { APP_ROUTES } from '../../../../app/constants/navigation'
import { AUTH_REDIRECT_QUERY, getAuthRedirectTarget } from '../../../../app/utils/auth-redirect'

export default defineEventHandler((event) => {
  const config = useRuntimeConfig()
  const clientId = String(config.public.googleClientId || '').trim()

  if (!clientId) {
    throw createError({
      statusCode: 503,
      statusMessage: 'Google OAuth client ID is not configured'
    })
  }

  const state = randomUUID()
  const redirectTo = getAuthRedirectTarget(getQuery(event)[AUTH_REDIRECT_QUERY])
  const requestUrl = getRequestURL(event)
  const redirectUri = `${requestUrl.origin}${APP_ROUTES.authGoogleCallback}`

  setCookie(event, AUTH_GOOGLE_STATE_COOKIE, JSON.stringify({ state, redirectTo }), {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 60 * 10
  })

  const googleUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth')
  googleUrl.searchParams.set('client_id', clientId)
  googleUrl.searchParams.set('redirect_uri', redirectUri)
  googleUrl.searchParams.set('response_type', 'code')
  googleUrl.searchParams.set('scope', 'openid email profile')
  googleUrl.searchParams.set('state', state)
  googleUrl.searchParams.set('prompt', 'select_account')

  return sendRedirect(event, googleUrl.toString())
})

import { z } from 'zod'
import { AUTH_GOOGLE_STATE_COOKIE } from '../../../../app/constants/auth'
import { APP_ROUTES } from '../../../../app/constants/navigation'
import { backendFetch, mapUser } from '../../../utils/backend'
import { setAuthCookies } from '../../../utils/auth-session'

const querySchema = z.object({
  code: z.string().min(1),
  state: z.string().min(1)
})

interface BackendGoogleExchangeResponse {
  access_token: string
  token_type: string
  user: {
    id: string
    email: string
    full_name: string
    public_profile?: string | null
  }
}

export default defineEventHandler(async (event) => {
  const parsed = querySchema.safeParse(getQuery(event))
  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Missing Google OAuth callback parameters'
    })
  }

  const stateCookie = getCookie(event, AUTH_GOOGLE_STATE_COOKIE)
  if (!stateCookie) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Google OAuth state is missing or expired'
    })
  }

  let statePayload: { state: string, redirectTo?: string }
  try {
    statePayload = JSON.parse(stateCookie)
  } catch {
    throw createError({
      statusCode: 400,
      statusMessage: 'Google OAuth state is invalid'
    })
  }

  if (statePayload.state !== parsed.data.state) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Google OAuth state does not match'
    })
  }

  const requestUrl = getRequestURL(event)
  const redirectUri = `${requestUrl.origin}${APP_ROUTES.authGoogleCallback}`
  const response = await backendFetch<BackendGoogleExchangeResponse>(event, '/auth/google/exchange', {
    method: 'POST',
    body: {
      code: parsed.data.code,
      redirect_uri: redirectUri
    }
  })

  deleteCookie(event, AUTH_GOOGLE_STATE_COOKIE, { path: '/' })

  const token = response.access_token
  setAuthCookies(event, token)

  return {
    token,
    tokenType: response.token_type || 'Bearer',
    user: mapUser(response.user),
    redirectTo: statePayload.redirectTo || APP_ROUTES.dashboard
  }
})

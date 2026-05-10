import { z } from 'zod'
import { backendFetch, mapUser } from '../../utils/backend'
import { setAuthCookies } from '../../utils/auth-session'

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
})

interface BackendLoginResponse {
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
  const body = loginSchema.parse(await readBody(event))
  const response = await backendFetch<BackendLoginResponse>(event, '/auth/login', {
    method: 'POST',
    body
  }).catch((err: unknown) => {
    throw createError({
      statusCode: getFetchStatusCode(err, 401),
      statusMessage: getFetchErrorMessage(err, 'Email hoặc mật khẩu không đúng.')
    })
  })
  const token = response.access_token
  setAuthCookies(event, token)

  return {
    token,
    tokenType: response.token_type || 'Bearer',
    user: mapUser(response.user)
  }
})

const getFetchStatusCode = (err: unknown, fallback: number) => {
  if (err && typeof err === 'object' && 'statusCode' in err) {
    return Number((err as { statusCode?: number }).statusCode || fallback)
  }
  if (err && typeof err === 'object' && 'status' in err) {
    return Number((err as { status?: number }).status || fallback)
  }
  return fallback
}

const getFetchErrorMessage = (err: unknown, fallback: string) => {
  if (err && typeof err === 'object' && 'data' in err) {
    const data = (err as { data?: { detail?: string, message?: string, statusMessage?: string } }).data
    return data?.detail || data?.message || data?.statusMessage || fallback
  }
  return fallback
}

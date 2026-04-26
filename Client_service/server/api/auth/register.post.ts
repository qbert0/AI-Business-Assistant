import { z } from 'zod'
import { AUTH_CLIENT_TOKEN_COOKIE, AUTH_TOKEN_COOKIE, AUTH_TOKEN_MAX_AGE } from '../../../app/constants/auth'
import { backendFetch, mapUser } from '../../utils/backend'

const registerSchema = z.object({
  full_name: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(8)
})

interface BackendRegisterResponse {
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
  const body = registerSchema.parse(await readBody(event))
  const response = await backendFetch<BackendRegisterResponse>(event, '/auth/register', {
    method: 'POST',
    body
  })
  const token = response.access_token

  setCookie(event, AUTH_TOKEN_COOKIE, token, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: AUTH_TOKEN_MAX_AGE
  })

  setCookie(event, AUTH_CLIENT_TOKEN_COOKIE, token, {
    httpOnly: false,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: AUTH_TOKEN_MAX_AGE
  })

  return {
    token,
    tokenType: response.token_type || 'Bearer',
    user: mapUser(response.user)
  }
})

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
  })
  const token = response.access_token
  setAuthCookies(event, token)

  return {
    token,
    tokenType: response.token_type || 'Bearer',
    user: mapUser(response.user)
  }
})

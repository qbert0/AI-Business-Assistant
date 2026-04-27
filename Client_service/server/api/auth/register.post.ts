import { z } from 'zod'
import { backendFetch, mapUser } from '../../utils/backend'
import { setAuthCookies } from '../../utils/auth-session'

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
  setAuthCookies(event, token)

  return {
    token,
    tokenType: response.token_type || 'Bearer',
    user: mapUser(response.user)
  }
})

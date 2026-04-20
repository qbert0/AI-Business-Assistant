import { z } from 'zod'
import { backendFetch, getBackendUser, mapMember } from '../../../utils/backend'

const memberSchema = z.object({
  email: z.string().email(),
  role: z.enum(['admin', 'user']).default('user'),
  permissions: z.array(z.string()).default([])
})

interface BackendUser {
  id: string
}

interface BackendMember {
  id: string
  user_id: string
  organization_id: string
  role: 'admin' | 'user'
  permissions: any[]
  status: 'active' | 'invited' | 'disabled'
  user: {
    id: string
    email: string
    full_name: string
    public_profile?: string | null
  }
}

export default defineEventHandler(async (event) => {
  const actingUser = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const body = memberSchema.parse(await readBody(event))
  const users = await backendFetch<BackendUser[]>(event, `/users?search=${encodeURIComponent(body.email)}&limit=10`)
  const targetUser = users.find((user: any) => user.email === body.email)

  if (!targetUser) {
    throw createError({ statusCode: 404, statusMessage: 'Registered user not found' })
  }

  const member = await backendFetch<BackendMember>(
    event,
    `/organizations/${orgId}/members?acting_user_id=${encodeURIComponent(actingUser.id)}`,
    {
      method: 'POST',
      body: {
        user_id: targetUser.id,
        role: body.role,
        permissions: body.permissions,
        status: 'active'
      }
    }
  )

  return { member: mapMember(member) }
})

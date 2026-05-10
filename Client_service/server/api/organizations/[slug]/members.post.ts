import { z } from 'zod'
import { backendFetch, getBackendUser, mapMember } from '../../../utils/backend'

const memberSchema = z.object({
  emails: z.array(z.string().email()).min(1),
  role: z.string().trim().min(1).default('user'),
  permissions: z.array(z.string()).default([])
})

interface BackendUser {
  id: string
  email: string
  full_name: string
}

interface BackendMember {
  id: string
  user_id: string
  organization_id: string
  role: string
  permissions: any[]
  status: 'active' | 'pending_response' | 'invited' | 'disabled'
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
  const uniqueEmails = [...new Set(body.emails.map((email) => email.trim().toLowerCase()).filter(Boolean))]
  const members: BackendMember[] = []

  for (const email of uniqueEmails) {
    const users = await backendFetch<BackendUser[]>(event, `/users?search=${encodeURIComponent(email)}&limit=20`)
    const targetUser = users.find((user: any) => String(user.email).toLowerCase() === email)

    if (!targetUser) {
      throw createError({ statusCode: 404, statusMessage: `Registered user not found: ${email}` })
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
          status: 'pending_response'
        }
      }
    )

    members.push(member)
  }

  return { members: members.map(mapMember) }
})

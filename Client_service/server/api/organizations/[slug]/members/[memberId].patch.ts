import { z } from 'zod'
import { backendFetch, getBackendUser, mapMember } from '../../../../utils/backend'

const patchMemberSchema = z.object({
  role: z.enum(['admin', 'user']).optional(),
  permissions: z.array(z.string()).optional()
})

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const memberId = getRouterParam(event, 'memberId') || ''
  const body = patchMemberSchema.parse(await readBody(event))
  const member = await backendFetch<any>(
    event,
    `/organizations/${orgId}/members/${memberId}?acting_user_id=${encodeURIComponent(user.id)}`,
    {
      method: 'PATCH',
      body
    }
  )

  return { member: mapMember(member) }
})

import { z } from 'zod'
import { requireAuthPayload } from '../../../../utils/jwt'
import { mockMembersByOrg } from '../../../../utils/mockData'

const patchMemberSchema = z.object({
  department: z.string().min(2).optional(),
  title: z.string().min(2).optional(),
  role: z.string().min(2).optional(),
  permissions: z.array(z.string()).optional()
})

export default defineEventHandler(async (event) => {
  requireAuthPayload(event)
  const slug = getRouterParam(event, 'slug') || ''
  const memberId = getRouterParam(event, 'memberId')
  const body = patchMemberSchema.parse(await readBody(event))

  mockMembersByOrg[slug] = (mockMembersByOrg[slug] ?? []).map((member) =>
    member.id === memberId ? { ...member, ...body } : member
  )

  return {
    member: mockMembersByOrg[slug].find((member) => member.id === memberId)
  }
})

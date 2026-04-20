import { z } from 'zod'
import { requireAuthPayload } from '../../../utils/jwt'
import { mockMembersByOrg } from '../../../utils/mockData'

const memberSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  department: z.string().min(2),
  title: z.string().min(2),
  role: z.string().min(2),
  permissions: z.array(z.string()).default([])
})

export default defineEventHandler(async (event) => {
  requireAuthPayload(event)
  const slug = getRouterParam(event, 'slug') || ''
  const body = memberSchema.parse(await readBody(event))
  const member = {
    ...body,
    id: `m-${Date.now()}`,
    status: 'invited' as const
  }

  mockMembersByOrg[slug] = [member, ...(mockMembersByOrg[slug] ?? [])]

  return { member }
})

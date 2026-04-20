import { requireAuthPayload } from '../../../../utils/jwt'
import { mockMembersByOrg } from '../../../../utils/mockData'

export default defineEventHandler((event) => {
  requireAuthPayload(event)
  const slug = getRouterParam(event, 'slug') || ''
  const memberId = getRouterParam(event, 'memberId')

  mockMembersByOrg[slug] = (mockMembersByOrg[slug] ?? []).filter((member) => member.id !== memberId)

  return { ok: true }
})

import { requireAuthPayload } from '../../../utils/jwt'
import { mockMembersByOrg } from '../../../utils/mockData'

export default defineEventHandler((event) => {
  requireAuthPayload(event)
  const slug = getRouterParam(event, 'slug') || ''

  return {
    members: mockMembersByOrg[slug] ?? []
  }
})

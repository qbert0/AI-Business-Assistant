import { requireAuthPayload } from '../../utils/jwt'
import { mockJoinRequests, mockOrganizations } from '../../utils/mockData'

export default defineEventHandler((event) => {
  requireAuthPayload(event)

  return {
    organizations: mockOrganizations,
    joinRequests: mockJoinRequests
  }
})

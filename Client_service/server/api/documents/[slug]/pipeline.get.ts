import { requireAuthPayload } from '../../../utils/jwt'
import { mockPipelineByOrg } from '../../../utils/mockData'

export default defineEventHandler((event) => {
  requireAuthPayload(event)
  const slug = getRouterParam(event, 'slug') || ''

  return {
    pipeline: mockPipelineByOrg[slug] ?? []
  }
})

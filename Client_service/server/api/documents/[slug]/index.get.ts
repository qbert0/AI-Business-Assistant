import { requireAuthPayload } from '../../../utils/jwt'
import { mockDocumentsByOrg } from '../../../utils/mockData'

export default defineEventHandler((event) => {
  requireAuthPayload(event)
  const slug = getRouterParam(event, 'slug') || ''

  return {
    documents: mockDocumentsByOrg[slug] ?? []
  }
})

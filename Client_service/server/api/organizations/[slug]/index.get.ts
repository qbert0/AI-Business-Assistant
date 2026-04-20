import { requireAuthPayload } from '../../../utils/jwt'
import { mockOrganizations } from '../../../utils/mockData'

export default defineEventHandler((event) => {
  requireAuthPayload(event)
  const slug = getRouterParam(event, 'slug')
  const organization = mockOrganizations.find((item) => item.slug === slug)

  if (!organization) {
    throw createError({ statusCode: 404, statusMessage: 'Organization not found' })
  }

  return { organization }
})

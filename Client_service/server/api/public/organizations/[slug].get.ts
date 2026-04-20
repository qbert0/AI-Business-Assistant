import { mockOrganizations } from '../../../utils/mockData'

export default defineEventHandler((event) => {
  const slug = getRouterParam(event, 'slug')
  const organization = mockOrganizations.find((item) => item.slug === slug)

  if (!organization) {
    throw createError({ statusCode: 404, statusMessage: 'Organization not found' })
  }

  return {
    organization,
    allowJoinRequests: true
  }
})

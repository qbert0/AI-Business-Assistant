import { backendFetch, mapOrganization } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  const orgId = getRouterParam(event, 'slug')
  if (!orgId) {
    throw createError({ statusCode: 400, statusMessage: 'Organization id is required' })
  }

  const organization = await backendFetch<any>(event, `/organizations/${orgId}`)

  return {
    organization: mapOrganization(organization),
    allowJoinRequests: false
  }
})

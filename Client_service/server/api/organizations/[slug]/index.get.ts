import { backendFetch, mapOrganization } from '../../../utils/backend'

interface BackendOrganization {
  id: string
  name: string
  industry?: string | null
  description?: string | null
  billing_status?: string | null
}

export default defineEventHandler(async (event) => {
  const orgId = getRouterParam(event, 'slug')
  if (!orgId) {
    throw createError({ statusCode: 400, statusMessage: 'Organization id is required' })
  }

  const organization = await backendFetch<BackendOrganization>(event, `/organizations/${orgId}`)
  return { organization: mapOrganization(organization) }
})

import { backendFetch, mapOrganization } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  const query = String(getQuery(event).q || '').trim()
  const organizations = await backendFetch<any[]>(
    event,
    `/organizations?search=${encodeURIComponent(query)}&limit=12`
  )

  return {
    organizations: organizations.map((organization) => mapOrganization(organization))
  }
})

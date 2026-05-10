import { backendFetch, getBackendUser } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''

  return backendFetch(event, `/organizations/${orgId}/analytics?acting_user_id=${encodeURIComponent(user.id)}`)
})

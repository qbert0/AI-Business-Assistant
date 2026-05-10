import { backendFetch, getBackendUser } from '../../../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''

  await backendFetch(
    event,
    `/organizations/${orgId}/membership?acting_user_id=${encodeURIComponent(user.id)}`,
    {
      method: 'DELETE'
    }
  )

  return { ok: true }
})

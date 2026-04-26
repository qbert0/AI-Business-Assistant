import { backendFetch, getBackendUser } from '../../../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const memberId = getRouterParam(event, 'memberId') || ''

  await backendFetch(event, `/organizations/${orgId}/members/${memberId}?acting_user_id=${encodeURIComponent(user.id)}`, {
    method: 'DELETE'
  })

  return { ok: true }
})

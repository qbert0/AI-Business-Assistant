import { backendFetch, getBackendUser, mapMember } from '../../../../utils/backend'

export default defineEventHandler(async (event) => {
  const orgId = String(getRouterParam(event, 'slug') || '')
  const user = await getBackendUser(event)
  const member = await backendFetch<any>(
    event,
    `/organizations/${orgId}/membership/decline?acting_user_id=${encodeURIComponent(user.id)}`,
    { method: 'POST' }
  )

  return {
    member: mapMember(member)
  }
})

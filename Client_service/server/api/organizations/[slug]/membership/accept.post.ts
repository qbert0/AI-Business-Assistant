import { backendFetch, getBackendUser, mapMember } from '../../../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const member = await backendFetch<any>(
    event,
    `/organizations/${orgId}/membership/accept?acting_user_id=${encodeURIComponent(user.id)}`,
    {
      method: 'POST'
    }
  )

  return { member: mapMember(member) }
})

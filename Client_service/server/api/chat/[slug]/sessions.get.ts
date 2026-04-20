import { backendFetch, getBackendUser, mapChatSession } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const cursor = Number(getQuery(event).cursor ?? 0)
  const limit = Number(getQuery(event).limit ?? 8)
  const sessions = await backendFetch<any[]>(
    event,
    `/organizations/${orgId}/chat/sessions?acting_user_id=${encodeURIComponent(user.id)}`
  )
  const mapped = sessions.map(mapChatSession)

  return {
    sessions: mapped.slice(cursor, cursor + limit),
    nextCursor: cursor + limit < mapped.length ? cursor + limit : null
  }
})

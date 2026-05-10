import { backendFetch, getBackendUser, mapChatSession } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const cursor = Number(getQuery(event).cursor ?? 0)
  const limit = Number(getQuery(event).limit ?? 10)
  const backendPath = orgId === 'personal'
    ? `/chat/personal/sessions?acting_user_id=${encodeURIComponent(user.id)}&skip=${cursor}&limit=${limit + 1}`
    : `/organizations/${orgId}/chat/sessions?acting_user_id=${encodeURIComponent(user.id)}&skip=${cursor}&limit=${limit + 1}`
  const sessions = await backendFetch<any[]>(
    event,
    backendPath
  )
  const mapped = sessions.slice(0, limit).map(mapChatSession)

  return {
    sessions: mapped,
    nextCursor: sessions.length > limit ? cursor + limit : null
  }
})

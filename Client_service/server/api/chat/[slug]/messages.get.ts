import { backendFetch, getBackendUser, mapChatMessage } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const query = getQuery(event)
  const sessionId = String(query.sessionId || '')
  const cursor = Number(query.cursor ?? 0)
  const limit = Number(query.limit ?? 20)

  if (!sessionId) {
    return { messages: [], nextCursor: null }
  }

  const messages = await backendFetch<any[]>(
    event,
    `/chat/sessions/${sessionId}/messages?acting_user_id=${encodeURIComponent(user.id)}`
  )
  const mapped = messages.map(mapChatMessage)
  const start = Math.max(0, mapped.length - cursor - limit)
  const end = mapped.length - cursor

  return {
    messages: mapped.slice(start, end),
    nextCursor: start > 0 ? mapped.length - start : null
  }
})

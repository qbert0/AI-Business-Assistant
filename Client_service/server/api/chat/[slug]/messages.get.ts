import { requireAuthPayload } from '../../../utils/jwt'
import { mockMessagesBySession, mockSessionsByOrg } from '../../../utils/mockData'

export default defineEventHandler((event) => {
  requireAuthPayload(event)
  const slug = getRouterParam(event, 'slug') || 'personal'
  const query = getQuery(event)
  const sessionId = String(query.sessionId || mockSessionsByOrg[slug]?.[0]?.id || '')
  const cursor = Number(query.cursor ?? 0)
  const limit = Number(query.limit ?? 20)
  const messages = sessionId ? mockMessagesBySession[sessionId] ?? [] : []
  const start = Math.max(0, messages.length - cursor - limit)
  const end = messages.length - cursor

  return {
    messages: messages.slice(start, end),
    nextCursor: start > 0 ? messages.length - start : null
  }
})

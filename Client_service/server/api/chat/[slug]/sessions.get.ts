import { requireAuthPayload } from '../../../utils/jwt'
import { mockSessionsByOrg } from '../../../utils/mockData'

export default defineEventHandler((event) => {
  requireAuthPayload(event)
  const slug = getRouterParam(event, 'slug') || 'personal'
  const cursor = Number(getQuery(event).cursor ?? 0)
  const limit = Number(getQuery(event).limit ?? 8)
  const sessions = mockSessionsByOrg[slug] ?? []

  return {
    sessions: sessions.slice(cursor, cursor + limit),
    nextCursor: cursor + limit < sessions.length ? cursor + limit : null
  }
})

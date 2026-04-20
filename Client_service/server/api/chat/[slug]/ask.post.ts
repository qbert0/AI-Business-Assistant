import { z } from 'zod'
import { backendFetch, getBackendUser, mapChatMessage, mapChatSession } from '../../../utils/backend'

const askSchema = z.object({
  prompt: z.string().min(1).max(4000),
  sessionId: z.string().nullable().optional()
})

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const body = askSchema.parse(await readBody(event))
  const response = await backendFetch<any>(event, `/organizations/${orgId}/chat/ask`, {
    method: 'POST',
    body: {
      user_id: user.id,
      question: body.prompt,
      session_id: body.sessionId || null
    }
  })

  return {
    session: mapChatSession(response.session),
    messages: [response.user_message, response.assistant_message].map(mapChatMessage)
  }
})

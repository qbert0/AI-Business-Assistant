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
  const backendPath = orgId === 'personal' ? '/chat/personal/ask' : `/organizations/${orgId}/chat/ask`
  const response = await backendFetch<any>(event, backendPath, {
    method: 'POST',
    body: {
      user_id: user.id,
      question: body.prompt,
      session_id: body.sessionId || null
    }
  })

  return {
    session: mapChatSession(response.session),
    messages: [
      mapChatMessage(response.user_message),
      {
        ...mapChatMessage(response.assistant_message),
        searchHits: (response.search_hits || []).map((item: any) => ({
          documentId: item.document_id,
          fileName: item.file_name,
          documentName: item.document_name ?? item.file_name,
          sourceUrl: item.source_url,
          chunkId: item.chunk_id ?? null,
          hitType: item.hit_type ?? null,
          score: item.score ?? null
        }))
      }
    ]
  }
})

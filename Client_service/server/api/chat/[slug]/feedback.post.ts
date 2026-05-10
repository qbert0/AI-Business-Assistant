import { z } from 'zod'
import { backendFetch, getBackendUser } from '../../../utils/backend'

const feedbackSchema = z.object({
  messageId: z.string().min(1),
  rating: z.enum(['positive', 'negative']),
  comment: z.string().max(1000).default('')
})

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const body = feedbackSchema.parse(await readBody(event))

  await backendFetch(event, `/chat/messages/${body.messageId}/feedback`, {
    method: 'POST',
    body: {
      user_id: user.id,
      rating: body.rating,
      comment: body.comment
    }
  })

  return { ok: true }
})

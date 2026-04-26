import { z } from 'zod'
import { getBackendUser } from '../../../utils/backend'

const feedbackSchema = z.object({
  rating: z.enum(['positive', 'negative']),
  comment: z.string().max(1000).default('')
})

export default defineEventHandler(async (event) => {
  await getBackendUser(event)
  feedbackSchema.parse(await readBody(event))

  return { ok: true }
})

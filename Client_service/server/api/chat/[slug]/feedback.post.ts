import { z } from 'zod'
import { requireAuthPayload } from '../../../utils/jwt'
import { mockFeedback } from '../../../utils/mockData'

const feedbackSchema = z.object({
  rating: z.enum(['positive', 'negative']),
  comment: z.string().max(1000).default('')
})

export default defineEventHandler(async (event) => {
  requireAuthPayload(event)
  const slug = getRouterParam(event, 'slug') || 'personal'
  const body = feedbackSchema.parse(await readBody(event))

  mockFeedback.unshift({
    id: `f-${Date.now()}`,
    organizationSlug: slug,
    rating: body.rating,
    comment: body.comment,
    createdAt: new Date().toISOString().slice(0, 10)
  })

  return { ok: true }
})

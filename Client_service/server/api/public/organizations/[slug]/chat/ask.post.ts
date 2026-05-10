import { z } from 'zod'
import { backendFetch } from '../../../../../utils/backend'

const schema = z.object({
  question: z.string().trim().min(1)
})

export default defineEventHandler(async (event) => {
  const orgId = getRouterParam(event, 'slug') || ''
  const body = schema.parse(await readBody(event))
  return backendFetch(event, `/organizations/${orgId}/public/chat/ask`, {
    method: 'POST',
    body
  })
})

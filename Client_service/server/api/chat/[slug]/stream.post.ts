import { z } from 'zod'

import { getBackendBaseUrl, getBackendUser } from '../../../utils/backend'

const streamSchema = z.object({
  question: z.string().min(1).max(4000),
  sessionId: z.string().nullable().optional(),
  userId: z.string().optional()
})

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const body = streamSchema.parse(await readBody(event))
  const backendPath = orgId === 'personal'
    ? '/chat/personal/ask/stream'
    : `/organizations/${orgId}/chat/ask/stream`

  const response = await fetch(`${getBackendBaseUrl()}${backendPath}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(getHeader(event, 'authorization') ? { Authorization: getHeader(event, 'authorization') as string } : {})
    },
    body: JSON.stringify({
      user_id: user.id,
      question: body.question,
      session_id: body.sessionId || null
    })
  })

  if (!response.ok || !response.body) {
    const detail = await response.text()
    throw createError({
      statusCode: response.status,
      statusMessage: detail || response.statusText || 'Chat stream failed'
    })
  }

  const contentType = response.headers.get('content-type') || 'application/x-ndjson'
  const cacheControl = response.headers.get('cache-control')
  const accelBuffering = response.headers.get('x-accel-buffering')

  setHeader(event, 'content-type', contentType)
  if (cacheControl) {
    setHeader(event, 'cache-control', cacheControl)
  }
  if (accelBuffering) {
    setHeader(event, 'x-accel-buffering', accelBuffering)
  }

  return sendStream(event, response.body)
})

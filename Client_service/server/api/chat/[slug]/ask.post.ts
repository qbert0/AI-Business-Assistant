import { z } from 'zod'
import { requireAuthPayload } from '../../../utils/jwt'
import { mockMessagesBySession, mockSessionsByOrg } from '../../../utils/mockData'

const askSchema = z.object({
  prompt: z.string().min(1).max(4000),
  sessionId: z.string().nullable().optional()
})

export default defineEventHandler(async (event) => {
  requireAuthPayload(event)
  const slug = getRouterParam(event, 'slug') || 'personal'
  const body = askSchema.parse(await readBody(event))
  const sessions = mockSessionsByOrg[slug] ?? []
  const existingSession = body.sessionId ? sessions.find((session) => session.id === body.sessionId) : sessions[0]
  const sessionId = existingSession?.id ?? `session-${Date.now()}`
  const updatedAt = new Date().toISOString().slice(0, 16).replace('T', ' ')

  if (!existingSession) {
    mockSessionsByOrg[slug] = [
      {
        id: sessionId,
        organizationSlug: slug,
        title: body.prompt.length > 52 ? `${body.prompt.slice(0, 49)}...` : body.prompt,
        updatedAt,
        preview: body.prompt
      },
      ...sessions
    ]
  } else {
    mockSessionsByOrg[slug] = [
      { ...existingSession, updatedAt, preview: body.prompt },
      ...sessions.filter((session) => session.id !== existingSession.id)
    ]
  }

  const userMessage = { id: `u-${Date.now()}`, role: 'user' as const, content: body.prompt }
  const assistantMessage = {
    id: `a-${Date.now()}`,
    role: 'assistant' as const,
    content: 'Mock server returned a grounded answer. A real backend would run retrieval, rerank, guardrails, and advisory agent orchestration before returning this response.',
    citations: ['Top retrieved chunks', 'Policy summary node']
  }

  mockMessagesBySession[sessionId] = [
    ...(mockMessagesBySession[sessionId] ?? []),
    userMessage,
    assistantMessage
  ]

  return {
    session: mockSessionsByOrg[slug].find((session) => session.id === sessionId),
    messages: [userMessage, assistantMessage]
  }
})

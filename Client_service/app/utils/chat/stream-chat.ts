import { getClientAuthToken } from '@/utils/auth-token'

type StreamEventHandler = (event: Record<string, any>) => void

export const streamChatAnswer = async (
  slug: string,
  body: { question: string, sessionId?: string | null, userId: string },
  onEvent: StreamEventHandler,
) => {
  const token = getClientAuthToken()
  const response = await fetch(`/api/chat/${slug}/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({
      question: body.question,
      userId: body.userId,
      sessionId: body.sessionId || null
    })
  })

  if (!response.ok || !response.body) {
    const detail = await response.text()
    throw new Error(detail || `Chat stream failed with status ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      const raw = line.trim()
      if (!raw) {
        continue
      }
      onEvent(JSON.parse(raw))
    }
  }

  const tail = buffer.trim()
  if (tail) {
    onEvent(JSON.parse(tail))
  }
}

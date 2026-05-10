import type { ChatMessage, ChatSession, PopularQuestion, SuggestionQuestion } from '@/types/organization'

import { useApiFetch } from '@/composables/api/core/useApiFetch'

export const useApiChat = () => {
  const apiFetch = useApiFetch()

  const sessions = (slug: string, cursor = 0, limit = 8) =>
    apiFetch<{ sessions: ChatSession[], nextCursor: number | null }>(`/api/chat/${slug}/sessions`, {
      query: { cursor, limit }
    })

  const messages = (slug: string, sessionId?: string | null, cursor = 0, limit = 20) =>
    apiFetch<{ messages: ChatMessage[], nextCursor: number | null }>(`/api/chat/${slug}/messages`, {
      query: { sessionId, cursor, limit }
    })

  const ask = (slug: string, prompt: string, sessionId?: string | null) =>
    apiFetch<{ session: ChatSession, messages: ChatMessage[] }>(`/api/chat/${slug}/ask`, {
      method: 'POST',
      body: { prompt, sessionId }
    })

  const suggestions = (slug: string) =>
    apiFetch<{ suggestions: SuggestionQuestion[], popularQuestions: PopularQuestion[] }>(`/api/chat/${slug}/suggestions`)

  const feedback = (slug: string, messageId: string, rating: 'positive' | 'negative', comment: string) =>
    apiFetch<{ ok: boolean }>(`/api/chat/${slug}/feedback`, {
      method: 'POST',
      body: { messageId, rating, comment }
    })

  return {
    sessions,
    messages,
    ask,
    suggestions,
    feedback
  }
}

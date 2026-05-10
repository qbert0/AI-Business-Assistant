import type { ChatSession, PopularQuestion, SuggestionQuestion } from '@/types/organization'

interface ChatSessionContextState {
  sessions: ChatSession[]
  sessionCursor: number | null
  suggestions: SuggestionQuestion[]
  popularQuestions: PopularQuestion[]
}

const createSessionContextState = (): ChatSessionContextState => ({
  sessions: [],
  sessionCursor: 0,
  suggestions: [],
  popularQuestions: []
})

import { useApiChat } from '@/composables/api/chat/useApiChat'

export const useChatSessionStore = defineStore('chat-sessions', () => {
  const api = useApiChat()
  const contexts = ref<Record<string, ChatSessionContextState>>({})
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const ensureContext = (slug: string) => {
    if (!contexts.value[slug]) {
      contexts.value[slug] = createSessionContextState()
    }

    return contexts.value[slug]
  }

  const getSessions = (slug: string) => ensureContext(slug).sessions
  const getSuggestions = (slug: string) => ensureContext(slug).suggestions
  const getPopularQuestions = (slug: string) => ensureContext(slug).popularQuestions

  const loadContext = async (slug: string) => {
    isLoading.value = true
    error.value = null

    try {
      const [sessionResponse, suggestionResponse] = await Promise.all([
        api.sessions(slug, 0, 8),
        api.suggestions(slug)
      ])
      const context = ensureContext(slug)
      context.sessions = sessionResponse.sessions
      context.sessionCursor = sessionResponse.nextCursor
      context.suggestions = suggestionResponse.suggestions
      context.popularQuestions = suggestionResponse.popularQuestions
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Cannot load chat context'
    } finally {
      isLoading.value = false
    }
  }

  const loadMoreSessions = async (slug: string) => {
    const context = ensureContext(slug)
    if (context.sessionCursor === null) {
      return
    }

    const response = await api.sessions(slug, context.sessionCursor, 8)
    context.sessions = [...context.sessions, ...response.sessions]
    context.sessionCursor = response.nextCursor
  }

  const upsertSession = (slug: string, session: ChatSession) => {
    const context = ensureContext(slug)
    context.sessions = [
      session,
      ...context.sessions.filter((item) => item.id !== session.id)
    ]
  }

  const renameSession = async (slug: string, sessionId: string, title: string) => {
    const context = ensureContext(slug)
    context.sessions = context.sessions.map((session) => (session.id === sessionId ? { ...session, title } : session))
  }

  const togglePinSession = async (slug: string, sessionId: string) => {
    const context = ensureContext(slug)
    context.sessions = context.sessions
      .map((session) => (session.id === sessionId ? { ...session, isPinned: !session.isPinned } : session))
      .sort((a, b) => Number(Boolean(b.isPinned)) - Number(Boolean(a.isPinned)))
  }

  const deleteSession = async (slug: string, sessionId: string) => {
    const context = ensureContext(slug)
    const targetSession = context.sessions.find((session) => session.id === sessionId)
    if (targetSession?.isDeletionRestricted) {
      return false
    }

    context.sessions = context.sessions.filter((session) => session.id !== sessionId)
    return true
  }

  return {
    contexts,
    isLoading,
    error,
    getSessions,
    getSuggestions,
    getPopularQuestions,
    loadContext,
    loadMoreSessions,
    upsertSession,
    renameSession,
    togglePinSession,
    deleteSession
  }
})

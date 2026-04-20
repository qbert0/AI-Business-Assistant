import type { ChatMessage, ChatSession, PopularQuestion, SuggestionQuestion } from '@/types/organization'

interface ChatContextState {
  sessions: ChatSession[]
  sessionCursor: number | null
  messagesBySession: Record<string, ChatMessage[]>
  messageCursorBySession: Record<string, number | null>
  suggestions: SuggestionQuestion[]
  popularQuestions: PopularQuestion[]
}

const createContextState = (): ChatContextState => ({
  sessions: [],
  sessionCursor: 0,
  messagesBySession: {},
  messageCursorBySession: {},
  suggestions: [],
  popularQuestions: []
})

export const useChatStore = defineStore('chat', () => {
  const contexts = ref<Record<string, ChatContextState>>({})
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const ensureContext = (slug: string) => {
    if (!contexts.value[slug]) {
      contexts.value[slug] = createContextState()
    }

    return contexts.value[slug]
  }

  const getSessions = (slug: string) => ensureContext(slug).sessions
  const getSuggestions = (slug: string) => ensureContext(slug).suggestions
  const getPopularQuestions = (slug: string) => ensureContext(slug).popularQuestions
  const getMessages = (slug: string, sessionId?: string | null) => {
    const context = ensureContext(slug)
    const targetSessionId = sessionId ?? context.sessions[0]?.id
    return targetSessionId ? context.messagesBySession[targetSessionId] ?? [] : []
  }

  const loadContext = async (slug: string) => {
    const api = useApiChat()
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

    const api = useApiChat()
    const response = await api.sessions(slug, context.sessionCursor, 8)
    context.sessions = [...context.sessions, ...response.sessions]
    context.sessionCursor = response.nextCursor
  }

  const loadMessages = async (slug: string, sessionId?: string | null) => {
    if (!sessionId) {
      return
    }

    const context = ensureContext(slug)
    const api = useApiChat()
    const response = await api.messages(slug, sessionId, 0, 20)
    context.messagesBySession[sessionId] = response.messages
    context.messageCursorBySession[sessionId] = response.nextCursor
  }

  const loadOlderMessages = async (slug: string, sessionId: string) => {
    const context = ensureContext(slug)
    const cursor = context.messageCursorBySession[sessionId]
    if (cursor === null || cursor === undefined) {
      return
    }

    const api = useApiChat()
    const response = await api.messages(slug, sessionId, cursor, 20)
    context.messagesBySession[sessionId] = [
      ...response.messages,
      ...(context.messagesBySession[sessionId] ?? [])
    ]
    context.messageCursorBySession[sessionId] = response.nextCursor
  }

  const askQuestion = async (slug: string, prompt: string, sessionId?: string | null) => {
    const api = useApiChat()
    const response = await api.ask(slug, prompt, sessionId)
    const context = ensureContext(slug)
    const targetSessionId = response.session.id
    context.sessions = [
      response.session,
      ...context.sessions.filter((session) => session.id !== targetSessionId)
    ]
    context.messagesBySession[targetSessionId] = [
      ...(context.messagesBySession[targetSessionId] ?? []),
      ...response.messages
    ]
    return targetSessionId
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
    const { [sessionId]: _deleted, ...remainingMessages } = context.messagesBySession
    context.messagesBySession = remainingMessages
    return true
  }

  const submitFeedback = async (slug: string, rating: 'positive' | 'negative', comment: string) => {
    const api = useApiChat()
    await api.feedback(slug, rating, comment)
  }

  return {
    contexts,
    isLoading,
    error,
    getSessions,
    getSuggestions,
    getPopularQuestions,
    getMessages,
    loadContext,
    loadMoreSessions,
    loadMessages,
    loadOlderMessages,
    askQuestion,
    renameSession,
    togglePinSession,
    deleteSession,
    submitFeedback
  }
})

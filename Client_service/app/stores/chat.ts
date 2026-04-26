import { streamChatAnswer } from '@/utils/chat-stream'
import type { ChatMessage, ChatSearchHit, ChatSession, PopularQuestion, SuggestionQuestion } from '@/types/organization'
import { useAuthStore } from './auth'

interface ChatContextState {
  sessions: ChatSession[]
  sessionCursor: number | null
  messagesBySession: Record<string, ChatMessage[]>
  messageCursorBySession: Record<string, number | null>
  suggestions: SuggestionQuestion[]
  popularQuestions: PopularQuestion[]
  streamingStatus: string | null
  isStreaming: boolean
}

const createContextState = (): ChatContextState => ({
  sessions: [],
  sessionCursor: 0,
  messagesBySession: {},
  messageCursorBySession: {},
  suggestions: [],
  popularQuestions: [],
  streamingStatus: null,
  isStreaming: false
})

const mapStreamSession = (session: any): ChatSession => ({
  id: session.id,
  organizationSlug: session.organization_id || 'personal',
  title: session.title,
  updatedAt: String(session.updated_at || '').slice(0, 16).replace('T', ' '),
  preview: session.title,
  isPinned: Boolean(session.is_pinned)
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
  const getStreamingStatus = (slug: string) => ensureContext(slug).streamingStatus
  const getIsStreaming = (slug: string) => ensureContext(slug).isStreaming
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
    const context = ensureContext(slug)
    const auth = useAuthStore()
    const currentUser = auth.user
    if (!currentUser) {
      throw new Error('Bạn chưa đăng nhập.')
    }

    isLoading.value = true
    error.value = null
    context.isStreaming = true
    context.streamingStatus = 'Đang chuẩn bị câu trả lời.'

    let activeSessionId = sessionId ?? null
    let tempAssistantMessage: ChatMessage | null = null
    const localUserMessageId = `local-user-${Date.now()}`

    try {
      await streamChatAnswer(
        slug,
        {
          question: prompt,
          sessionId,
          userId: currentUser.id
        },
        (event) => {
          if (event.type === 'session') {
            const session = mapStreamSession(event.session)
            activeSessionId = session.id
            context.sessions = [
              session,
              ...context.sessions.filter((item) => item.id !== session.id)
            ]
            const existingMessages = context.messagesBySession[session.id] ?? []
            tempAssistantMessage = {
              id: `stream-${session.id}`,
              role: 'assistant',
              content: '',
              citations: [],
              searchHits: [],
              status: 'thinking',
              activity: context.streamingStatus
            }
            context.messagesBySession[session.id] = [
              ...existingMessages,
              {
                id: localUserMessageId,
                role: 'user',
                content: prompt,
                citations: [],
                searchHits: [],
                status: 'complete',
                activity: null
              },
              tempAssistantMessage
            ]
            return
          }

          if (!activeSessionId) {
            return
          }

          const messages = context.messagesBySession[activeSessionId] ?? []
          const assistantIndex = messages.findIndex((item) => item.id === tempAssistantMessage?.id)
          const ensureAssistant = () => {
            if (assistantIndex >= 0) {
              return messages[assistantIndex]
            }
            const created: ChatMessage = {
              id: `stream-${activeSessionId}`,
              role: 'assistant',
              content: '',
              citations: [],
              searchHits: [],
              status: 'thinking',
              activity: context.streamingStatus
            }
            context.messagesBySession[activeSessionId] = [...messages, created]
            tempAssistantMessage = created
            return created
          }
          const assistantMessage = ensureAssistant()

          if (event.type === 'status') {
            context.streamingStatus = event.message || null
            assistantMessage.activity = event.message || null
            assistantMessage.status = event.stage === 'answering' ? 'streaming' : 'thinking'
            return
          }

          if (event.type === 'search_results') {
            assistantMessage.citations = event.citations?.map((item: any) => ({
              documentId: item.document_id,
              fileName: item.file_name,
              sourceUrl: item.source_url
            })) ?? []
            assistantMessage.searchHits = event.hits?.map((item: any): ChatSearchHit => ({
              documentId: item.document_id,
              fileName: item.file_name,
              sourceUrl: item.source_url,
              score: item.score ?? null
            })) ?? []
            return
          }

          if (event.type === 'answer_chunk') {
            assistantMessage.content += event.chunk || ''
            assistantMessage.status = 'streaming'
            assistantMessage.activity = context.streamingStatus
            return
          }

          if (event.type === 'error') {
            context.streamingStatus = event.message || 'Trả lời thất bại.'
            assistantMessage.status = 'error'
            assistantMessage.activity = event.message || null
            if (!assistantMessage.content) {
              assistantMessage.content = event.message || 'Trả lời thất bại.'
            }
            return
          }

          if (event.type === 'complete') {
            const response = event.response as any
            const finalSession = mapStreamSession(response.session)
            const finalMessages: ChatMessage[] = [
              {
                id: response.user_message.id,
                role: 'user',
                content: response.user_message.content,
                citations: [],
                searchHits: [],
                status: 'complete',
                activity: null
              },
              {
                id: response.assistant_message.id,
                role: 'assistant',
                content: response.assistant_message.content,
                citations: (response.assistant_message.citations || []).map((item: any) => ({
                  documentId: item.document_id,
                  fileName: item.file_name,
                  sourceUrl: item.source_url
                })),
                searchHits: (response.search_hits || []).map((item: any) => ({
                  documentId: item.document_id,
                  fileName: item.file_name,
                  sourceUrl: item.source_url,
                  score: item.score ?? null
                })),
                status: 'complete',
                activity: null
              }
            ]
            context.sessions = [
              finalSession,
              ...context.sessions.filter((item) => item.id !== finalSession.id)
            ]
            context.messagesBySession[finalSession.id] = [
              ...(context.messagesBySession[finalSession.id] ?? []).filter(
                (item) => item.id !== tempAssistantMessage?.id && item.id !== localUserMessageId
              ),
              ...finalMessages
            ]
            activeSessionId = finalSession.id
          }
        }
      )
      return activeSessionId
    } catch (err) {
      const detail = err instanceof Error ? err.message : 'Không thể stream câu trả lời.'
      error.value = detail
      context.streamingStatus = 'Trả lời thất bại.'
      if (activeSessionId) {
        const messages = context.messagesBySession[activeSessionId] ?? []
        const assistantMessage = messages.find((item) => item.id === tempAssistantMessage?.id)
        if (assistantMessage) {
          assistantMessage.status = 'error'
          assistantMessage.activity = detail
          if (!assistantMessage.content) {
            assistantMessage.content = detail
          }
        }
      }
      throw err
    } finally {
      context.isStreaming = false
      if (context.streamingStatus !== 'Trả lời thất bại.') {
        context.streamingStatus = null
      }
      isLoading.value = false
    }
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
    getStreamingStatus,
    getIsStreaming,
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

import { useAuthStore } from '@/stores/auth/useAuthStore'
import { useChatSessionStore } from '@/stores/chat/useChatSessionStore'
import { streamChatAnswer } from '@/utils/chat-stream'
import { useApiChat } from '@/composables/api/chat/useApiChat'
import { useAuthStore } from '@/stores/auth/useAuthStore'
import { useChatSessionStore } from '@/stores/chat/useChatSessionStore'
import type { ChatMessage, ChatSearchHit, ChatSession } from '@/types/organization'

interface StreamSessionPayload {
  id: string
  organization_id?: string | null
  title: string
  updated_at?: string | null
  is_pinned?: boolean | null
}

interface StreamCitationPayload {
  document_id: string
  file_name: string
  source_url: string
}

interface StreamSearchHitPayload extends StreamCitationPayload {
  score?: number | null
}

interface StreamMessagePayload {
  id: string
  content: string
  citations?: StreamCitationPayload[]
  artifacts?: Array<{ kind?: 'pdf', label?: string, file_name?: string, source_url?: string, download_url?: string | null, content_type?: string | null }>
}

interface StreamCompletePayload {
  session: StreamSessionPayload
  user_message: StreamMessagePayload
  assistant_message: StreamMessagePayload
  search_hits?: StreamSearchHitPayload[]
}

interface StreamEventPayload {
  type: 'session' | 'status' | 'search_results' | 'answer_chunk' | 'error' | 'complete'
  session?: StreamSessionPayload
  message?: string | null
  stage?: string | null
  citations?: StreamCitationPayload[]
  hits?: StreamSearchHitPayload[]
  chunk?: string | null
  response?: StreamCompletePayload
}

interface ChatMessageContextState {
  messagesBySession: Record<string, ChatMessage[]>
  messageCursorBySession: Record<string, number | null>
  streamingStatus: string | null
  isStreaming: boolean
}

const createMessageContextState = (): ChatMessageContextState => ({
  messagesBySession: {},
  messageCursorBySession: {},
  streamingStatus: null,
  isStreaming: false
})

const mapStreamSession = (session: StreamSessionPayload): ChatSession => ({
  id: session.id,
  organizationSlug: session.organization_id || 'personal',
  title: session.title,
  updatedAt: String(session.updated_at || '').slice(0, 16).replace('T', ' '),
  preview: session.title,
  isPinned: Boolean(session.is_pinned)
})

export const useChatMessageStore = defineStore('chat-messages', () => {
  const api = useApiChat()
  const contexts = ref<Record<string, ChatMessageContextState>>({})
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const ensureContext = (slug: string) => {
    if (!contexts.value[slug]) {
      contexts.value[slug] = createMessageContextState()
    }

    return contexts.value[slug]
  }

  const getMessages = (slug: string, sessionId?: string | null) => {
    if (!sessionId) {
      return []
    }

    return ensureContext(slug).messagesBySession[sessionId] ?? []
  }

  const getStreamingStatus = (slug: string) => ensureContext(slug).streamingStatus
  const getIsStreaming = (slug: string) => ensureContext(slug).isStreaming

  const loadMessages = async (slug: string, sessionId?: string | null) => {
    if (!sessionId) {
      return
    }

    const context = ensureContext(slug)
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

    const response = await api.messages(slug, sessionId, cursor, 20)
    context.messagesBySession[sessionId] = [
      ...response.messages,
      ...(context.messagesBySession[sessionId] ?? [])
    ]
    context.messageCursorBySession[sessionId] = response.nextCursor
  }

  const deleteSessionMessages = (slug: string, sessionId: string) => {
    const context = ensureContext(slug)
    const { [sessionId]: _removedMessages, ...remainingMessages } = context.messagesBySession
    const { [sessionId]: _removedCursor, ...remainingCursors } = context.messageCursorBySession
    context.messagesBySession = remainingMessages
    context.messageCursorBySession = remainingCursors
  }

  const askQuestion = async (slug: string, prompt: string, sessionId?: string | null) => {
    const context = ensureContext(slug)
    const auth = useAuthStore()
    const sessions = useChatSessionStore()
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
        (event: StreamEventPayload) => {
          if (event.type === 'session') {
            if (!event.session) {
              return
            }
            const session = mapStreamSession(event.session)
            activeSessionId = session.id
            sessions.upsertSession(slug, session)
            const existingMessages = context.messagesBySession[session.id] ?? []
            tempAssistantMessage = {
              id: `stream-${session.id}`,
              role: 'assistant',
              content: '',
              citations: [],
              artifacts: [],
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
                artifacts: [],
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
              artifacts: [],
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
            assistantMessage.citations = event.citations?.map((item) => ({
              documentId: item.document_id,
              fileName: item.file_name,
              sourceUrl: item.source_url
            })) ?? []
            assistantMessage.searchHits = event.hits?.map((item): ChatSearchHit => ({
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
            if (!event.response) {
              return
            }
            const response = event.response
            const finalSession = mapStreamSession(response.session)
            const finalMessages: ChatMessage[] = [
              {
                id: response.user_message.id,
                role: 'user',
                content: response.user_message.content,
                citations: [],
                artifacts: [],
                searchHits: [],
                status: 'complete',
                activity: null
              },
              {
                id: response.assistant_message.id,
                role: 'assistant',
                content: response.assistant_message.content,
                citations: (response.assistant_message.citations || []).map((item) => ({
                  documentId: item.document_id,
                  fileName: item.file_name,
                  sourceUrl: item.source_url
                })),
                artifacts: (response.assistant_message.artifacts || []).map((item) => ({
                  kind: 'pdf',
                  label: item.label || 'Xem báo cáo PDF',
                  fileName: item.file_name || 'report.pdf',
                  sourceUrl: item.source_url || '',
                  downloadUrl: item.download_url || null,
                  contentType: item.content_type || null
                })),
                searchHits: (response.search_hits || []).map((item) => ({
                  documentId: item.document_id,
                  fileName: item.file_name,
                  sourceUrl: item.source_url,
                  score: item.score ?? null
                })),
                status: 'complete',
                activity: null
              }
            ]
            sessions.upsertSession(slug, finalSession)
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

  const submitFeedback = async (slug: string, messageId: string, rating: 'positive' | 'negative', comment: string) => {
    const api = useApiChat()
    await api.feedback(slug, messageId, rating, comment)
  }

  return {
    contexts,
    isLoading,
    error,
    getMessages,
    getStreamingStatus,
    getIsStreaming,
    loadMessages,
    loadOlderMessages,
    deleteSessionMessages,
    askQuestion,
    submitFeedback
  }
})

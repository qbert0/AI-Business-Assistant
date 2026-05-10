import { useChatMessageStore } from '@/stores/chat/useChatMessageStore'
import { useChatSessionStore } from '@/stores/chat/useChatSessionStore'

export const useChatStore = defineStore('chat', () => {
  const sessions = useChatSessionStore()
  const messages = useChatMessageStore()

  return {
    contexts: computed(() => ({
      sessions: sessions.contexts,
      messages: messages.contexts
    })),
    isLoading: computed(() => sessions.isLoading || messages.isLoading),
    error: computed(() => sessions.error || messages.error),
    getSessions: sessions.getSessions,
    getSuggestions: sessions.getSuggestions,
    getPopularQuestions: sessions.getPopularQuestions,
    getMessages: messages.getMessages,
    getStreamingStatus: messages.getStreamingStatus,
    getIsStreaming: messages.getIsStreaming,
    loadContext: sessions.loadContext,
    loadMoreSessions: sessions.loadMoreSessions,
    loadMessages: messages.loadMessages,
    loadOlderMessages: messages.loadOlderMessages,
    askQuestion: messages.askQuestion,
    renameSession: sessions.renameSession,
    togglePinSession: sessions.togglePinSession,
    deleteSession: async (slug: string, sessionId: string) => {
      const deleted = await sessions.deleteSession(slug, sessionId)
      if (deleted) {
        messages.deleteSessionMessages(slug, sessionId)
      }
      return deleted
    },
    submitFeedback: messages.submitFeedback
  }
})

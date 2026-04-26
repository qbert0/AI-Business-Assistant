export const useChatbot = () => {
  const store = useChatStore()

  return {
    loadContext: store.loadContext,
    loadMoreSessions: store.loadMoreSessions,
    loadMessages: store.loadMessages,
    loadOlderMessages: store.loadOlderMessages,
    getSuggestions: store.getSuggestions,
    getPopularQuestions: store.getPopularQuestions,
    getMessages: store.getMessages,
    getSessions: store.getSessions,
    getStreamingStatus: store.getStreamingStatus,
    getIsStreaming: store.getIsStreaming,
    askQuestion: store.askQuestion,
    renameSession: store.renameSession,
    togglePinSession: store.togglePinSession,
    deleteSession: store.deleteSession,
    submitFeedback: store.submitFeedback
  }
}

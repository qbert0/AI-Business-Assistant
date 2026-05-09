export const useDocuments = () => {
  const store = useDocumentStore()

  return {
    isLoading: computed(() => store.isLoading),
    error: computed(() => store.error),
    getDocuments: store.getDocuments,
    getPipeline: store.getPipeline,
    getOpenDocumentIds: store.getOpenDocumentIds,
    getSelectedDocumentId: store.getSelectedDocumentId,
    getPreview: store.getPreview,
    loadDocuments: store.loadDocuments,
    loadPipeline: store.loadPipeline,
    uploadDocument: store.uploadDocument,
    openDocument: store.openDocument,
    selectDocument: store.selectDocument,
    closeDocument: store.closeDocument,
    closeAllDocuments: store.closeAllDocuments,
    loadPreview: store.loadPreview
  }
}

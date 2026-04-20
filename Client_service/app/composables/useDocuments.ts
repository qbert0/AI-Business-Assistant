export const useDocuments = () => {
  const store = useDocumentStore()

  return {
    isLoading: computed(() => store.isLoading),
    error: computed(() => store.error),
    getDocuments: store.getDocuments,
    getPipeline: store.getPipeline,
    loadDocuments: store.loadDocuments,
    loadPipeline: store.loadPipeline,
    uploadDocument: store.uploadDocument
  }
}

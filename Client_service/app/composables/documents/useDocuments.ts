import { useDocumentStore } from '@/stores/documents/useDocumentStore'

export const useDocuments = () => {
  const store = useDocumentStore()

  return {
    isLoading: computed(() => store.isLoading),
    error: computed(() => store.error),
    getDocuments: store.getDocuments,
    getPipeline: store.getPipeline,
    getDocumentGraph: store.getDocumentGraph,
    getOrganizationGraph: store.getOrganizationGraph,
    getOpenDocumentIds: store.getOpenDocumentIds,
    getSelectedDocumentId: store.getSelectedDocumentId,
    getPreview: store.getPreview,
    getSearchResults: store.getSearchResults,
    loadDocuments: store.loadDocuments,
    loadPublicDocuments: store.loadPublicDocuments,
    loadPipeline: store.loadPipeline,
    uploadDocument: store.uploadDocument,
    startAnalysis: store.startAnalysis,
    stopAnalysis: store.stopAnalysis,
    loadDocumentGraph: store.loadDocumentGraph,
    loadOrganizationGraph: store.loadOrganizationGraph,
    searchDocument: store.searchDocument,
    searchOrganization: store.searchOrganization,
    openDocument: store.openDocument,
    selectDocument: store.selectDocument,
    closeDocument: store.closeDocument,
    closeAllDocuments: store.closeAllDocuments,
    loadPreview: store.loadPreview
  }
}

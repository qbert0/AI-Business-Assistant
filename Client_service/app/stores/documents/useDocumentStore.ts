import { useDocumentLibraryStore } from '@/stores/documents/useDocumentLibraryStore'
import { useDocumentViewerStore } from '@/stores/documents/useDocumentViewerStore'

export const useDocumentStore = defineStore('documents', () => {
  const library = useDocumentLibraryStore()
  const viewer = useDocumentViewerStore()

  return {
    documentsByOrg: computed(() => library.documentsByOrg),
    pipelineByOrg: computed(() => library.pipelineByOrg),
    graphByDocumentId: computed(() => library.graphByDocumentId),
    graphByOrg: computed(() => library.graphByOrg),
    isLoading: computed(() => library.isLoading || viewer.isLoading),
    error: computed(() => library.error || viewer.error),
    getDocuments: library.getDocuments,
    getPipeline: library.getPipeline,
    getDocumentGraph: library.getDocumentGraph,
    getOrganizationGraph: library.getOrganizationGraph,
    loadDocuments: library.loadDocuments,
    loadPipeline: library.loadPipeline,
    uploadDocument: library.uploadDocument,
    startAnalysis: library.startAnalysis,
    stopAnalysis: library.stopAnalysis,
    loadDocumentGraph: library.loadDocumentGraph,
    loadOrganizationGraph: library.loadOrganizationGraph,
    getOpenDocumentIds: viewer.getOpenDocumentIds,
    getSelectedDocumentId: viewer.getSelectedDocumentId,
    getPreview: viewer.getPreview,
    openDocument: viewer.openDocument,
    selectDocument: viewer.selectDocument,
    closeDocument: viewer.closeDocument,
    closeAllDocuments: viewer.closeAllDocuments,
    loadPreview: viewer.loadPreview
  }
})

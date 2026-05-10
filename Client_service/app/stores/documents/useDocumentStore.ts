import { useDocumentLibraryStore } from '@/stores/documents/useDocumentLibraryStore'
import { useDocumentViewerStore } from '@/stores/documents/useDocumentViewerStore'

export const useDocumentStore = defineStore('documents', () => {
  const library = useDocumentLibraryStore()
  const viewer = useDocumentViewerStore()

  return {
    documentsByOrg: computed(() => library.documentsByOrg),
    pipelineByOrg: computed(() => library.pipelineByOrg),
    isLoading: computed(() => library.isLoading || viewer.isLoading),
    error: computed(() => library.error || viewer.error),
    getDocuments: library.getDocuments,
    getPipeline: library.getPipeline,
    loadDocuments: library.loadDocuments,
    loadPipeline: library.loadPipeline,
    uploadDocument: library.uploadDocument,
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

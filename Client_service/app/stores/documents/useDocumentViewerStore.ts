import type { KnowledgeDocument } from '@/types/organization'

interface DocumentPreviewPayload {
  kind: string
  content?: string | null
  message?: string | null
  url?: string | null
}

interface DocumentViewerState {
  openDocumentIds: string[]
  selectedDocumentId: string | null
  previewsByDocumentId: Record<string, DocumentPreviewPayload>
}

const createViewerState = (): DocumentViewerState => ({
  openDocumentIds: [],
  selectedDocumentId: null,
  previewsByDocumentId: {}
})

import { useApiDocuments } from '@/composables/api/documents/useApiDocuments'

export const useDocumentViewerStore = defineStore('document-viewer', () => {
  const api = useApiDocuments()
  const stateByOrg = ref<Record<string, DocumentViewerState>>({})
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const ensureState = (slug: string) => {
    if (!stateByOrg.value[slug]) {
      stateByOrg.value[slug] = createViewerState()
    }

    return stateByOrg.value[slug]
  }

  const getOpenDocumentIds = (slug: string) => ensureState(slug).openDocumentIds
  const getSelectedDocumentId = (slug: string) => ensureState(slug).selectedDocumentId
  const getPreview = (slug: string, documentId: string) => ensureState(slug).previewsByDocumentId[documentId] ?? null

  const openDocument = async (slug: string, document: KnowledgeDocument) => {
    const state = ensureState(slug)
    if (!state.openDocumentIds.includes(document.id)) {
      state.openDocumentIds = [...state.openDocumentIds, document.id]
    }

    state.selectedDocumentId = document.id
    await loadPreview(slug, document)
  }

  const selectDocument = async (slug: string, document: KnowledgeDocument) => {
    ensureState(slug).selectedDocumentId = document.id
    await loadPreview(slug, document)
  }

  const closeDocument = (slug: string, documentId: string) => {
    const state = ensureState(slug)
    const currentIndex = state.openDocumentIds.indexOf(documentId)
    state.openDocumentIds = state.openDocumentIds.filter((id) => id !== documentId)

    const { [documentId]: _removedPreview, ...remainingPreviews } = state.previewsByDocumentId
    state.previewsByDocumentId = remainingPreviews

    if (state.selectedDocumentId !== documentId) {
      return
    }

    state.selectedDocumentId = state.openDocumentIds[Math.max(0, currentIndex - 1)] ?? state.openDocumentIds[0] ?? null
  }

  const closeAllDocuments = (slug: string) => {
    const state = ensureState(slug)
    state.openDocumentIds = []
    state.selectedDocumentId = null
    state.previewsByDocumentId = {}
  }

  const loadPreview = async (slug: string, document: KnowledgeDocument) => {
    const state = ensureState(slug)
    const lowerTitle = document.title.toLowerCase()
    const isPdf = lowerTitle.endsWith('.pdf')
    const isImage = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'].some((extension) => lowerTitle.endsWith(extension))

    if (state.previewsByDocumentId[document.id]) {
      return
    }

    isLoading.value = true
    error.value = null

    try {
      const preview = isPdf || isImage
        ? await api.downloadUrl(slug, document.id).then((response) => ({
            kind: isPdf ? 'pdf' : 'image',
            url: response.download_url
          }))
        : await api.preview(slug, document.id)
      state.previewsByDocumentId = {
        ...state.previewsByDocumentId,
        [document.id]: preview
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Cannot load document preview'
      state.previewsByDocumentId = {
        ...state.previewsByDocumentId,
        [document.id]: {
          kind: 'error',
          message: error.value
        }
      }
    } finally {
      isLoading.value = false
    }
  }

  return {
    stateByOrg,
    isLoading,
    error,
    getOpenDocumentIds,
    getSelectedDocumentId,
    getPreview,
    openDocument,
    selectDocument,
    closeDocument,
    closeAllDocuments,
    loadPreview
  }
})

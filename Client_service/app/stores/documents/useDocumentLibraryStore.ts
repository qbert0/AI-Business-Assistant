import type { DocumentGraph, KnowledgeDocument, PipelineStep } from '@/types/organization'

import { useApiDocuments } from '@/composables/api/documents/useApiDocuments'

export const useDocumentLibraryStore = defineStore('document-library', () => {
  const api = useApiDocuments()
  const documentsByOrg = ref<Record<string, KnowledgeDocument[]>>({})
  const pipelineByOrg = ref<Record<string, PipelineStep[]>>({})
  const graphByDocumentId = ref<Record<string, DocumentGraph>>({})
  const graphByOrg = ref<Record<string, DocumentGraph>>({})
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const getDocuments = (slug: string) => documentsByOrg.value[slug] ?? []
  const getPipeline = (slug: string) => pipelineByOrg.value[slug] ?? []
  const getDocumentGraph = (documentId: string) => graphByDocumentId.value[documentId] ?? null
  const getOrganizationGraph = (slug: string) => graphByOrg.value[slug] ?? null

  const loadDocuments = async (slug: string) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.list(slug)
      documentsByOrg.value = {
        ...documentsByOrg.value,
        [slug]: response.documents
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Cannot load documents'
    } finally {
      isLoading.value = false
    }
  }

  const loadPipeline = async (slug: string) => {
    const response = await api.pipeline(slug)
    pipelineByOrg.value = {
      ...pipelineByOrg.value,
      [slug]: response.pipeline
    }
  }

  const replaceDocument = (slug: string, document: KnowledgeDocument) => {
    documentsByOrg.value = {
      ...documentsByOrg.value,
      [slug]: getDocuments(slug).map((item) => item.id === document.id ? document : item)
    }
  }

  const uploadDocument = async (slug: string, file: string | File) => {
    const response = await api.upload(slug, file)
    documentsByOrg.value = {
      ...documentsByOrg.value,
      [slug]: [response.document, ...getDocuments(slug)]
    }
  }

  const startAnalysis = async (slug: string, documentId: string) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.startAnalysis(slug, documentId)
      replaceDocument(slug, response.document)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Cannot start document analysis'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const stopAnalysis = async (slug: string, documentId: string) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.stopAnalysis(slug, documentId)
      replaceDocument(slug, response.document)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Cannot stop document analysis'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const loadDocumentGraph = async (slug: string, documentId: string) => {
    try {
      const response = await api.graph(slug, documentId)
      graphByDocumentId.value = {
        ...graphByDocumentId.value,
        [documentId]: response.graph
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Cannot load document graph'
    }
  }

  const loadOrganizationGraph = async (slug: string) => {
    try {
      const response = await api.organizationGraph(slug)
      graphByOrg.value = {
        ...graphByOrg.value,
        [slug]: response.graph
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Cannot load organization graph'
    }
  }

  return {
    documentsByOrg,
    pipelineByOrg,
    graphByDocumentId,
    graphByOrg,
    isLoading,
    error,
    getDocuments,
    getPipeline,
    getDocumentGraph,
    getOrganizationGraph,
    loadDocuments,
    loadPipeline,
    uploadDocument,
    startAnalysis,
    stopAnalysis,
    loadDocumentGraph,
    loadOrganizationGraph
  }
})

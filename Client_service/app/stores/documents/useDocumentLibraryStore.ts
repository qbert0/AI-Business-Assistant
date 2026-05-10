import type { KnowledgeDocument, PipelineStep } from '@/types/organization'

import { useApiDocuments } from '@/composables/api/documents/useApiDocuments'

export const useDocumentLibraryStore = defineStore('document-library', () => {
  const api = useApiDocuments()
  const documentsByOrg = ref<Record<string, KnowledgeDocument[]>>({})
  const pipelineByOrg = ref<Record<string, PipelineStep[]>>({})
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const getDocuments = (slug: string) => documentsByOrg.value[slug] ?? []
  const getPipeline = (slug: string) => pipelineByOrg.value[slug] ?? []

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

  const uploadDocument = async (slug: string, file: string | File) => {
    const response = await api.upload(slug, file)
    documentsByOrg.value = {
      ...documentsByOrg.value,
      [slug]: [response.document, ...getDocuments(slug)]
    }
  }

  return {
    documentsByOrg,
    pipelineByOrg,
    isLoading,
    error,
    getDocuments,
    getPipeline,
    loadDocuments,
    loadPipeline,
    uploadDocument
  }
})

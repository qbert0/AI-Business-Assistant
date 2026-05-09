import type { KnowledgeDocument, PipelineStep } from '@/types/organization'

export const useApiDocuments = () => {
  const apiFetch = useApiFetch()

  const list = (slug: string) => apiFetch<{ documents: KnowledgeDocument[] }>(`/api/documents/${slug}`)

  const upload = (slug: string, file: string | File) => {
    const body = typeof file === 'string'
      ? { title: file }
      : (() => {
          const formData = new FormData()
          formData.append('file', file)
          return formData
        })()

    return apiFetch<{ document: KnowledgeDocument }>(`/api/documents/${slug}`, {
      method: 'POST',
      body
    })
  }

  const pipeline = (slug: string) =>
    apiFetch<{ pipeline: PipelineStep[] }>(`/api/documents/${slug}/pipeline`)

  const preview = (slug: string, documentId: string) =>
    apiFetch<{ kind: string, content?: string | null, message?: string | null }>(
      `/api/documents/${slug}/${documentId}/preview`
    )

  return {
    list,
    upload,
    pipeline,
    preview
  }
}

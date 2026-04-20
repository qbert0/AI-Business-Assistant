import type { KnowledgeDocument, PipelineStep } from '@/types/organization'

export const useApiDocuments = () => {
  const apiFetch = useApiFetch()

  const list = (slug: string) => apiFetch<{ documents: KnowledgeDocument[] }>(`/api/documents/${slug}`)

  const upload = (slug: string, title: string) =>
    apiFetch<{ document: KnowledgeDocument }>(`/api/documents/${slug}`, {
      method: 'POST',
      body: { title }
    })

  const pipeline = (slug: string) =>
    apiFetch<{ pipeline: PipelineStep[] }>(`/api/documents/${slug}/pipeline`)

  return {
    list,
    upload,
    pipeline
  }
}

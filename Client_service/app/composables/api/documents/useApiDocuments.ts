import type { DocumentGraph, DocumentSearchResult, KnowledgeDocument, PipelineStep } from '@/types/organization'

import { useApiFetch } from '@/composables/api/core/useApiFetch'
import { getClientAuthToken } from '@/utils/auth-token'

const decodeJwtSubject = (token: string | null): string => {
  if (!token) {
    return ''
  }

  const payload = token.split('.')[1]
  if (!payload) {
    return ''
  }

  try {
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=')
    const decoded = import.meta.client ? atob(padded) : ''
    const parsed = JSON.parse(decoded) as { sub?: string }
    return parsed.sub || ''
  } catch {
    return ''
  }
}

export const useApiDocuments = () => {
  const apiFetch = useApiFetch()
  const config = useRuntimeConfig()
  const backendBaseUrl = (config.public.backendApiBaseUrl || 'http://localhost:8000').replace(/\/$/, '')

  const list = (slug: string) => apiFetch<{ documents: KnowledgeDocument[] }>(`/api/documents/${slug}`)

  const upload = async (slug: string, file: string | File) => {
    if (typeof file === 'string') {
      return apiFetch<{ document: KnowledgeDocument }>(`/api/documents/${slug}`, {
        method: 'POST',
        body: { title: file }
      })
    }

    const contentType = file.type || 'application/octet-stream'
    const presignedUpload = await apiFetch<{
      bucket: string
      object_key: string
      upload_url: string
      source_url: string
      expires_in: number
      content_type?: string | null
    }>(`/api/documents/${slug}/presign`, {
      method: 'POST',
      body: {
        fileName: file.name,
        contentType,
        expires: 3600
      }
    })

    const uploadResponse = await fetch(presignedUpload.upload_url, {
      method: 'PUT',
      headers: {
        'Content-Type': contentType
      },
      body: file
    })

    if (!uploadResponse.ok) {
      const responseText = await uploadResponse.text().catch(() => '')
      throw new Error(`Storage upload failed: ${uploadResponse.status} ${responseText || uploadResponse.statusText}`)
    }

    return apiFetch<{ document: KnowledgeDocument }>(`/api/documents/${slug}/complete`, {
      method: 'POST',
      body: {
        fileName: file.name,
        bucket: presignedUpload.bucket,
        objectKey: presignedUpload.object_key,
        sourceUrl: presignedUpload.source_url,
        contentType,
        metadata: {
          source: 'client-presigned-upload'
        }
      }
    })
  }

  const pipeline = (slug: string) =>
    apiFetch<{ pipeline: PipelineStep[] }>(`/api/documents/${slug}/pipeline`)

  const preview = (slug: string, documentId: string) =>
    apiFetch<{ kind: string, content?: string | null, message?: string | null }>(
      `/api/documents/${slug}/${documentId}/preview`
    )

  const downloadUrl = (slug: string, documentId: string) =>
    (() => {
      const token = getClientAuthToken()
      const actingUserId = decodeJwtSubject(token)

      return $fetch<{ download_url: string, expires_in: number }>(
        `${backendBaseUrl}/documents/${documentId}/download-url`,
        {
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {})
          },
          query: {
            acting_user_id: actingUserId,
            expires: 3600
          }
        }
      )
    })()

  const startAnalysis = (slug: string, documentId: string) =>
    apiFetch<{ document: KnowledgeDocument }>(`/api/documents/${slug}/${documentId}/analysis/start`, {
      method: 'POST'
    })

  const stopAnalysis = (slug: string, documentId: string) =>
    apiFetch<{ document: KnowledgeDocument }>(`/api/documents/${slug}/${documentId}/analysis/stop`, {
      method: 'POST'
    })

  const graph = (slug: string, documentId: string) =>
    apiFetch<{ graph: DocumentGraph }>(`/api/documents/${slug}/${documentId}/graph`)

  const organizationGraph = (slug: string) =>
    apiFetch<{ graph: DocumentGraph }>(`/api/documents/${slug}/graph`)

  const searchDocument = (slug: string, documentId: string, query: string, limit = 12) =>
    apiFetch<{ results: DocumentSearchResult[], count: number }>(`/api/documents/${slug}/${documentId}/search`, {
      method: 'POST',
      body: { query, limit }
    })

  const searchOrganization = (slug: string, query: string, limit = 24) =>
    apiFetch<{ results: DocumentSearchResult[], count: number }>(`/api/documents/${slug}/search`, {
      method: 'POST',
      body: { query, limit }
    })

  return {
    list,
    upload,
    pipeline,
    preview,
    downloadUrl,
    startAnalysis,
    stopAnalysis,
    graph,
    organizationGraph,
    searchDocument,
    searchOrganization
  }
}

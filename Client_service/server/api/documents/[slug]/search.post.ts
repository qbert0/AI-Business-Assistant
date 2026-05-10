import { backendFetch, getBackendUser, getRagBaseUrl } from '../../../utils/backend'

const toDocumentGroupId = (documentId: string) => `document-${documentId.replace(/[^A-Za-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '') || 'unknown-document'}`

const mapFactResult = (item: any, documentId: string, documentName: string) => ({
  id: String(item.uuid || `${documentId}-${item.name || item.fact || Math.random()}`),
  documentId,
  documentName,
  title: String(item.name || documentName || 'Fact'),
  content: String(item.fact || item.summary || item.name || ''),
  type: 'fact' as const,
  score: typeof item.score === 'number' ? item.score : null,
  sourceNodeId: item.source_node_uuid ? String(item.source_node_uuid) : null,
  targetNodeId: item.target_node_uuid ? String(item.target_node_uuid) : null
})

const mapNodeResult = (item: any, documentId: string, documentName: string) => ({
  id: String(item.uuid || `${documentId}-${item.name || Math.random()}`),
  documentId,
  documentName,
  title: String(item.name || documentName || 'Entity'),
  content: String(item.summary || item.name || ''),
  type: 'node' as const,
  score: typeof item.score === 'number' ? item.score : null,
  sourceNodeId: item.uuid ? String(item.uuid) : null,
  targetNodeId: null
})

const safeSearch = async (url: string, body: Record<string, unknown>) => {
  try {
    return await $fetch<{ results: any[] }>(url, {
      method: 'POST',
      body
    })
  } catch {
    return { results: [] }
  }
}

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  if (!orgId) {
    throw createError({ statusCode: 400, statusMessage: 'Missing organization id' })
  }

  const body = await readBody<{ query?: string, limit?: number }>(event)
  const query = String(body?.query || '').trim()
  if (!query) {
    throw createError({ statusCode: 400, statusMessage: 'Missing search query' })
  }

  const limit = Math.max(1, Math.min(Number(body?.limit || 24), 80))
  const documents = await backendFetch<any[]>(
    event,
    `/organizations/${orgId}/documents?acting_user_id=${encodeURIComponent(user.id)}&limit=500`
  )
  const indexedDocuments = documents
    .filter((document) => ['indexed', 'completed'].includes(String(document.status || '').toLowerCase()))
    .map((document) => ({
      id: String(document.id),
      name: String(document.title || document.file_name || document.id)
    }))

  if (!indexedDocuments.length) {
    return { results: [], count: 0 }
  }

  const baseUrl = getRagBaseUrl()
  const perDocumentLimit = Math.max(2, Math.ceil(limit / indexedDocuments.length))
  const batches = await Promise.all(indexedDocuments.map(async (document) => {
    const groupId = toDocumentGroupId(document.id)
    const [response, nodeResponse] = await Promise.all([
      safeSearch(`${baseUrl}/search/facts`, {
        query,
        limit: perDocumentLimit,
        group_id: groupId
      }),
      safeSearch(`${baseUrl}/search/nodes`, {
        query,
        limit: perDocumentLimit,
        group_id: groupId
      })
    ])

    return [
      ...(response.results || []).map((item) => mapFactResult(item, document.id, document.name)),
      ...(nodeResponse.results || []).map((item) => mapNodeResult(item, document.id, document.name))
    ]
  }))
  const results = batches.flat().slice(0, limit)

  return {
    results,
    count: results.length
  }
})

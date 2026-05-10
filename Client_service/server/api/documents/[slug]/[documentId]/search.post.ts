import { getRagBaseUrl } from '../../../../utils/backend'

const toDocumentGroupId = (documentId: string) => `document-${documentId.replace(/[^A-Za-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '') || 'unknown-document'}`

const mapFactResult = (item: any, documentId: string, documentName = '') => ({
  id: String(item.uuid || `${documentId}-${item.name || item.fact || Math.random()}`),
  documentId,
  documentName,
  title: String(item.name || 'Fact'),
  content: String(item.fact || item.summary || item.name || ''),
  type: 'fact' as const,
  score: typeof item.score === 'number' ? item.score : null,
  sourceNodeId: item.source_node_uuid ? String(item.source_node_uuid) : null,
  targetNodeId: item.target_node_uuid ? String(item.target_node_uuid) : null
})

const mapNodeResult = (item: any, documentId: string, documentName = '') => ({
  id: String(item.uuid || `${documentId}-${item.name || Math.random()}`),
  documentId,
  documentName,
  title: String(item.name || 'Entity'),
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
  const documentId = getRouterParam(event, 'documentId') || ''
  if (!documentId) {
    throw createError({ statusCode: 400, statusMessage: 'Missing document id' })
  }

  const body = await readBody<{ query?: string, limit?: number }>(event)
  const query = String(body?.query || '').trim()
  if (!query) {
    throw createError({ statusCode: 400, statusMessage: 'Missing search query' })
  }

  const limit = Math.max(1, Math.min(Number(body?.limit || 12), 50))
  const baseUrl = getRagBaseUrl()
  const groupId = toDocumentGroupId(documentId)
  const results = await Promise.all([
    safeSearch(`${baseUrl}/search/facts`, {
      query,
      limit,
      group_id: groupId
    }),
    safeSearch(`${baseUrl}/search/nodes`, {
      query,
      limit,
      group_id: groupId
    })
  ]).then(([response, nodeResponse]) => [
    ...(response.results || []).map((item) => mapFactResult(item, documentId)),
    ...(nodeResponse.results || []).map((item) => mapNodeResult(item, documentId))
  ].slice(0, limit)).catch(() => [])

  return {
    results,
    count: results.length
  }
})

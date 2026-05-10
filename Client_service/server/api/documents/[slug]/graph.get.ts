import { backendFetch, getBackendUser, getRagBaseUrl, mapDocumentGraph } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  if (!orgId) {
    throw createError({ statusCode: 400, statusMessage: 'Missing organization id' })
  }

  const documents = await backendFetch<any[]>(
    event,
    `/organizations/${orgId}/documents?acting_user_id=${encodeURIComponent(user.id)}&limit=100`
  )
  const documentIds = documents
    .filter((document) => ['indexed', 'completed'].includes(String(document.status || '').toLowerCase()))
    .map((document) => String(document.id))

  const baseUrl = getRagBaseUrl()
  const response = await $fetch<{ graph: any }>(`${baseUrl}/graph/documents`, {
    method: 'POST',
    body: {
      document_ids: documentIds,
      scope_id: orgId,
      limit: 220
    }
  })

  return {
    graph: mapDocumentGraph(response.graph || {})
  }
})

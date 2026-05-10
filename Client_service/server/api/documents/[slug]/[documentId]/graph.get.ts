import { getBackendUser, mapDocumentGraph } from '../../../../utils/backend'

export default defineEventHandler(async (event) => {
  await getBackendUser(event)
  const documentId = getRouterParam(event, 'documentId') || ''
  if (!documentId) {
    throw createError({ statusCode: 400, statusMessage: 'Missing document id' })
  }

  const config = useRuntimeConfig()
  const baseUrl = String(config.ragServiceBaseUrl || 'http://rag-service:8000').replace(/\/$/, '')
  const response = await $fetch<{ graph: any }>(`${baseUrl}/graph/documents/${documentId}`, {
    query: {
      limit: 80
    }
  })

  return {
    graph: mapDocumentGraph(response.graph || {})
  }
})

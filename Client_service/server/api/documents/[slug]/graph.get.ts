import { backendFetch, getBackendUser, getRagBaseUrl, mapDocumentGraph } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  const orgId = getRouterParam(event, 'slug') || ''
  if (!orgId) {
    throw createError({ statusCode: 400, statusMessage: 'Missing organization id' })
  }

  let upstreamUrl = ''
  try {
    const user = await getBackendUser(event)
    const documents = await backendFetch<any[]>(
      event,
      `/organizations/${orgId}/documents?acting_user_id=${encodeURIComponent(user.id)}&limit=100`
    )
    const documentIds = documents
      .filter((document) => ['indexed', 'completed'].includes(String(document.status || '').toLowerCase()))
      .map((document) => String(document.id))

    const baseUrl = getRagBaseUrl()
    const url = `${baseUrl}/graph/documents`
    upstreamUrl = url
    console.info(`[documents:organization-graph] forwarding to RAG ${url}`)
    const response = await $fetch<{ graph: any }>(url, {
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
  } catch (error: any) {
    console.error('[documents:organization-graph] route failed', {
      orgId,
      upstreamUrl: upstreamUrl || null,
      statusCode: error?.statusCode || error?.response?.status,
      statusMessage: error?.statusMessage || error?.response?.statusText,
      data: error?.data
    })
    throw createError({
      statusCode: error?.statusCode || error?.response?.status || 502,
      statusMessage: 'RAG organization graph request failed',
      data: {
        upstreamUrl: upstreamUrl || null,
        upstream: error?.data
      }
    })
  }
})

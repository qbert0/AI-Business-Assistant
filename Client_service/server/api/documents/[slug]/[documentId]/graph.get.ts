import { getRagBaseUrl, mapDocumentGraph } from '../../../../utils/backend'

export default defineEventHandler(async (event) => {
  const documentId = getRouterParam(event, 'documentId') || ''
  if (!documentId) {
    throw createError({ statusCode: 400, statusMessage: 'Missing document id' })
  }

  const baseUrl = getRagBaseUrl()
  const url = `${baseUrl}/graph/documents/${documentId}`
  try {
    console.info(`[documents:graph] forwarding to RAG ${url}`)
    const response = await $fetch<{ graph: any }>(url, {
      query: {
        limit: 80
      }
    })

    return {
      graph: mapDocumentGraph(response.graph || {})
    }
  } catch (error: any) {
    console.error('[documents:graph] route failed', {
      url,
      documentId,
      statusCode: error?.statusCode || error?.response?.status,
      statusMessage: error?.statusMessage || error?.response?.statusText,
      data: error?.data
    })
    throw createError({
      statusCode: error?.statusCode || error?.response?.status || 502,
      statusMessage: 'RAG document graph request failed',
      data: {
        upstreamUrl: url,
        upstream: error?.data
      }
    })
  }
})

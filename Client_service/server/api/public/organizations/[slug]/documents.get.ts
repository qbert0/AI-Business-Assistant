import { backendFetch, mapDocument } from '../../../../utils/backend'

export default defineEventHandler(async (event) => {
  const orgId = getRouterParam(event, 'slug')
  if (!orgId) {
    throw createError({ statusCode: 400, statusMessage: 'Organization id is required' })
  }

  const documents = await backendFetch<any[]>(
    event,
    `/organizations/${orgId}/public/documents?limit=100`
  )

  return {
    documents: documents.map(mapDocument)
  }
})

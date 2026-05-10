import { backendFetch } from '../../../../utils/backend'

export default defineEventHandler(async (event) => {
  const documentId = getRouterParam(event, 'documentId')
  if (!documentId) {
    throw createError({ statusCode: 400, statusMessage: 'Document id is required' })
  }

  return backendFetch(event, `/documents/${documentId}/public/preview`)
})

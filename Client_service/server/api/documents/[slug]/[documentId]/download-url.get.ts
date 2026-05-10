import { backendFetch, getBackendUser } from '../../../../utils/backend'

export default defineEventHandler(async (event) => {
  const documentId = getRouterParam(event, 'documentId') || ''

  if (!documentId) {
    throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })
  }

  const user = await getBackendUser(event)

  return backendFetch<{
    document_id: string
    file_name: string
    download_url: string
    expires_in: number
  }>(event, `/documents/${documentId}/download-url?acting_user_id=${encodeURIComponent(user.id)}&expires=3600`)
})

import { backendFetch, getBackendUser } from '../../../../utils/backend'

export default defineEventHandler(async (event) => {
  const documentId = getRouterParam(event, 'documentId') || ''

  if (!documentId) {
    throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })
  }

  const user = await getBackendUser(event)

  const downloadInfo = await backendFetch<{ download_url: string }>(
    event,
    `/documents/${documentId}/download-url?acting_user_id=${encodeURIComponent(user.id)}&expires=3600`
  )

  return sendRedirect(event, downloadInfo.download_url, 302)
})

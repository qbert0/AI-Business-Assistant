import { backendFetch, getBackendUser } from '../../../../utils/backend'

export default defineEventHandler(async (event) => {
  const documentId = getRouterParam(event, 'documentId') || ''

  if (!documentId) {
    throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })
  }

  const user = await getBackendUser(event)

  return backendFetch(
    event,
    `/documents/${documentId}/preview?acting_user_id=${encodeURIComponent(user.id)}`
  )
})

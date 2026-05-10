import { backendFetch, getBackendUser, mapDocument } from '../../../../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const documentId = getRouterParam(event, 'documentId') || ''

  const document = await backendFetch<any>(
    event,
    `/documents/${documentId}/analysis/start?acting_user_id=${encodeURIComponent(user.id)}`,
    {
      method: 'POST'
    }
  )

  return {
    document: mapDocument(document)
  }
})

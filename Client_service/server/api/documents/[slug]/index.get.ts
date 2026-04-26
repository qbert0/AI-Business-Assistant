import { backendFetch, getBackendUser, mapDocument } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const documents = await backendFetch<any[]>(
    event,
    `/organizations/${orgId}/documents?acting_user_id=${encodeURIComponent(user.id)}&limit=100`
  )

  return {
    documents: documents.map(mapDocument)
  }
})

import { backendFetch } from '../../../../../utils/backend'

export default defineEventHandler(async (event) => {
  const orgId = getRouterParam(event, 'slug') || ''
  const suggestions = await backendFetch<string[]>(
    event,
    `/organizations/${orgId}/public/chat/suggestions`
  )

  return { suggestions }
})

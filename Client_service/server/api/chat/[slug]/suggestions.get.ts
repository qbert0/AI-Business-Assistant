import { backendFetch, getBackendUser, mapSuggestions } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const suggestions = await backendFetch<string[]>(
    event,
    `/organizations/${orgId}/chat/suggestions?acting_user_id=${encodeURIComponent(user.id)}`
  )

  return {
    suggestions: mapSuggestions(suggestions),
    popularQuestions: []
  }
})

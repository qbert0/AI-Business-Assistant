import { backendFetch, getBackendUser, mapSuggestions } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const backendPath = orgId === 'personal'
    ? `/chat/personal/suggestions?acting_user_id=${encodeURIComponent(user.id)}`
    : `/organizations/${orgId}/chat/suggestions?acting_user_id=${encodeURIComponent(user.id)}`
  const suggestions = await backendFetch<string[]>(
    event,
    backendPath
  )

  return {
    suggestions: mapSuggestions(suggestions),
    popularQuestions: []
  }
})

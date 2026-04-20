import { requireAuthPayload } from '../../../utils/jwt'
import { mockPopularQuestions, mockSuggestions } from '../../../utils/mockData'

export default defineEventHandler((event) => {
  requireAuthPayload(event)
  const slug = getRouterParam(event, 'slug') || 'personal'

  return {
    suggestions: mockSuggestions[slug] ?? [],
    popularQuestions: mockPopularQuestions[slug] ?? []
  }
})

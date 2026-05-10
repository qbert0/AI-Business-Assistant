import { normalizeText } from '@/utils/text'

export const includesSearchTerm = (value: string, searchTerm: string) =>
  normalizeText(value).includes(normalizeText(searchTerm))

const splitSearchTokens = (value: string) =>
  normalizeText(value)
    .split(/\s+/)
    .map((item) => item.trim())
    .filter(Boolean)

export const scoreSearchMatch = (value: string, searchTerm: string) => {
  const haystack = normalizeText(value)
  const needle = normalizeText(searchTerm)

  if (!needle) {
    return 0
  }

  if (haystack === needle) {
    return 10_000
  }

  let score = 0

  if (haystack.startsWith(needle)) {
    score += 2_000
  }

  if (haystack.includes(needle)) {
    score += 1_000
  }

  for (const token of splitSearchTokens(needle)) {
    if (haystack.includes(token)) {
      score += 200
    }
  }

  const compactHaystack = haystack.replace(/\s+/g, '')
  const compactNeedle = needle.replace(/\s+/g, '')
  if (compactHaystack.includes(compactNeedle)) {
    score += 500
  }

  return score
}

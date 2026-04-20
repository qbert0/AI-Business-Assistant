import { normalizeText } from '@/utils/text'

export const includesSearchTerm = (value: string, searchTerm: string) =>
  normalizeText(value).includes(normalizeText(searchTerm))

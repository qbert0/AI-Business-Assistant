export const normalizeText = (value: string) => value.trim().toLowerCase()

export const createSlug = (value: string) =>
  normalizeText(value)
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')

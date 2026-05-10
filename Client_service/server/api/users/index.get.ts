import { backendFetch, getBackendUser } from '../../utils/backend'

interface BackendUser {
  id: string
  email: string
  full_name: string
}

export default defineEventHandler(async (event) => {
  await getBackendUser(event)
  const search = getQuery(event).search
  const normalizedSearch = typeof search === 'string' ? search.trim() : ''

  if (!normalizedSearch) {
    return { users: [] }
  }

  const users = await backendFetch<BackendUser[]>(
    event,
    `/users?search=${encodeURIComponent(normalizedSearch)}&limit=20`
  )

  return {
    users: users.map((user) => ({
      id: user.id,
      name: user.full_name,
      email: user.email
    }))
  }
})

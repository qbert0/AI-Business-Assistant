import { getBackendUser, mapUser } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  try {
    const user = await getBackendUser(event)

    return {
      user: mapUser(user)
    }
  } catch {
    throw createError({
      statusCode: 401,
      statusMessage: 'Authentication required'
    })
  }
})

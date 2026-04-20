import { requireAuthPayload } from '../../utils/jwt'
import { findUserById, stripPassword } from '../../utils/mockData'

export default defineEventHandler((event) => {
  const payload = requireAuthPayload(event)
  const user = findUserById(payload.sub)

  if (!user) {
    throw createError({ statusCode: 401, statusMessage: 'User not found' })
  }

  return {
    user: stripPassword(user)
  }
})

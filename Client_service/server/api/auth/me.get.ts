import { getBackendUser, mapUser } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)

  return {
    user: mapUser(user)
  }
})

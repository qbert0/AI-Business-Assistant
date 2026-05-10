import { backendFetch } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  const notificationId = String(getRouterParam(event, 'id') || '')
  const notification = await backendFetch<any>(
    event,
    `/notifications/${encodeURIComponent(notificationId)}/read`,
    { method: 'PATCH' }
  )

  return {
    notification
  }
})

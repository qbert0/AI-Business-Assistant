import { backendFetch, getBackendUser } from '../../utils/backend'

interface BackendNotification {
  id: string
  title: string
  content?: string | null
  action_url?: string | null
  notification_type: string
  is_read: boolean
}

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const notifications = await backendFetch<BackendNotification[]>(
    event,
    `/users/${encodeURIComponent(user.id)}/notifications`
  )

  return {
    notifications: notifications.map((notification) => ({
      id: notification.id,
      title: notification.title,
      description: notification.content || '',
      to: notification.action_url || '/notifications',
      tone: notification.notification_type === 'organization' ? 'info' : 'success'
    }))
  }
})

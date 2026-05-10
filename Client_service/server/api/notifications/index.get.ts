import { backendFetch, getBackendUser } from '../../utils/backend'

interface BackendNotification {
  id: string
  title: string
  content?: string | null
  action_url?: string | null
  notification_type: string
  is_read: boolean
  organization_id?: string | null
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
      tone: notification.notification_type === 'organization'
        ? (notification.is_read ? 'success' : 'warning')
        : 'success',
      isRead: notification.is_read,
      organizationId: notification.organization_id || null,
      actionType: notification.notification_type === 'organization' && !notification.is_read
        ? 'organization_invitation'
        : undefined
    }))
  }
})

import { APP_ROUTES, getOrganizationRoute } from '@/constants/navigation'
import type { AppNotificationItem } from '@/types/notification'
import { hasClientAuthToken } from '@/utils/auth-token'

export const useAppNotifications = () => {
  const { text } = useAppLocale()
  const apiFetch = useApiFetch()
  const items = useState<AppNotificationItem[]>('app-notifications', () => [])
  const isLoaded = useState<boolean>('app-notifications-loaded', () => false)

  const fallbackNotifications = computed<AppNotificationItem[]>(() => [
    {
      id: 'document-indexed',
      title: text.notifications.documentIndexedTitle,
      description: text.notifications.documentIndexedDescription,
      to: getOrganizationRoute('acme-holdings', 'documents'),
      tone: 'info'
    },
    {
      id: 'join-approved',
      title: text.notifications.joinApprovedTitle,
      description: text.notifications.joinApprovedDescription,
      to: APP_ROUTES.organizations,
      tone: 'success'
    }
  ])

  const loadNotifications = async () => {
    if (!hasClientAuthToken()) {
      items.value = []
      return
    }

    const response = await apiFetch<{ notifications: AppNotificationItem[] }>('/api/notifications')
    items.value = response.notifications
    isLoaded.value = true
  }

  if (import.meta.client && !isLoaded.value) {
    void loadNotifications()
  }

  const notifications = computed<AppNotificationItem[]>(() =>
    isLoaded.value ? items.value : fallbackNotifications.value
  )

  const notificationSummary = computed(() => notifications.value.slice(0, 3))

  return {
    notifications,
    notificationSummary,
    loadNotifications
  }
}

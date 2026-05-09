import { APP_ROUTES, getOrganizationRoute } from '@/constants/navigation'
import type { AppNotificationItem } from '@/types/notification'

export const useAppNotifications = () => {
  const { text } = useAppLocale()

  const notifications = computed<AppNotificationItem[]>(() => [
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

  const notificationSummary = computed(() => notifications.value.slice(0, 3))

  return {
    notifications,
    notificationSummary
  }
}


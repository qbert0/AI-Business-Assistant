import { useAppLocale } from '@/composables/system/useAppLocale'

export const useAppNotifications = () => {
  const { text } = useAppLocale()

  const notifications = computed(() => [
    {
      id: 'document-indexed',
      title: text.notifications.documentIndexedTitle,
      description: text.notifications.documentIndexedDescription,
      to: '/org/acme/documents'
    },
    {
      id: 'join-approved',
      title: text.notifications.joinApprovedTitle,
      description: text.notifications.joinApprovedDescription,
      to: '/workspace/requests'
    }
  ])

  const notificationSummary = computed(() => `${notifications.value.length}`)

  return {
    notifications,
    notificationSummary
  }
}

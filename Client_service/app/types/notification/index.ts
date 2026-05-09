export interface AppNotificationItem {
  id: string
  title: string
  description: string
  to: string
  tone: 'info' | 'success' | 'warning'
}


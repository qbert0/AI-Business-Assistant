export interface AppNotificationItem {
  id: string
  title: string
  description: string
  to: string
  tone: 'info' | 'success' | 'warning'
  isRead?: boolean
  organizationId?: string | null
  actionType?: 'organization_invitation'
}


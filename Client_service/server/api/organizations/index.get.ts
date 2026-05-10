import { backendFetch, getBackendUser, mapOrganization } from '../../utils/backend'
import type { OrganizationPermission } from '../../../app/constants/rbac'

interface BackendOrganization {
  id: string
  name: string
  industry?: string | null
  description?: string | null
  billing_status?: string | null
  settings?: {
    identity_keywords?: string[]
  }
}

interface BackendDashboard {
  employee_count: number
  document_count: number
  chat_session_count: number
}

interface BackendMember {
  user_id: string
  role: string
  permissions: OrganizationPermission[]
}

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const backendOrganizations = await backendFetch<BackendOrganization[]>(
    event,
    `/organizations?user_id=${encodeURIComponent(user.id)}&limit=100`
  )

  const organizations = await Promise.all(backendOrganizations.map(async (organization) => {
    let role: 'admin' | 'user' = 'user'
    let counts = {}

    try {
      const dashboard = await backendFetch<BackendDashboard>(
        event,
        `/organizations/${organization.id}/dashboard?acting_user_id=${encodeURIComponent(user.id)}`
      )
      counts = {
        employeesCount: dashboard.employee_count,
        documentsCount: dashboard.document_count,
        visits: dashboard.chat_session_count
      }
    } catch {
      // Keep the organization list usable even when dashboard permissions/data are incomplete.
    }

    try {
      const members = await backendFetch<BackendMember[]>(
        event,
        `/organizations/${organization.id}/members?acting_user_id=${encodeURIComponent(user.id)}&limit=100`
      )
      role = members.find((member) => member.user_id === user.id)?.role === 'admin' ? 'admin' : role
    } catch {
      // Non-admin users may not have view_employees; their organization role stays user.
    }

    return mapOrganization(organization, role, counts)
  }))

  return {
    organizations,
    joinRequests: []
  }
})

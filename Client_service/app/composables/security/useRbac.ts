import type { OrganizationPermission } from '@/constants/rbac'

const SEGMENT_PERMISSION_MAP: Record<string, OrganizationPermission | null> = {
  dashboard: null,
  workspace: 'chat_advisory',
  employees: 'view_employees',
  documents: 'read_documents',
  analytics: 'view_analytics',
  chat: 'chat_advisory',
  settings: 'access_org_settings',
  pipeline: 'upload_documents'
}

const parseOrganizationRoute = (path: string) => {
  const parts = path.split('/').filter(Boolean)
  const root = parts[0]

  if (root !== 'org') {
    return null
  }

  const slug = parts[1]
  const segment = parts[2] || 'dashboard'

  if (!slug || slug === 'create') {
    return null
  }

  return { slug, segment }
}

export const useRbac = () => {
  const auth = useAuthStore()
  const organizations = useOrganizationStore()

  const resolveRouteAccess = async (path: string) => {
    const route = parseOrganizationRoute(path)
    if (!route) {
      return { allowed: true, reason: null as string | null }
    }

    if (!organizations.organizations.length) {
      await organizations.loadOrganizations()
    }

    const organization = organizations.getOrganizationBySlug(route.slug)
    if (!organization) {
      return { allowed: false, reason: 'organization-not-found' }
    }

    if (organization.role === 'admin') {
      return { allowed: true, reason: null }
    }

    const requiredPermission = SEGMENT_PERMISSION_MAP[route.segment]
    if (!requiredPermission) {
      return { allowed: true, reason: null }
    }

    if (!organizations.getMembers(route.slug).length) {
      await organizations.loadMembers(route.slug)
    }

    const currentMember = organizations
      .getMembers(route.slug)
      .find((member) => member.email === auth.user?.email)

    if (!currentMember?.permissions.includes(requiredPermission)) {
      return { allowed: false, reason: 'missing-permission' }
    }

    return { allowed: true, reason: null }
  }

  const can = (slug: string, permission: OrganizationPermission) => {
    const organization = organizations.getOrganizationBySlug(slug)
    if (organization?.role === 'admin') {
      return true
    }

    return organizations
      .getMembers(slug)
      .some((member) => member.email === auth.user?.email && member.permissions.includes(permission))
  }

  return {
    resolveRouteAccess,
    can
  }
}

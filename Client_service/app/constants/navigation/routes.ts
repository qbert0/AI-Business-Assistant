import type { OrganizationPermission } from '@/constants/rbac'
import type { AppMessages } from '@/locales'

export interface NavigationItem {
  label: string
  icon: string
  to: string
}

export const APP_ROUTES = {
  home: '/',
  dashboard: '/dashboard',
  legacyWorkspace: '/workspace',
  organizations: '/org',
  organizationSearch: '/org/search',
  organizationCreate: '/org/create',
  profile: '/profile',
  settings: '/setting',
  settingProfile: '/setting/profile',
  settingPayment: '/setting/payment',
  settingOrganize: '/setting/organize',
  settingAuthen: '/setting/authen',
  notifications: '/notifications',
  authLogin: '/auth/login',
  authRegister: '/auth/register',
  authGoogleCallback: '/auth/google/callback'
} as const

export const ORGANIZATION_ROUTE_SEGMENTS = {
  dashboard: 'dashboard',
  workspace: 'workspace',
  employees: 'employees',
  documents: 'documents',
  pipeline: 'pipeline',
  analytics: 'analytics',
  chat: 'chat',
  settings: 'settings'
} as const

export type OrganizationRouteSegment = keyof typeof ORGANIZATION_ROUTE_SEGMENTS

export const getOrganizationRoute = (slug: string, segment: OrganizationRouteSegment = 'dashboard') =>
  `${APP_ROUTES.organizations}/${slug}/${ORGANIZATION_ROUTE_SEGMENTS[segment]}`

export const getOrganizationPublicRoute = (slug: string) => `${APP_ROUTES.organizations}/${slug}/public`

export const getContextChatRoute = (slug: string, sessionId?: string | null) => {
  if (slug === 'personal') {
    return sessionId ? `${APP_ROUTES.dashboard}/chat/${sessionId}` : APP_ROUTES.dashboard
  }

  const workspaceRoute = getOrganizationRoute(slug, 'workspace')
  return sessionId ? `${workspaceRoute}/chat/${sessionId}` : workspaceRoute
}

export const getAppNavigation = (text: AppMessages): NavigationItem[] => [
  {
    label: text.navigation.home,
    icon: 'lucide:house',
    to: APP_ROUTES.dashboard
  },
  {
    label: text.navigation.organizations,
    icon: 'lucide:building-2',
    to: APP_ROUTES.organizations
  }
]

export const getSettingNavigation = (text: AppMessages): NavigationItem[] => [
  {
    label: text.settingsNavigation.profile,
    icon: 'lucide:user-round',
    to: APP_ROUTES.settingProfile
  },
  {
    label: text.settingsNavigation.payment,
    icon: 'lucide:credit-card',
    to: APP_ROUTES.settingPayment
  },
  {
    label: text.settingsNavigation.organize,
    icon: 'lucide:layout-grid',
    to: APP_ROUTES.settingOrganize
  },
  {
    label: text.settingsNavigation.authen,
    icon: 'lucide:shield-check',
    to: APP_ROUTES.settingAuthen
  }
]

export const getOrganizationNavigation = (text: AppMessages): Array<{
  label: string
  permission: OrganizationPermission | null
  to: (slug: string) => string
}> => [
  { label: text.common.overview, permission: null, to: (slug: string) => getOrganizationRoute(slug, 'dashboard') },
  { label: text.common.employees, permission: 'view_employees', to: (slug: string) => getOrganizationRoute(slug, 'employees') },
  { label: text.common.documents, permission: 'read_documents', to: (slug: string) => getOrganizationRoute(slug, 'documents') },
  { label: text.common.analytics, permission: 'view_analytics', to: (slug: string) => getOrganizationRoute(slug, 'analytics') },
  { label: text.common.settings, permission: 'access_org_settings', to: (slug: string) => getOrganizationRoute(slug, 'settings') }
]

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

export const getContextChatRoute = (slug: string) =>
  slug === 'personal' ? APP_ROUTES.dashboard : getOrganizationRoute(slug, 'workspace')

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

export const getOrganizationNavigation = (text: AppMessages) => [
  { label: text.common.overview, to: (slug: string) => getOrganizationRoute(slug, 'dashboard') },
  { label: text.navigation.workspace, to: (slug: string) => getOrganizationRoute(slug, 'workspace') },
  { label: text.common.employees, to: (slug: string) => getOrganizationRoute(slug, 'employees') },
  { label: text.common.documents, to: (slug: string) => getOrganizationRoute(slug, 'documents') },
  { label: text.common.pipeline, to: (slug: string) => getOrganizationRoute(slug, 'pipeline') },
  { label: text.common.analytics, to: (slug: string) => getOrganizationRoute(slug, 'analytics') },
  { label: text.common.settings, to: (slug: string) => getOrganizationRoute(slug, 'settings') }
]

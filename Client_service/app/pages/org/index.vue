<template>
  <main class="org-hub-page">
    <AppPanel class="org-hub-container">
      <template #header-left>
        <h1 class="page-title">{{ text.organizations.title }}</h1>
      </template>

      <template #header-right>
        <NuxtLink class="btn-primary" :to="APP_ROUTES.organizationCreate">
          <Icon name="lucide:plus" />
          {{ text.organizations.create }}
        </NuxtLink>
      </template>
    </AppPanel>

    <section class="org-hub-toolbar org-hub-container">
      <div class="org-filter-search">
        <Icon name="lucide:search" />
        <input v-model="localSearch" :placeholder="text.organizations.searchPlaceholder" />
      </div>

      <div class="org-filter-tabs" :aria-label="text.organizations.filterLabel">
        <button
          v-for="option in filterOptions"
          :key="option.value"
          type="button"
          :class="['org-filter-tab', activeFilter === option.value && 'active']"
          @click="activeFilter = option.value"
        >
          <span>{{ option.label }}</span>
          <strong>{{ option.count }}</strong>
        </button>
      </div>
    </section>

    <div class="org-hub-grid org-hub-container">
      <AppPanel>
        <template #header-left>
          <h2 class="panel-title">{{ text.organizations.listTitle }}</h2>
        </template>

        <template #header-right>
          <span class="text-caption text-stone">{{ filteredOrganizations.length }} {{ text.organizations.resultUnit }}</span>
        </template>

        <template #content>
          <div class="org-list">
            <article v-for="organization in filteredOrganizations" :key="organization.id" class="org-row">
              <div class="org-row-main">
                <div class="org-logo-mark">{{ getInitials(organization.name) }}</div>
                <div class="min-w-0">
                  <div class="org-row-title">
                    <h3>{{ organization.name }}</h3>
                    <span :class="organization.status === 'pending' ? 'status-badge status-warning' : 'status-badge status-info'">
                      {{ organization.status === 'pending' ? text.common.pending : roleLabel(organization.role) }}
                    </span>
                  </div>
                  <p>{{ organization.industry }}</p>
                </div>
              </div>

              <div class="org-row-actions">
                <NuxtLink class="btn-secondary" :to="getOrganizationRoute(organization.slug, 'dashboard')">
                  {{ text.organizations.enterWorkspace }}
                </NuxtLink>
                <NuxtLink
                  v-if="organization.role === 'admin'"
                  class="btn-secondary"
                  :to="getOrganizationRoute(organization.slug, 'employees')"
                >
                  {{ text.common.employees }}
                </NuxtLink>
                <NuxtLink class="btn-secondary" :to="getOrganizationPublicRoute(organization.slug)">
                  {{ text.organizationPublic.openPublicPage }}
                </NuxtLink>
                <NuxtLink class="btn-dark" :to="getOrganizationRoute(organization.slug, 'workspace')">{{ text.navigation.workspace }}</NuxtLink>
              </div>
            </article>
          </div>

          <p v-if="!filteredOrganizations.length" class="table-copy">{{ UI_MESSAGES.emptyOrganizations }}</p>
        </template>
      </AppPanel>

      <aside class="org-request-panel">
        <AppPanel>
          <template #header-left>
            <h2 class="panel-title">{{ text.organizations.notificationSummaryTitle }}</h2>
          </template>

          <template #header-right>
            <NuxtLink class="panel-link" :to="APP_ROUTES.notifications">
              {{ text.organizations.viewAllNotifications }}
            </NuxtLink>
          </template>

          <template #content>
            <div class="space-y-2">
              <NuxtLink v-for="notification in notificationSummary" :key="notification.id" :to="notification.to" class="org-request-row">
                <div class="min-w-0">
                  <h3>{{ notification.title }}</h3>
                  <p>{{ notification.description }}</p>
                </div>
                <span :class="['status-badge', getNotificationStatusClass(notification.tone)]">
                  {{ getNotificationStatusLabel(notification.tone) }}
                </span>
              </NuxtLink>

              <p v-if="!notificationSummary.length" class="table-copy">{{ text.organizations.emptyNotifications }}</p>
            </div>
          </template>
        </AppPanel>
      </aside>
    </div>
  </main>
</template>

<script setup lang="ts">
import { UI_MESSAGES } from '@/constants/messages'
import { APP_ROUTES, getOrganizationPublicRoute, getOrganizationRoute } from '@/constants/navigation'
import type { OrganizationSummary } from '@/types/organization'
import type { AppNotificationItem } from '@/types/notification'

definePageMeta({
  layout: 'org'
})

type OrganizationFilter = 'all' | 'admin' | 'user' | 'pending'

const { text } = useAppLocale()

const route = useRoute()
const { searchOrganizations } = useOrganization()
const { notificationSummary } = useAppNotifications()

const activeFilter = ref<OrganizationFilter>('all')
const localSearch = ref(typeof route.query.q === 'string' ? route.query.q : '')

const searchedOrganizations = computed(() => searchOrganizations(localSearch.value))
const filteredOrganizations = computed(() =>
  searchedOrganizations.value.filter((organization: OrganizationSummary) => {
    if (activeFilter.value === 'all') return true
    if (activeFilter.value === 'pending') return organization.status === 'pending'
    return organization.role === activeFilter.value
  })
)

const getCount = (filter: OrganizationFilter) => {
  if (filter === 'all') return searchedOrganizations.value.length
  if (filter === 'pending') return searchedOrganizations.value.filter((organization: OrganizationSummary) => organization.status === 'pending').length
  return searchedOrganizations.value.filter((organization: OrganizationSummary) => organization.role === filter).length
}

const filterOptions = computed(() => [
  { value: 'all' as const, label: text.organizations.allFilter, count: getCount('all') },
  { value: 'admin' as const, label: text.common.admin, count: getCount('admin') },
  { value: 'user' as const, label: text.common.employee, count: getCount('user') },
  { value: 'pending' as const, label: text.common.pending, count: getCount('pending') }
])

const getInitials = (name: string) =>
  name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()

const roleLabel = (role: OrganizationSummary['role']) => (role === 'admin' ? text.common.admin : text.organizations.employeeStatus)

const getNotificationStatusClass = (tone: AppNotificationItem['tone']) => {
  if (tone === 'success') return 'status-success'
  if (tone === 'warning') return 'status-warning'
  return 'status-info'
}

const getNotificationStatusLabel = (tone: AppNotificationItem['tone']) => {
  if (tone === 'success') return text.common.approved
  if (tone === 'warning') return text.common.pending
  return text.common.notifications
}
</script>

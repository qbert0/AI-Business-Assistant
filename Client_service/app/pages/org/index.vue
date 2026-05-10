<template>
  <main class="org-hub-page">
    <section class="org-hub-hero org-hub-container">
      <div class="min-w-0">
        <p class="eyebrow">{{ text.organizations.eyebrow }}</p>
        <h1 class="page-title">{{ text.organizations.title }}</h1>
        <p class="org-hub-hero-copy">{{ text.organizations.description }}</p>
      </div>

      <div class="org-hub-hero-actions">
        <NuxtLink class="btn-primary" :to="APP_ROUTES.organizationCreate">
          <Icon name="lucide:plus" />
          {{ text.organizations.create }}
        </NuxtLink>
      </div>
    </section>

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
                  <div class="org-row-metrics">
                    <span>{{ organization.employeeCount }} {{ text.common.employees }}</span>
                    <span>{{ organization.documentCount }} {{ text.common.documents }}</span>
                    <span>{{ organization.visits }} {{ text.organizations.visits }}</span>
                  </div>
                </div>
              </div>

              <div class="org-row-actions">
                <NuxtLink
                  v-if="organization.status === 'active'"
                  class="btn-primary"
                  :to="getOrganizationRoute(organization.slug, 'dashboard')"
                >
                  {{ text.organizations.enterWorkspace }}
                </NuxtLink>
                <button v-else class="btn-secondary" type="button" disabled>
                  {{ text.common.pending }}
                </button>
                <AppPopup root-class="relative" content-class="org-row-action-menu" match-trigger-position teleport>
                  <template #trigger="{ toggle }">
                    <button class="icon-action-light" type="button" :aria-label="text.organizations.actions" @click="toggle">
                      <Icon name="lucide:more-horizontal" />
                    </button>
                  </template>

                  <template #default="{ close }">
                    <NuxtLink class="org-row-menu-item" :to="getOrganizationPublicRoute(organization.slug)" @click="close">
                      <Icon name="lucide:globe-2" />
                      <span>{{ text.organizationPublic.openPublicPage }}</span>
                    </NuxtLink>
                    <NuxtLink
                      v-if="canManageOrganization(organization)"
                      class="org-row-menu-item"
                      :to="getOrganizationRoute(organization.slug, 'employees')"
                      @click="close"
                    >
                      <Icon name="lucide:users" />
                      <span>{{ text.common.employees }}</span>
                    </NuxtLink>
                    <NuxtLink
                      v-if="canManageOrganization(organization)"
                      class="org-row-menu-item"
                      :to="getOrganizationRoute(organization.slug, 'settings')"
                      @click="close"
                    >
                      <Icon name="lucide:settings" />
                      <span>{{ text.common.settings }}</span>
                    </NuxtLink>
                    <button
                      v-if="canLeaveOrganization(organization)"
                      class="org-row-menu-item danger"
                      type="button"
                      :disabled="leavingSlug === organization.slug"
                      @click="handleLeaveOrganization(organization, close)"
                    >
                      <Icon name="lucide:log-out" />
                      <span>{{ leavingSlug === organization.slug ? text.organizations.leaving : text.organizations.leave }}</span>
                    </button>
                  </template>
                </AppPopup>
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
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
import { useAppNotifications } from '@/composables/system/useAppNotifications'
import { UI_MESSAGES } from '@/constants/messages'
import { APP_ROUTES, getOrganizationPublicRoute, getOrganizationRoute } from '@/constants/navigation'
import type { OrganizationSummary } from '@/types/organization'
import type { AppNotificationItem } from '@/types/notification'

definePageMeta({
  layout: 'org',
  orgFullBleed: true
})

type OrganizationFilter = 'all' | 'admin' | 'user' | 'pending'

const { text } = useAppLocale()

const route = useRoute()
const { searchOrganizations, leaveOrganization } = useOrganization()
const { notificationSummary } = useAppNotifications()

const activeFilter = ref<OrganizationFilter>('all')
const localSearch = ref(typeof route.query.q === 'string' ? route.query.q : '')
const leavingSlug = ref<string | null>(null)

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

const canManageOrganization = (organization: OrganizationSummary) => organization.role === 'admin' && organization.status === 'active'

const canLeaveOrganization = (organization: OrganizationSummary) => organization.role !== 'admin' && organization.status === 'active'

const handleLeaveOrganization = async (organization: OrganizationSummary, close: () => void) => {
  close()
  if (!window.confirm(text.organizations.leaveConfirm.replace('{name}', organization.name))) {
    return
  }

  leavingSlug.value = organization.slug
  try {
    await leaveOrganization(organization.slug)
  } finally {
    leavingSlug.value = null
  }
}

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

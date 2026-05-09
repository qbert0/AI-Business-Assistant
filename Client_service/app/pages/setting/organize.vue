<template>
  <!--
    Layout page:
    - Khối 1: heading
    - Khối 2: chọn workspace mặc định
    - Khối 3: danh sách tổ chức để truy cập nhanh
  -->
  <div class="settings-content">
    <!-- Block 1: page heading -->
    <section class="settings-page-heading">
      <p class="eyebrow">{{ text.settingsNavigation.organize }}</p>
      <h1 class="page-title">{{ text.settingsOrganize.title }}</h1>
      <p class="muted-copy">{{ text.settingsOrganize.description }}</p>
    </section>

    <!-- Block 2: default workspace selector -->
    <section class="settings-panel">
      <div class="settings-panel-heading">
        <div>
          <p class="section-kicker">{{ text.settingsOrganize.defaultContextEyebrow }}</p>
          <h2 class="panel-title">{{ text.settingsOrganize.defaultWorkspace }}</h2>
        </div>
        <NuxtLink v-if="selectedOrganization" class="btn-dark" :to="getContextChatRoute(form.defaultWorkspace)">
          {{ text.settingsOrganize.openDefaultWorkspace }}
        </NuxtLink>
      </div>

      <select v-model="form.defaultWorkspace" class="app-select" @change="saveOrganize">
        <option value="personal">{{ text.settingsOrganize.personalWorkspace }}</option>
        <option v-for="organization in organizations" :key="organization.id" :value="organization.slug">{{ organization.name }}</option>
      </select>

      <p class="table-copy">{{ defaultContextDescription }}</p>
      <p v-if="organizeErrors" class="text-caption text-orange">{{ organizeErrors }}</p>
    </section>

    <!-- Block 3: quick access organization list -->
    <section class="settings-panel">
      <div class="settings-panel-heading">
        <div>
          <p class="section-kicker">{{ text.settingsOrganize.quickAccessEyebrow }}</p>
          <h2 class="panel-title">{{ text.settingsOrganize.organizationAccess }}</h2>
        </div>
        <NuxtLink class="btn-secondary" :to="APP_ROUTES.organizations">{{ text.settingsOrganize.manageOrganizations }}</NuxtLink>
      </div>

      <div class="settings-org-list">
        <article v-for="organization in organizations" :key="organization.id" class="settings-org-row">
          <div class="min-w-0">
            <h3>{{ organization.name }}</h3>
            <p>{{ organization.industry }}</p>
          </div>
          <div class="settings-org-actions">
            <span :class="organization.role === 'admin' ? 'status-badge status-success' : 'status-badge status-info'">
              {{ organization.role === 'admin' ? text.common.admin : text.organizations.employeeStatus }}
            </span>
            <NuxtLink
              class="icon-action-light"
              :to="getOrganizationRoute(organization.slug, 'dashboard')"
              :aria-label="text.settingsOrganize.openOrganization"
              :title="text.settingsOrganize.openOrganization"
            >
              <Icon name="lucide:log-in" />
            </NuxtLink>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { APP_ROUTES, getContextChatRoute, getOrganizationRoute } from '@/constants/navigation'
import type { OrganizationSummary } from '@/types/organization'

definePageMeta({
  layout: 'settings'
})

const { text } = useAppLocale()
const { organizations } = useOrganization()
const { organizeErrors, validateOrganize } = useSettingsForms()

const form = reactive({
  defaultWorkspace: 'personal'
})

const selectedOrganization = computed(() =>
  organizations.value.find((organization: OrganizationSummary) => organization.slug === form.defaultWorkspace)
)

const defaultContextDescription = computed(() =>
  selectedOrganization.value
    ? text.settingsOrganize.defaultOrganizationHint.replace('{name}', selectedOrganization.value.name)
    : text.settingsOrganize.personalWorkspaceHint
)

const saveOrganize = () => {
  validateOrganize(form)
}

/*
Layout map

+---------------------------------------------------+
| Heading                                           |
|---------------------------------------------------|
| Default workspace selector + open workspace CTA   |
|---------------------------------------------------|
| Organization quick access list                    |
| org row | role badge | open action                |
+---------------------------------------------------+
*/
</script>

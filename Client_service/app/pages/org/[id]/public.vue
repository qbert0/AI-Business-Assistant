<template>
  <main class="org-content-page">
    <AppPanel v-if="organization">
      <template #header-left>
        <div>
          <p class="eyebrow">{{ text.organizationPublic.eyebrow }}</p>
          <h1 class="page-title">{{ organization.name }}</h1>
        </div>
      </template>

      <template #header-right>
        <span class="status-badge status-info">{{ organization.industry }}</span>
      </template>

      <div class="space-y-4">
        <p class="muted-copy">{{ organization.description }}</p>

        <div class="grid gap-2 sm:grid-cols-3">
          <div class="rounded-xl bg-white p-3">
            <p class="text-caption text-stone">{{ text.common.employees }}</p>
            <strong class="text-xl">{{ organization.employeesCount }}</strong>
          </div>
          <div class="rounded-xl bg-white p-3">
            <p class="text-caption text-stone">{{ text.common.documents }}</p>
            <strong class="text-xl">{{ organization.documentsCount }}</strong>
          </div>
          <div class="rounded-xl bg-white p-3">
            <p class="text-caption text-stone">{{ text.organizations.visits }}</p>
            <strong class="text-xl">{{ organization.visits }}</strong>
          </div>
        </div>
      </div>
    </AppPanel>

    <AppPanel v-if="organization">
      <template #header-left>
        <h2 class="panel-title">{{ text.organizationPublic.joinTitle }}</h2>
      </template>

      <div v-if="allowJoinRequests" class="space-y-3">
        <p class="table-copy">{{ text.organizationPublic.joinDescription }}</p>
        <textarea v-model="note" class="app-textarea" rows="4" :placeholder="text.organizationPublic.notePlaceholder" />
        <button v-if="isAuthenticated" class="btn-primary" @click="submitJoinRequest">{{ text.organizationPublic.submit }}</button>
        <NuxtLink v-else class="btn-primary" :to="APP_ROUTES.authLogin">{{ text.organizationPublic.loginToRequest }}</NuxtLink>
      </div>

      <p v-else class="table-copy">{{ text.organizationPublic.joinDisabled }}</p>
    </AppPanel>
  </main>
</template>

<script setup lang="ts">
import { useAuth } from '@/composables/auth/useAuth'
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
import { APP_ROUTES } from '@/constants/navigation'
import type { OrganizationSummary } from '@/types/organization'

definePageMeta({
  layout: 'org',
  orgFullBleed: true
})

const route = useRoute()
const { text } = useAppLocale()
const { isAuthenticated } = useAuth()
const { requestJoinOrganization } = useOrganization()

const note = ref('')
const slug = computed(() => route.params.id as string)

const { data } = await useFetch<{ organization: OrganizationSummary, allowJoinRequests: boolean }>(
  () => `/api/public/organizations/${slug.value}`
)

const organization = computed(() => data.value?.organization)
const allowJoinRequests = computed(() => data.value?.allowJoinRequests ?? false)

const submitJoinRequest = async () => {
  if (!organization.value) {
    return
  }

  await requestJoinOrganization(organization.value.name, note.value)
  note.value = ''
  await navigateTo(APP_ROUTES.organizations)
}
</script>

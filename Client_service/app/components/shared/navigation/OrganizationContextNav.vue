<template>
  <div v-if="slug" class="context-nav">
    <div v-if="displayOrganization" class="context-organization-label">
      <span>{{ text.drawer.organizationLabel }}</span>
      <strong>{{ displayOrganization.name }}</strong>
    </div>

    <NuxtLink
      v-for="item in organizationNavigation"
      :key="item.label"
      :to="item.to(slug)"
      class="context-link"
    >
      {{ item.label }}
    </NuxtLink>
  </div>
</template>

<script setup lang="ts">
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
import { getOrganizationNavigation, getOrganizationRoute } from '@/constants/navigation'
import type { OrganizationSummary } from '@/types/organization'

const { text } = useAppLocale()
const { user } = useAuth()
const { getOrganizationBySlug, getMembers, loadMembers } = useOrganization()

const props = defineProps<{
  slug?: string
}>()

const publicOrganization = ref<OrganizationSummary | null>(null)
const allowGuestDocumentAccess = ref(false)
const organization = computed(() => (props.slug ? getOrganizationBySlug(props.slug) : undefined))
const displayOrganization = computed(() => organization.value ?? publicOrganization.value)
const currentMember = computed(() =>
  props.slug
    ? getMembers(props.slug).find((member) => member.email === user.value.email)
    : undefined
)
const organizationNavigation = computed(() => {
  if (!organization.value) {
    return [
      { label: text.common.overview, to: (slug: string) => getOrganizationRoute(slug, 'dashboard') },
      ...(allowGuestDocumentAccess.value
        ? [{ label: text.common.documents, to: (slug: string) => getOrganizationRoute(slug, 'documents') }]
        : []),
      { label: text.organizationPublic.guestChatTitle, to: (slug: string) => getOrganizationRoute(slug, 'chat') }
    ]
  }

  return getOrganizationNavigation(text).filter((item) => {
    if (!item.permission || organization.value?.role === 'admin') {
      return true
    }
    return currentMember.value?.permissions.includes(item.permission)
  })
})

watch(
  () => props.slug,
  async (slug) => {
    if (slug && organization.value && organization.value.role !== 'admin' && !getMembers(slug).length) {
      await loadMembers(slug)
    }
    if (slug && !organization.value) {
      try {
        const response = await $fetch<{ organization: OrganizationSummary, allowGuestDocumentAccess: boolean }>(`/api/public/organizations/${slug}`)
        publicOrganization.value = response.organization
        allowGuestDocumentAccess.value = response.allowGuestDocumentAccess
      } catch {
        publicOrganization.value = null
        allowGuestDocumentAccess.value = false
      }
    } else {
      publicOrganization.value = null
      allowGuestDocumentAccess.value = false
    }
  },
  { immediate: true }
)
</script>

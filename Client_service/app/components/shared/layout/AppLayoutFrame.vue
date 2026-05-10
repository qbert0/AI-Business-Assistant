<template>
  <div class="flex min-h-screen flex-col bg-parchment">
    <AppHeader />
    <div class="flex min-h-0 flex-1">
      <AppSidebar v-if="isAuthenticated" />
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuth } from '@/composables/auth/useAuth'
import { useOrganization } from '@/composables/organizations/useOrganization'

const { isAuthenticated } = useAuth()
const { loadOrganizations } = useOrganization()

if (isAuthenticated.value) {
  await loadOrganizations()
}

watch(
  isAuthenticated,
  async (value: boolean) => {
    if (value) {
      await loadOrganizations()
    }
  },
  { immediate: false }
)
</script>

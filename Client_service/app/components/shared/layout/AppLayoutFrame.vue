<template>
  <div class="flex min-h-screen flex-col bg-parchment">
    <AppHeader />
    <div class="flex-1">
      <AppSidebar v-if="isAuthenticated" />
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
const { isAuthenticated } = useAuth()
const { loadOrganizations } = useOrganization()

watch(
  isAuthenticated,
  async (value: boolean) => {
    if (value) {
      await loadOrganizations()
    }
  },
  { immediate: true }
)
</script>

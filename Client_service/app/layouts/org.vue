<template>
  <AppLayoutFrame>
    <main :class="contentShellClass">
      <OrganizationContextNav v-if="showOrganizationNav" :slug="slug" />
      <slot />
    </main>
  </AppLayoutFrame>
</template>

<script setup lang="ts">
const route = useRoute()

const slug = computed(() => route.params.id as string | undefined)
const showOrganizationNav = computed(() => Boolean(slug.value) && route.name !== 'org-id-public')
const contentShellClass = computed(() => (route.meta.orgFullBleed ? 'org-full-page-shell' : 'org-page-shell'))
</script>

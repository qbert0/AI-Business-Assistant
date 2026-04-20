<template>
  <div v-if="slug" class="context-nav">
    <div v-if="organization" class="context-organization-label">
      <span>{{ text.drawer.organizationLabel }}</span>
      <strong>{{ organization.name }}</strong>
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
import { getOrganizationNavigation } from '@/constants/navigation'

const { text } = useAppLocale()
const { getOrganizationBySlug } = useOrganization()

const props = defineProps<{
  slug?: string
}>()

const organization = computed(() => (props.slug ? getOrganizationBySlug(props.slug) : undefined))
const organizationNavigation = computed(() => getOrganizationNavigation(text))
</script>

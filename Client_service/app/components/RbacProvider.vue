<template>
  <slot v-if="allowed" />
  <section v-else class="surface-card space-y-3">
    <p class="eyebrow">Permission denied</p>
    <h1 class="page-title">You do not have access to this area</h1>
    <p class="muted-copy">Your current organization role does not include the permission required for this page.</p>
  </section>
</template>

<script setup lang="ts">
import type { OrganizationPermission } from '@/constants/rbac'

const props = defineProps<{
  slug: string
  permission: OrganizationPermission
}>()

const { can } = useRbac()
const allowed = computed(() => can(props.slug, props.permission))
</script>

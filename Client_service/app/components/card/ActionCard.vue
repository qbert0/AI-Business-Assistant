<template>
  <NuxtLink :to="item.link" class="action-card">
    <div class="card-icon">
      <Icon :name="item.icon" />
    </div>
    <div class="space-y-1.5">
      <h3>{{ item.title }}</h3>
      <p>{{ item.description }}</p>
    </div>
    <span class="card-link">
      {{ text.common.openPage }}
      <Icon name="lucide:arrow-up-right" />
    </span>
  </NuxtLink>
</template>

<script setup lang="ts">
import { useAppLocale } from '@/composables/system/useAppLocale'
import type { ActionCardItem } from '@/types/dashboard'

const { text } = useAppLocale()

defineProps<{
  item: ActionCardItem
}>()
</script>


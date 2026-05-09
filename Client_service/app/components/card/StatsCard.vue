<template>
  <section class="surface-dark space-y-4">
    <div class="space-y-1">
      <p class="eyebrow">{{ text.stats.eyebrow }}</p>
      <h2 class="text-title font-medium">{{ title }}</h2>
    </div>

    <div class="space-y-3">
      <div v-for="item in items" :key="item.label" class="stats-row">
        <div>
          <p class="stats-label">{{ item.label }}</p>
          <p class="stats-hint">{{ item.hint }}</p>
        </div>
        <strong class="stats-value">{{ item.value }}</strong>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { StatItem } from '@/types/dashboard'

const { text } = useAppLocale()

defineProps<{
  title: string
  items: StatItem[]
}>()
</script>


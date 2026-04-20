<template>
  <main class="space-y-4">
    <section class="surface-card space-y-3">
      <p class="eyebrow">{{ text.common.notifications }}</p>
      <h1 class="page-title">{{ text.personal.notificationsTitle }}</h1>
      <p class="muted-copy">{{ text.personal.notificationsDescription }}</p>
    </section>

    <section class="surface-card space-y-2">
      <NuxtLink v-for="item in notifications" :key="item.id" :to="item.to" class="search-result">
        <span>
          <strong>{{ item.title }}</strong>
          <p>{{ item.description }}</p>
        </span>
        <Icon name="lucide:arrow-up-right" />
      </NuxtLink>
    </section>
  </main>
</template>

<script setup lang="ts">
const { text } = useAppLocale()
const { notifications } = useAppNotifications()
</script>

<template>
  <main class="space-y-4">
    <section class="surface-card space-y-3">
      <p class="eyebrow">{{ text.common.notifications }}</p>
      <h1 class="page-title">{{ text.personal.notificationsTitle }}</h1>
      <p class="muted-copy">{{ text.personal.notificationsDescription }}</p>
    </section>

    <section class="surface-card space-y-2">
      <article v-for="item in notifications" :key="item.id" class="search-result">
        <span>
          <strong>{{ item.title }}</strong>
          <p>{{ item.description }}</p>
        </span>
        <div v-if="item.actionType === 'organization_invitation'" class="flex shrink-0 flex-wrap gap-2">
          <button class="btn-secondary" type="button" @click="respondToInvitation(item, 'decline')">Từ chối</button>
          <button class="btn-primary" type="button" @click="respondToInvitation(item, 'accept')">Đồng ý</button>
        </div>
        <NuxtLink v-else :to="item.to" class="icon-action-light">
          <Icon name="lucide:arrow-up-right" />
        </NuxtLink>
      </article>
      <p v-if="!notifications.length" class="table-copy">Chưa có thông báo mới.</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { useAppNotifications } from '@/composables/system/useAppNotifications'
import { useAppLocale } from '@/composables/system/useAppLocale'

const { text } = useAppLocale()
const { notifications, respondToInvitation } = useAppNotifications()
</script>

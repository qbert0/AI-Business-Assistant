<template>
  <main class="two-column-layout">
    <section class="surface-card space-y-4">
      <div>
        <p class="eyebrow">{{ text.requests.eyebrow }}</p>
        <h1 class="page-title">{{ text.requests.title }}</h1>
        <p class="muted-copy">{{ text.requests.description }}</p>
      </div>

      <input v-model="organizationName" class="app-input" :placeholder="text.requests.organizationPlaceholder" />
      <textarea v-model="note" class="app-textarea" rows="4" :placeholder="text.requests.notePlaceholder" />
      <button class="btn-primary" @click="handleRequest">{{ text.requests.submit }}</button>
    </section>

    <section class="surface-card space-y-3">
      <div>
        <p class="section-kicker">{{ text.requests.currentEyebrow }}</p>
        <h2 class="panel-title">{{ text.requests.currentTitle }}</h2>
      </div>

      <div class="space-y-3">
        <article v-for="item in joinRequests" :key="item.id" class="space-y-2 rounded-panel border border-cream bg-white p-3">
          <div class="flex items-start justify-between gap-3">
            <strong>{{ item.organizationName }}</strong>
            <span :class="item.status === 'approved' ? 'status-badge status-success' : 'status-badge status-warning'">
              {{ statusLabel(item.status) }}
            </span>
          </div>
          <p class="muted-copy">{{ item.note }}</p>
        </article>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
import type { JoinRequest } from '@/types/organization'

const { text } = useAppLocale()

const { joinRequests, requestJoinOrganization } = useOrganization()

const organizationName = ref('')
const note = ref('')
const statusLabel = (status: JoinRequest['status']) => (status === 'approved' ? text.common.approved : text.common.pending)

const handleRequest = async () => {
  if (!organizationName.value) {
    return
  }

  await requestJoinOrganization(organizationName.value, note.value)
  organizationName.value = ''
  note.value = ''
}
</script>


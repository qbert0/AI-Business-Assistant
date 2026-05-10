<template>
  <div v-if="organization" class="space-y-6">
    <section class="surface-card space-y-3">
      <p class="eyebrow">{{ text.common.settings }}</p>
      <h1 class="page-title">{{ text.organizationSettings.titlePrefix }} {{ organization.name }}</h1>
      <p class="muted-copy">{{ text.organizationSettings.description }}</p>
    </section>

    <section class="grid gap-3 lg:grid-cols-2">
      <article class="surface-card space-y-3">
        <h2 class="panel-title">{{ text.organizationSettings.identityTitle }}</h2>
        <input v-model="organizationName" class="app-input" />
        <div class="flex gap-2">
          <button class="btn-primary">{{ text.common.openPage }}</button>
          <button class="btn-secondary">{{ text.common.cancel }}</button>
        </div>
      </article>

      <article class="surface-card space-y-3">
        <h2 class="panel-title">{{ text.organizationSettings.paymentTitle }}</h2>
        <p class="muted-copy">{{ text.organizationSettings.paymentDescription }}</p>
        <button class="btn-secondary">{{ text.common.openPage }}</button>
      </article>
    </section>

    <AppPanel>
      <template #header-left>
        <h2 class="panel-title">{{ text.organizationSettings.publicAccessTitle }}</h2>
      </template>

      <div class="settings-toggle-row">
        <div class="min-w-0">
          <span>{{ text.organizationSettings.allowJoinRequests }}</span>
          <p class="text-caption font-normal text-olive">{{ text.organizationSettings.allowJoinRequestsDescription }}</p>
        </div>
        <input v-model="allowJoinRequests" type="checkbox" />
      </div>
    </AppPanel>

    <section class="surface-card space-y-3">
      <h2 class="panel-title text-orange">{{ text.organizationSettings.dangerTitle }}</h2>
      <button class="btn-dark" @click="confirmDelete">{{ text.organizationSettings.deleteOrganization }}</button>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
definePageMeta({
  layout: 'org'
})

const { text } = useAppLocale()
const route = useRoute()
const { getOrganizationBySlug } = useOrganization()

const slug = computed(() => route.params.id as string)
const organization = computed(() => getOrganizationBySlug(slug.value))
const organizationName = ref('')
const allowJoinRequests = ref(true)

watchEffect(() => {
  organizationName.value = organization.value?.name ?? ''
})

const confirmDelete = () => {
  window.confirm(text.organizationSettings.deleteConfirm)
}
</script>

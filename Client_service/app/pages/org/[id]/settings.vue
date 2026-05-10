<template>
  <div v-if="organization" class="org-content-page">
    <section class="surface-card org-hero-card space-y-3">
      <p class="eyebrow">{{ text.common.settings }}</p>
      <h1 class="page-title">{{ text.organizationSettings.titlePrefix }} {{ organization.name }}</h1>
      <p class="muted-copy">{{ text.organizationSettings.description }}</p>
    </section>

    <section class="org-card-grid-2">
      <article class="surface-card space-y-3">
        <h2 class="panel-title">{{ text.organizationSettings.identityTitle }}</h2>
        <input v-model="organizationName" class="app-input" :placeholder="text.organizationSettings.organizationName" />
        <div class="space-y-2">
          <div class="flex items-center justify-between gap-3">
            <h3 class="field-label">{{ text.organizationSettings.identityKeywordsTitle }}</h3>
            <span class="text-caption text-olive">3</span>
          </div>
          <input
            v-for="(keyword, index) in identityKeywords"
            :key="`keyword-${index}`"
            v-model="identityKeywords[index]"
            class="app-input"
            :placeholder="`${text.organizationSettings.keywordPlaceholder} ${index + 1}`"
          />
          <p class="text-caption text-olive">{{ text.organizationSettings.identityKeywordsDescription }}</p>
        </div>
        <div class="settings-card-actions">
          <button class="btn-primary" :disabled="isSaving" @click="saveSettings">
            {{ isSaving ? text.organizationSettings.saving : text.common.saveChanges }}
          </button>
          <button class="btn-secondary" :disabled="isSaving" @click="resetForm">{{ text.common.cancel }}</button>
        </div>
      </article>

      <article class="surface-card space-y-3">
        <h2 class="panel-title">{{ text.organizationSettings.suggestedQuestionsTitle }}</h2>
        <p class="muted-copy">{{ text.organizationSettings.suggestedQuestionsDescription }}</p>
        <input
          v-for="(question, index) in suggestedQuestions"
          :key="`question-${index}`"
          v-model="suggestedQuestions[index]"
          class="app-input"
          :placeholder="`${text.organizationSettings.questionPlaceholder} ${index + 1}`"
        />
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

    <AppPanel>
      <template #header-left>
        <h2 class="panel-title">{{ text.organizationSettings.guestAccessTitle }}</h2>
      </template>

      <div class="space-y-4">
        <label class="settings-toggle-row">
          <div class="min-w-0">
            <span>{{ text.organizationSettings.allowGuestChat }}</span>
            <p class="text-caption font-normal text-olive">{{ text.organizationSettings.allowGuestChatDescription }}</p>
          </div>
          <input v-model="allowGuestChat" type="checkbox" />
        </label>

        <label class="settings-toggle-row">
          <div class="min-w-0">
            <span>{{ text.organizationSettings.allowGuestDocumentAccess }}</span>
            <p class="text-caption font-normal text-olive">{{ text.organizationSettings.allowGuestDocumentAccessDescription }}</p>
          </div>
          <input v-model="allowGuestDocumentAccess" type="checkbox" :disabled="!allowGuestChat" />
        </label>
      </div>
    </AppPanel>

    <section class="surface-card space-y-3">
      <h2 class="panel-title text-orange">{{ text.organizationSettings.dangerTitle }}</h2>
      <button class="btn-dark" @click="confirmDelete">{{ text.organizationSettings.deleteOrganization }}</button>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { OrganizationSettingsData } from '@/types/organization'

definePageMeta({
  layout: 'org',
  orgFullBleed: true
})

const { text } = useAppLocale()
const route = useRoute()
const { getOrganizationBySlug, loadOrganizations } = useOrganization()
const api = useApiOrganizationSettings()

const slug = computed(() => route.params.id as string)
const organization = computed(() => getOrganizationBySlug(slug.value))
const organizationName = ref('')
const allowJoinRequests = ref(true)
const allowGuestChat = ref(false)
const allowGuestDocumentAccess = ref(false)
const identityKeywords = ref(['', '', ''])
const suggestedQuestions = ref(['', '', ''])
const isSaving = ref(false)

const normalizeSettings = (settings?: Partial<OrganizationSettingsData>) => ({
  allowJoinRequests: settings?.allowJoinRequests !== false,
  allowGuestChat: settings?.allowGuestChat === true,
  allowGuestDocumentAccess: settings?.allowGuestDocumentAccess === true,
  identityKeywords: [...Array.from({ length: 3 }, (_, index) => settings?.identityKeywords?.[index] ?? '')],
  suggestedQuestions: [...Array.from({ length: 3 }, (_, index) => settings?.suggestedQuestions?.[index] ?? '')]
})

watchEffect(() => {
  organizationName.value = organization.value?.name ?? ''
})

const loadSettings = async () => {
  const response = await api.get(slug.value)
  const normalized = normalizeSettings(response.settings)
  allowJoinRequests.value = normalized.allowJoinRequests
  allowGuestChat.value = normalized.allowGuestChat
  allowGuestDocumentAccess.value = normalized.allowGuestDocumentAccess
  identityKeywords.value = normalized.identityKeywords
  suggestedQuestions.value = normalized.suggestedQuestions
}

const resetForm = () => {
  organizationName.value = organization.value?.name ?? ''
  void loadSettings()
}

const saveSettings = async () => {
  isSaving.value = true
  try {
    await api.update(slug.value, {
      name: organizationName.value.trim(),
      settings: {
        allowJoinRequests: allowJoinRequests.value,
        allowGuestChat: allowGuestChat.value,
        allowGuestDocumentAccess: allowGuestDocumentAccess.value,
        identityKeywords: identityKeywords.value.map((item) => item.trim()).filter(Boolean).slice(0, 3),
        suggestedQuestions: suggestedQuestions.value.map((item) => item.trim()).filter(Boolean).slice(0, 3)
      }
    })
    await loadOrganizations()
    await loadSettings()
  } finally {
    isSaving.value = false
  }
}

const confirmDelete = () => {
  window.confirm(text.organizationSettings.deleteConfirm)
}

onMounted(async () => {
  await loadOrganizations()
  await loadSettings()
})
</script>

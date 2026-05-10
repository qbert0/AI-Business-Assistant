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
          <button class="btn-primary" :disabled="isSavingIdentity" @click="saveIdentitySettings">
            {{ isSavingIdentity ? text.organizationSettings.saving : text.common.saveChanges }}
          </button>
          <button class="btn-secondary" :disabled="isSavingIdentity" @click="clearIdentityKeywords">
            {{ text.organizationSettings.clearIdentityKeywords }}
          </button>
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
        <p class="text-caption text-olive">{{ suggestionSaveState }}</p>
        <div class="settings-card-actions">
          <button class="btn-primary" :disabled="isSavingSuggestions" @click="saveSuggestedQuestions">
            {{ isSavingSuggestions ? text.organizationSettings.saving : text.common.saveChanges }}
          </button>
        </div>
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

      <div class="settings-card-actions mt-3">
        <button class="btn-primary" :disabled="isSavingPublicAccess" @click="savePublicAccessSettings">
          {{ isSavingPublicAccess ? text.organizationSettings.saving : text.common.saveChanges }}
        </button>
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

        <div class="settings-card-actions">
          <button class="btn-primary" :disabled="isSavingGuestAccess" @click="saveGuestAccessSettings">
            {{ isSavingGuestAccess ? text.organizationSettings.saving : text.common.saveChanges }}
          </button>
        </div>
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
const isSavingIdentity = ref(false)
const isSavingPublicAccess = ref(false)
const isSavingGuestAccess = ref(false)
const isSavingSuggestions = ref(false)
const isSettingsLoaded = ref(false)
const suggestionSaveState = ref(text.organizationSettings.suggestionAutoSaveReady)
let suggestionSaveTimer: ReturnType<typeof setTimeout> | null = null

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

watch(allowGuestChat, (enabled) => {
  if (!enabled) {
    allowGuestDocumentAccess.value = false
  }
})

const loadSettings = async () => {
  const response = await api.get(slug.value)
  const normalized = normalizeSettings(response.settings)
  allowJoinRequests.value = normalized.allowJoinRequests
  allowGuestChat.value = normalized.allowGuestChat
  allowGuestDocumentAccess.value = normalized.allowGuestDocumentAccess
  identityKeywords.value = normalized.identityKeywords
  suggestedQuestions.value = normalized.suggestedQuestions
  isSettingsLoaded.value = true
}

const clearIdentityKeywords = () => {
  identityKeywords.value = ['', '', '']
}

const saveIdentitySettings = async () => {
  isSavingIdentity.value = true
  try {
    await api.update(slug.value, {
      name: organizationName.value.trim(),
      settings: {
        identityKeywords: identityKeywords.value.map((item) => item.trim()).filter(Boolean).slice(0, 3)
      }
    })
    await loadOrganizations()
    await loadSettings()
  } finally {
    isSavingIdentity.value = false
  }
}

const savePublicAccessSettings = async () => {
  isSavingPublicAccess.value = true
  try {
    await api.update(slug.value, {
      settings: {
        allowJoinRequests: allowJoinRequests.value
      }
    })
    await loadSettings()
  } finally {
    isSavingPublicAccess.value = false
  }
}

const saveGuestAccessSettings = async () => {
  isSavingGuestAccess.value = true
  try {
    await api.update(slug.value, {
      settings: {
        allowGuestChat: allowGuestChat.value,
        allowGuestDocumentAccess: allowGuestChat.value && allowGuestDocumentAccess.value
      }
    })
    await loadSettings()
  } finally {
    isSavingGuestAccess.value = false
  }
}

const saveSuggestedQuestions = async () => {
  if (!isSettingsLoaded.value) {
    return
  }

  if (suggestionSaveTimer) {
    clearTimeout(suggestionSaveTimer)
    suggestionSaveTimer = null
  }
  isSavingSuggestions.value = true
  suggestionSaveState.value = text.organizationSettings.suggestionAutoSaving
  try {
    await api.update(slug.value, {
      settings: {
        suggestedQuestions: suggestedQuestions.value.map((item) => item.trim()).filter(Boolean).slice(0, 3)
      }
    })
    suggestionSaveState.value = text.organizationSettings.suggestionAutoSaved
  } catch {
    suggestionSaveState.value = text.organizationSettings.suggestionAutoSaveFailed
  } finally {
    isSavingSuggestions.value = false
  }
}

const confirmDelete = () => {
  window.confirm(text.organizationSettings.deleteConfirm)
}

onMounted(async () => {
  await loadOrganizations()
  await loadSettings()
})

watch(
  suggestedQuestions,
  () => {
    if (!isSettingsLoaded.value) {
      return
    }
    if (suggestionSaveTimer) {
      clearTimeout(suggestionSaveTimer)
    }
    suggestionSaveState.value = text.organizationSettings.suggestionAutoSavePending
    suggestionSaveTimer = setTimeout(() => {
      void saveSuggestedQuestions()
    }, 700)
  },
  { deep: true }
)

onBeforeUnmount(() => {
  if (suggestionSaveTimer) {
    clearTimeout(suggestionSaveTimer)
  }
})
</script>

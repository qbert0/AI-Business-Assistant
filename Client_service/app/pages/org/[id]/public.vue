<template>
  <main class="org-content-page">
    <AppPanel v-if="organization">
      <template #header-left>
        <div>
          <p class="eyebrow">{{ text.organizationPublic.eyebrow }}</p>
          <h1 class="page-title">{{ organization.name }}</h1>
        </div>
      </template>

      <template #header-right>
        <span class="status-badge status-info">{{ organization.industry }}</span>
      </template>

      <div class="space-y-4">
        <p class="muted-copy">{{ organization.description }}</p>

        <div class="grid gap-2 sm:grid-cols-3">
          <div class="rounded-xl bg-white p-3">
            <p class="text-caption text-stone">{{ text.common.employees }}</p>
            <strong class="text-xl">{{ organization.employeesCount }}</strong>
          </div>
          <div class="rounded-xl bg-white p-3">
            <p class="text-caption text-stone">{{ text.common.documents }}</p>
            <strong class="text-xl">{{ organization.documentsCount }}</strong>
          </div>
          <div class="rounded-xl bg-white p-3">
            <p class="text-caption text-stone">{{ text.organizations.visits }}</p>
            <strong class="text-xl">{{ organization.visits }}</strong>
          </div>
        </div>
      </div>
    </AppPanel>

    <AppPanel v-if="organization">
      <template #header-left>
        <h2 class="panel-title">{{ text.organizationPublic.joinTitle }}</h2>
      </template>

      <div v-if="allowJoinRequests" class="space-y-3">
        <p class="table-copy">{{ text.organizationPublic.joinDescription }}</p>
        <textarea v-model="note" class="app-textarea" rows="4" :placeholder="text.organizationPublic.notePlaceholder" />
        <button v-if="isAuthenticated" class="btn-primary" @click="submitJoinRequest">{{ text.organizationPublic.submit }}</button>
        <NuxtLink v-else class="btn-primary" :to="APP_ROUTES.authLogin">{{ text.organizationPublic.loginToRequest }}</NuxtLink>
      </div>

      <p v-else class="table-copy">{{ text.organizationPublic.joinDisabled }}</p>
    </AppPanel>

    <AppPanel v-if="organization">
      <template #header-left>
        <h2 class="panel-title">{{ text.organizationPublic.guestChatTitle }}</h2>
      </template>

      <div v-if="allowGuestChat" class="space-y-4">
        <p class="table-copy">{{ text.organizationPublic.guestChatDescription }}</p>
        <NuxtLink class="btn-primary" :to="getOrganizationRoute(slug, 'chat')">
          {{ text.organizationPublic.guestEnterCompany }}
        </NuxtLink>
        <div class="flex flex-wrap gap-2">
          <button v-for="item in suggestions" :key="item" class="question-chip" type="button" @click="useSuggestion(item)">
            {{ item }}
          </button>
        </div>

        <div class="public-chat-thread">
          <article
            v-for="message in guestMessages"
            :key="message.id"
            class="public-chat-message"
            :class="message.role"
          >
            <p class="whitespace-pre-line">{{ message.content }}</p>
          </article>
          <p v-if="!guestMessages.length" class="table-copy">{{ text.organizationPublic.guestChatPlaceholder }}</p>
        </div>

        <form class="chat-input-shell" @submit.prevent="askPublicQuestion">
          <textarea
            v-model="prompt"
            class="chat-input"
            rows="2"
            :placeholder="text.organizationPublic.guestChatPlaceholder"
            @keydown.enter.exact.prevent="askPublicQuestion"
          />
          <button class="btn-primary" type="submit" :disabled="isAsking || !prompt.trim()">
            {{ isAsking ? text.organizationPublic.guestChatAsking : text.chatPage.send }}
          </button>
        </form>
        <p v-if="!allowGuestDocumentAccess" class="text-caption text-olive">{{ text.organizationPublic.guestDocumentDisabled }}</p>
      </div>

      <p v-else class="table-copy">{{ text.organizationPublic.guestChatDisabled }}</p>
    </AppPanel>
  </main>
</template>

<script setup lang="ts">
import { useAuth } from '@/composables/auth/useAuth'
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
import { APP_ROUTES, getOrganizationRoute } from '@/constants/navigation'
import type { OrganizationSummary } from '@/types/organization'

definePageMeta({
  layout: 'org',
  orgFullBleed: true
})

const route = useRoute()
const { text } = useAppLocale()
const { isAuthenticated } = useAuth()
const { requestJoinOrganization } = useOrganization()

const note = ref('')
const prompt = ref('')
const suggestions = ref<string[]>([])
const isAsking = ref(false)
const slug = computed(() => route.params.id as string)
const guestMessages = ref<Array<{ id: string, role: 'user' | 'assistant', content: string }>>([])

const { data } = await useFetch<{ organization: OrganizationSummary, allowJoinRequests: boolean, allowGuestChat: boolean, allowGuestDocumentAccess: boolean }>(
  () => `/api/public/organizations/${slug.value}`
)

const organization = computed(() => data.value?.organization)
const allowJoinRequests = computed(() => data.value?.allowJoinRequests ?? false)
const allowGuestChat = computed(() => data.value?.allowGuestChat ?? false)
const allowGuestDocumentAccess = computed(() => data.value?.allowGuestDocumentAccess ?? false)

const submitJoinRequest = async () => {
  if (!organization.value) {
    return
  }

  await requestJoinOrganization(organization.value.name, note.value)
  note.value = ''
  await navigateTo(APP_ROUTES.organizations)
}

const askPublicQuestion = async () => {
  const currentPrompt = prompt.value.trim()
  if (!currentPrompt || isAsking.value) {
    return
  }

  prompt.value = ''
  guestMessages.value.push({
    id: `guest-user-${Date.now()}`,
    role: 'user',
    content: currentPrompt
  })
  isAsking.value = true
  try {
    const response = await $fetch<{ answer: string }>(`/api/public/organizations/${slug.value}/chat/ask`, {
      method: 'POST',
      body: { question: currentPrompt }
    })
    guestMessages.value.push({
      id: `guest-assistant-${Date.now()}`,
      role: 'assistant',
      content: response.answer
    })
  } catch (error) {
    prompt.value = currentPrompt
    throw error
  } finally {
    isAsking.value = false
  }
}

const useSuggestion = (question: string) => {
  prompt.value = question
}

onMounted(async () => {
  if (!allowGuestChat.value) {
    return
  }

  const response = await $fetch<{ suggestions: string[] }>(`/api/public/organizations/${slug.value}/chat/suggestions`)
  suggestions.value = response.suggestions
})
</script>

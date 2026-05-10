<template>
  <main class="org-content-page">
    <AppPanel v-if="organization">
      <template #header-left>
        <div>
          <p class="eyebrow">{{ text.organizationPublic.guestChatTitle }}</p>
          <h1 class="page-title">{{ organization.name }}</h1>
        </div>
      </template>

      <template #header-right>
        <NuxtLink class="btn-secondary" :to="getOrganizationPublicRoute(slug)">
          {{ text.organizationPublic.openPublicPage }}
        </NuxtLink>
      </template>

      <template #content>
        <div v-if="allowGuestChat" class="space-y-4">
          <p class="table-copy">{{ text.organizationPublic.guestChatDescription }}</p>

          <div class="flex flex-wrap gap-2">
            <button v-for="item in suggestions" :key="item" class="question-chip" type="button" @click="prompt = item">
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
      </template>
    </AppPanel>
  </main>
</template>

<script setup lang="ts">
import { getOrganizationPublicRoute } from '@/constants/navigation'
import type { OrganizationSummary } from '@/types/organization'

definePageMeta({
  layout: 'org',
  orgFullBleed: true
})

const route = useRoute()
const { text } = useAppLocale()
const slug = computed(() => String(route.params.id ?? route.params.slug ?? ''))

const prompt = ref('')
const suggestions = ref<string[]>([])
const isAsking = ref(false)
const guestMessages = ref<Array<{ id: string, role: 'user' | 'assistant', content: string }>>([])

const GUEST_CHAT_TTL_MS = 60 * 60 * 1000
const storageKey = computed(() => `guest-chat:${slug.value}`)

const { data } = await useFetch<{
  organization: OrganizationSummary
  allowJoinRequests: boolean
  allowGuestChat: boolean
  allowGuestDocumentAccess: boolean
}>(() => `/api/public/organizations/${slug.value}`)

const organization = computed(() => data.value?.organization)
const allowGuestChat = computed(() => data.value?.allowGuestChat ?? false)
const allowGuestDocumentAccess = computed(() => data.value?.allowGuestDocumentAccess ?? false)

const persistGuestChat = () => {
  if (!import.meta.client) {
    return
  }

  localStorage.setItem(storageKey.value, JSON.stringify({
    updatedAt: Date.now(),
    messages: guestMessages.value
  }))
}

const restoreGuestChat = () => {
  if (!import.meta.client) {
    return
  }

  const raw = localStorage.getItem(storageKey.value)
  if (!raw) {
    return
  }

  try {
    const parsed = JSON.parse(raw) as { updatedAt?: number, messages?: typeof guestMessages.value }
    if (!parsed.updatedAt || Date.now() - parsed.updatedAt > GUEST_CHAT_TTL_MS) {
      localStorage.removeItem(storageKey.value)
      return
    }

    guestMessages.value = Array.isArray(parsed.messages) ? parsed.messages : []
  } catch {
    localStorage.removeItem(storageKey.value)
  }
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
  persistGuestChat()

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
    persistGuestChat()
  } catch (error) {
    prompt.value = currentPrompt
    throw error
  } finally {
    isAsking.value = false
  }
}

onMounted(async () => {
  restoreGuestChat()
  if (!allowGuestChat.value) {
    return
  }

  const response = await $fetch<{ suggestions: string[] }>(`/api/public/organizations/${slug.value}/chat/suggestions`)
  suggestions.value = response.suggestions
})
</script>

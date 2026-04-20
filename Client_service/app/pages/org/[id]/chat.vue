<template>
  <div v-if="organization" class="space-y-6">
    <section class="chat-layout">
      <ChatSessionSidebar
        :slug="slug"
        v-model:selected-session-id="selectedSessionId"
        :sessions="sessions"
      />

      <section class="surface-card space-y-4">
        <h1 class="page-title">{{ text.chatPage.titlePrefix }} {{ organization.name }}</h1>

        <div class="chat-thread">
          <article
            v-for="message in messages"
            :key="message.id"
            :class="message.role === 'assistant' ? 'chat-bubble assistant' : 'chat-bubble user'"
          >
            <p>{{ message.content }}</p>
            <div v-if="message.citations?.length" class="mt-3 flex flex-wrap gap-2">
              <span v-for="citation in message.citations" :key="citation" class="pill">{{ citation }}</span>
            </div>
          </article>
        </div>

        <div class="space-y-3">
          <textarea v-model="prompt" class="app-textarea" rows="4" :placeholder="UI_MESSAGES.chatPlaceholder" />
          <div class="flex flex-wrap gap-2.5">
            <button class="btn-primary" @click="handleAsk">{{ text.chatPage.send }}</button>
            <button class="btn-secondary" @click="fillSuggestion">{{ text.chatPage.useSuggestion }}</button>
          </div>
        </div>
      </section>

      <aside class="space-y-3">
        <section class="surface-card space-y-3">
          <h2 class="panel-title">{{ text.chatPage.suggestionsTitle }}</h2>
          <div class="flex flex-wrap gap-2.5">
            <button v-for="item in suggestions" :key="item.id" class="question-chip" @click="prompt = item.question">
              {{ item.question }}
            </button>
          </div>
        </section>

        <section class="surface-card space-y-3">
          <h2 class="panel-title">{{ text.chatPage.feedbackTitle }}</h2>
          <textarea v-model="feedbackComment" class="app-textarea" rows="3" :placeholder="text.chatPage.feedbackPlaceholder" />
          <div class="flex flex-wrap gap-2.5">
            <button class="btn-primary" @click="handleFeedback('positive')">{{ text.chatPage.positive }}</button>
            <button class="btn-secondary" @click="handleFeedback('negative')">{{ text.chatPage.negative }}</button>
          </div>
        </section>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import ChatSessionSidebar from '@/components/ChatSessionSidebar.vue'
import { UI_MESSAGES } from '@/constants/messages'

definePageMeta({
  layout: 'org'
})

const { text } = useAppLocale()

const route = useRoute()
const { loadOrganizations, getOrganizationBySlug } = useOrganization()
const { getMessages, getSessions, getSuggestions, askQuestion, submitFeedback, loadContext, loadMessages } = useChatbot()

const slug = computed(() => (route.params.slug ?? route.params.id) as string)
const organization = computed(() => getOrganizationBySlug(slug.value))
const messages = computed(() => getMessages(slug.value, selectedSessionId.value))
const sessions = computed(() => getSessions(slug.value))
const suggestions = computed(() => getSuggestions(slug.value))

const prompt = ref('')
const feedbackComment = ref('')
const selectedSessionId = ref<string | null>(null)

const handleAsk = async () => {
  if (!prompt.value) {
    return
  }

  await askQuestion(slug.value, prompt.value)
  prompt.value = ''
}

const fillSuggestion = () => {
  prompt.value = suggestions.value[0]?.question ?? ''
}

const handleFeedback = async (rating: 'positive' | 'negative') => {
  await submitFeedback(slug.value, rating, feedbackComment.value || UI_MESSAGES.feedbackDefault)
  feedbackComment.value = ''
}

onMounted(async () => {
  await loadOrganizations()
  await loadContext(slug.value)
  selectedSessionId.value = sessions.value[0]?.id ?? null
  await loadMessages(slug.value, selectedSessionId.value)
})
</script>


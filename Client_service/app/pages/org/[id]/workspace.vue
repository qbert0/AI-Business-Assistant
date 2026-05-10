<template>
  <!--
    Layout page:
    - Cột trái: sidebar của chat trong workspace tổ chức
    - Cột giữa: thread chat + composer
    - Cột phải: gợi ý câu hỏi
  -->
  <div v-if="organization" class="org-chat-workspace">
    <section class="chat-layout org-chat-layout">
      <!-- Left rail: organization chat sessions -->
      <div class="org-chat-sidebar-shell">
        <ChatSessionSidebar
          :slug="slug"
          v-model:selected-session-id="selectedSessionId"
          :sessions="sessions"
        />
      </div>

      <!-- Main column: thread + composer -->
      <section class="surface-card org-chat-main-panel">
        <div class="org-chat-main-header">
          <h1 class="page-title">{{ organization.name }} Workspace</h1>
        </div>

        <div ref="chatThreadRef" class="chat-thread org-chat-thread">
          <ChatMessageBubble
            v-for="message in messages"
            :key="message.id"
            :data-message-id="message.id"
            :data-message-role="message.role"
            :message="message"
            :is-latest-assistant="message.id === latestAssistantMessage?.id"
            :feedback-expanded="Boolean(expandedFeedbackMessageIds[message.id])"
            :feedback-comment="feedbackDrafts[message.id] ?? ''"
            :feedback-pending="feedbackPendingMessageId === message.id"
            :feedback-submitted="Boolean(submittedFeedbackMessageIds[message.id])"
            :feedback-title="text.chatPage.feedbackTitle"
            :feedback-placeholder="text.chatPage.feedbackPlaceholder"
            :positive-label="text.chatPage.positive"
            :negative-label="text.chatPage.negative"
            @toggle-feedback="toggleFeedback"
            @submit-feedback="handleFeedback"
            @update:feedback-comment="setFeedbackComment(message.id, $event)"
          />
        </div>

        <div class="org-chat-composer">
          <textarea
            v-model="prompt"
            class="app-textarea"
            rows="4"
            :placeholder="UI_MESSAGES.chatPlaceholder"
            @keydown.enter.exact.prevent="handleAsk"
          />
          <div class="flex flex-wrap gap-2.5">
            <button class="btn-primary" :disabled="isStreaming || !prompt.trim()" @click="handleAsk">{{ isStreaming ? 'Dang tra loi...' : text.chatPage.send }}</button>
            <button class="btn-secondary" @click="fillSuggestion">{{ text.chatPage.useSuggestion }}</button>
          </div>
          <p class="chat-disclaimer">{{ UI_MESSAGES.chatDisclaimer }}</p>
        </div>
      </section>

      <!-- Right rail: suggestion chips -->
      <aside class="org-chat-rail">
        <section class="surface-card org-chat-rail-card space-y-3">
          <h2 class="panel-title">{{ text.chatPage.suggestionsTitle }}</h2>
          <div class="flex flex-wrap gap-2.5">
            <button v-for="item in suggestions" :key="item.id" class="question-chip" @click="prompt = item.question">
              {{ item.question }}
            </button>
          </div>
        </section>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import ChatMessageBubble from '@/components/shared/chat/ChatMessageBubble.vue'
import { useChatbot } from '@/composables/chat/useChatbot'
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
import ChatSessionSidebar from '@/components/shared/chat/ChatSessionSidebar.vue'
import { UI_MESSAGES } from '@/constants/messages'

definePageMeta({
  layout: 'org',
  orgFullBleed: true
})

const { text } = useAppLocale()

const route = useRoute()
const { loadOrganizations, getOrganizationBySlug } = useOrganization()
const { getMessages, getSessions, getSuggestions, askQuestion, submitFeedback, loadContext, loadMessages, getIsStreaming } = useChatbot()

const slug = computed(() => (route.params.slug ?? route.params.id) as string)
const organization = computed(() => getOrganizationBySlug(slug.value))
const messages = computed(() => getMessages(slug.value, selectedSessionId.value))
const sessions = computed(() => getSessions(slug.value))
const suggestions = computed(() => getSuggestions(slug.value))
const isStreaming = computed(() => getIsStreaming(slug.value))
const latestAssistantMessage = computed(() => [...messages.value].reverse().find((message) => message.role === 'assistant') ?? null)

const prompt = ref('')
const selectedSessionId = ref<string | null>(null)
const chatThreadRef = ref<HTMLElement | null>(null)
const shouldScrollToSubmittedMessage = ref(false)
const feedbackDrafts = ref<Record<string, string>>({})
const expandedFeedbackMessageIds = ref<Record<string, boolean>>({})
const submittedFeedbackMessageIds = ref<Record<string, boolean>>({})
const feedbackPendingMessageId = ref<string | null>(null)

const scrollToSubmittedMessage = async () => {
  await nextTick()
  const threadElement = chatThreadRef.value
  if (!threadElement) {
    return
  }

  const latestAssistantMessage = [...threadElement.querySelectorAll<HTMLElement>('[data-message-role="assistant"]')].at(-1)
  const latestUserMessage = [...threadElement.querySelectorAll<HTMLElement>('[data-message-role="user"]')].at(-1)
  const targetMessage = latestAssistantMessage ?? latestUserMessage
  if (targetMessage) {
    targetMessage.scrollIntoView({ block: 'end', behavior: 'smooth' })
    return
  }

  threadElement.scrollTo({ top: threadElement.scrollHeight, behavior: 'smooth' })
}

const primeWorkspace = async () => {
  try {
    await loadOrganizations()
    await loadContext(slug.value)
    selectedSessionId.value = getSessions(slug.value)[0]?.id ?? null
    await loadMessages(slug.value, selectedSessionId.value)
  } catch {
    selectedSessionId.value = null
  }
}

const handleAsk = async () => {
  const currentPrompt = prompt.value.trim()
  if (!currentPrompt || isStreaming.value) {
    return
  }

  prompt.value = ''
  shouldScrollToSubmittedMessage.value = true
  try {
    selectedSessionId.value = await askQuestion(
      slug.value,
      currentPrompt,
      selectedSessionId.value,
      {
        onSession: (sessionId: string) => {
          selectedSessionId.value = sessionId
        }
      }
    )
  } catch (error) {
    shouldScrollToSubmittedMessage.value = false
    prompt.value = currentPrompt
    throw error
  }
}

const fillSuggestion = () => {
  prompt.value = suggestions.value[0]?.question ?? ''
}

const setFeedbackComment = (messageId: string, value: string) => {
  feedbackDrafts.value = {
    ...feedbackDrafts.value,
    [messageId]: value
  }
}

const toggleFeedback = (messageId: string) => {
  expandedFeedbackMessageIds.value = {
    ...expandedFeedbackMessageIds.value,
    [messageId]: !expandedFeedbackMessageIds.value[messageId]
  }
}

const handleFeedback = async (messageId: string, rating: 'positive' | 'negative') => {
  if (!messageId || feedbackPendingMessageId.value) {
    return
  }

  feedbackPendingMessageId.value = messageId
  try {
    await submitFeedback(
      slug.value,
      messageId,
      rating,
      feedbackDrafts.value[messageId] || UI_MESSAGES.feedbackDefault
    )
    submittedFeedbackMessageIds.value = {
      ...submittedFeedbackMessageIds.value,
      [messageId]: true
    }
    feedbackDrafts.value = {
      ...feedbackDrafts.value,
      [messageId]: ''
    }
    expandedFeedbackMessageIds.value = {
      ...expandedFeedbackMessageIds.value,
      [messageId]: false
    }
  } finally {
    feedbackPendingMessageId.value = null
  }
}

onMounted(() => {
  primeWorkspace()
})

watch(selectedSessionId, (sessionId: string | null) => {
  loadMessages(slug.value, sessionId)
})

watch(
  () => messages.value.map((message) => `${message.id}:${message.role}`).join('|'),
  async () => {
    if (!shouldScrollToSubmittedMessage.value) {
      return
    }

    const hasSubmittedUserMessage = messages.value.some((message) => message.role === 'user')
    if (!hasSubmittedUserMessage) {
      return
    }

    shouldScrollToSubmittedMessage.value = false
    await scrollToSubmittedMessage()
  },
  { flush: 'post' }
)

/*
Layout map

+-------------------------------------------------------------------+
| Session sidebar | Chat thread + composer | Suggestions             |
+-------------------------------------------------------------------+
*/
</script>

<template>
  <!--
    Layout page:
    - Cột trái: sidebar chọn workspace + lịch sử chat
    - Cột giữa: vùng hội thoại
    - Đáy cột giữa: composer
  -->
  <main class="workspace-chat-page">
    <!-- Left rail: workspace switcher + session list -->
    <ChatSessionSidebar
      v-model:slug="selectedSlug"
      v-model:selected-session-id="selectedSessionId"
      :sessions="sessions"
      :organizations="organizations"
    />

    <!-- Main column: thread + composer -->
    <section class="workspace-chat-main">
      <!-- Conversation thread -->
      <div ref="chatThreadRef" class="chat-thread chat-thread-main">
        <article v-if="!messages.length" class="chat-empty-state">
          <div class="chat-empty-visual">
            <Icon name="lucide:sparkles" />
          </div>
          <h2>{{ text.workspace.noChatSelectedTitle }}</h2>
          <p>{{ text.workspace.noChatSelectedDescription }}</p>
          <div class="flex flex-wrap justify-center gap-2.5">
            <button v-for="item in suggestions" :key="item.id" class="question-chip" @click="prompt = item.question">
              {{ item.question }}
            </button>
          </div>
        </article>

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

      <!-- Composer area -->
      <div class="chat-composer">
        <div class="chat-suggestion-row">
          <button v-for="item in suggestions.slice(0, 3)" :key="item.id" class="question-chip" @click="prompt = item.question">
            {{ item.question }}
          </button>
        </div>
        <div class="chat-input-shell">
          <textarea
            v-model="prompt"
            class="chat-input"
            rows="2"
            :placeholder="text.workspace.inputPlaceholder"
            @keydown.enter.exact.prevent="handleAsk"
          />
          <button class="btn-primary" type="button" :disabled="isStreaming || !prompt.trim()" @click="handleAsk">{{ isStreaming ? 'Dang tra loi...' : text.workspace.send }}</button>
        </div>
        <p class="chat-disclaimer">{{ UI_MESSAGES.chatDisclaimer }}</p>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import ChatMessageBubble from '@/components/shared/chat/ChatMessageBubble.vue'
import { useChatbot } from '@/composables/chat/useChatbot'
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
import ChatSessionSidebar from '@/components/shared/chat/ChatSessionSidebar.vue'
import { UI_MESSAGES } from '@/constants/messages'
import type { ChatSession, OrganizationSummary } from '@/types/organization'

const { text } = useAppLocale()
const { organizations } = useOrganization()
const { getMessages, getSessions, getSuggestions, askQuestion, submitFeedback, loadContext, loadMessages, getIsStreaming } = useChatbot()

const selectedSlug = ref('personal')
const selectedSessionId = ref<string | null>(null)
const messages = computed(() => getMessages(selectedSlug.value, selectedSessionId.value))
const sessions = computed(() => getSessions(selectedSlug.value))
const suggestions = computed(() => getSuggestions(selectedSlug.value))
const isStreaming = computed(() => getIsStreaming(selectedSlug.value))
const latestAssistantMessage = computed(() => [...messages.value].reverse().find((message) => message.role === 'assistant') ?? null)
const prompt = ref('')
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
    await loadContext(selectedSlug.value)
    selectedSessionId.value = getSessions(selectedSlug.value)[0]?.id ?? null
    await loadMessages(selectedSlug.value, selectedSessionId.value)
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
      selectedSlug.value,
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
      selectedSlug.value,
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

watch(organizations, (value: OrganizationSummary[]) => {
  if (!selectedSlug.value && value[0]) {
    selectedSlug.value = 'personal'
  }
})

watch(selectedSlug, () => {
  selectedSessionId.value = null
  loadContext(selectedSlug.value)
})

watch(sessions, (value: ChatSession[]) => {
  if (selectedSessionId.value && value.some((session: ChatSession) => session.id === selectedSessionId.value)) {
    return
  }

  selectedSessionId.value = value[0]?.id ?? null
}, { immediate: true })

watch(selectedSessionId, (value: string | null) => {
  loadMessages(selectedSlug.value, value)
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

+---------------------------------------------------------------+
| Sidebar chat |               Thread area                      |
| workspace    |-----------------------------------------------|
| sessions     | suggestion chips                              |
| history      | composer textarea + send button               |
+---------------------------------------------------------------+
*/
</script>

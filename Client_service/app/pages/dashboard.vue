<template>
  <!--
    Layout page:
    - Cột trái: sidebar chọn workspace + lịch sử chat
    - Cột giữa: nội dung hội thoại đang mở
    - Đáy cột giữa: composer để gửi câu hỏi mới
  -->
  <main class="workspace-chat-page">
    <!-- Left rail: workspace switcher + chat session history -->
    <ChatSessionSidebar
      v-model:slug="selectedSlug"
      v-model:selected-session-id="selectedSessionId"
      :sessions="sessions"
      :organizations="organizations"
    />

    <!-- Main column: thread + composer -->
    <section class="workspace-chat-main">
      <!-- Conversation thread -->
      <div class="chat-thread chat-thread-main">
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
          :message="message"
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
        <p v-if="streamingStatus" class="text-sm opacity-70">{{ streamingStatus }}</p>
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
import type { ChatSession, OrganizationSummary } from '@/types/organization'

const { text } = useAppLocale()
const { organizations } = useOrganization()
const { getMessages, getSessions, getSuggestions, askQuestion, loadContext, loadMessages, getStreamingStatus, getIsStreaming } = useChatbot()

const selectedSlug = ref('personal')
const selectedSessionId = ref<string | null>(null)
const messages = computed(() => getMessages(selectedSlug.value, selectedSessionId.value))
const sessions = computed(() => getSessions(selectedSlug.value))
const suggestions = computed(() => getSuggestions(selectedSlug.value))
const streamingStatus = computed(() => getStreamingStatus(selectedSlug.value))
const isStreaming = computed(() => getIsStreaming(selectedSlug.value))
const prompt = ref('')

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
  try {
    selectedSessionId.value = await askQuestion(selectedSlug.value, currentPrompt, selectedSessionId.value)
  } catch (error) {
    prompt.value = currentPrompt
    throw error
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

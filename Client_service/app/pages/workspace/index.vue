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

        <article
          v-for="message in messages"
          :key="message.id"
          :class="message.role === 'assistant' ? 'chat-bubble assistant' : 'chat-bubble user'"
        >
          <p>{{ message.content }}</p>
          <p v-if="message.activity" class="mt-2 text-sm opacity-70">{{ message.activity }}</p>
          <div v-if="message.citations?.length" class="mt-3 flex flex-wrap gap-2">
            <a
              v-for="citation in message.citations"
              :key="`${message.id}-${citation.documentId}-${citation.fileName}`"
              class="pill"
              :href="citation.sourceUrl || undefined"
              target="_blank"
              rel="noreferrer"
            >
              {{ citation.fileName }}
            </a>
          </div>
          <div v-if="message.searchHits?.length" class="mt-3 space-y-2">
            <div
              v-for="hit in message.searchHits"
              :key="`${message.id}-${hit.documentId}`"
              class="rounded-md border border-white/10 px-3 py-2 text-sm"
            >
              <p class="font-medium">{{ hit.fileName }}</p>
              <p class="opacity-70">{{ hit.sourceUrl }}</p>
              <p v-if="hit.score !== null && hit.score !== undefined" class="opacity-60">Score: {{ hit.score.toFixed(3) }}</p>
            </div>
          </div>
        </article>
      </div>

      <!-- Composer area -->
      <div class="chat-composer">
        <div class="chat-suggestion-row">
          <button v-for="item in suggestions.slice(0, 3)" :key="item.id" class="question-chip" @click="prompt = item.question">
            {{ item.question }}
          </button>
        </div>
        <div class="chat-input-shell">
          <textarea v-model="prompt" class="chat-input" rows="2" :placeholder="text.workspace.inputPlaceholder" />
          <button class="btn-primary" type="button" :disabled="isStreaming" @click="handleAsk">{{ isStreaming ? 'Dang tra loi...' : text.workspace.send }}</button>
        </div>
        <p v-if="streamingStatus" class="text-sm opacity-70">{{ streamingStatus }}</p>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
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
  if (!prompt.value.trim()) {
    return
  }

  selectedSessionId.value = await askQuestion(selectedSlug.value, prompt.value.trim(), selectedSessionId.value)
  prompt.value = ''
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

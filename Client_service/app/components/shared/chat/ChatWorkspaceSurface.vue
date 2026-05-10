<template>
  <main class="workspace-chat-page">
    <ChatSessionSidebar
      v-model:slug="selectedSlug"
      v-model:selected-session-id="selectedSessionId"
      :sessions="sessions"
      :organizations="organizations"
      :allow-context-switch="true"
      :has-more-sessions="hasMoreSessions"
      :show-personal-context="showPersonalContext"
      @load-more="loadMoreSessions(selectedSlug)"
    />

    <section class="workspace-chat-main">
      <div class="chat-thread chat-thread-main">
        <article v-if="!selectedSessionId && !messages.length" class="chat-empty-state">
          <div class="chat-empty-visual">
            <Icon name="lucide:sparkles" />
          </div>
          <h2>{{ text.workspace.noChatSelectedTitle }}</h2>
          <p>{{ text.workspace.noChatSelectedDescription }}</p>
          <div class="flex flex-wrap justify-center gap-2.5">
            <button v-for="item in suggestions" :key="item.id" class="question-chip" type="button" @click="prompt = item.question">
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

      <div class="chat-composer">
        <div class="chat-suggestion-row">
          <button v-for="item in suggestions.slice(0, 3)" :key="item.id" class="question-chip" type="button" @click="prompt = item.question">
            {{ item.question }}
          </button>
        </div>
        <form class="chat-input-shell" @submit.prevent="handleAsk">
          <textarea
            v-model="prompt"
            class="chat-input"
            rows="2"
            :placeholder="text.workspace.inputPlaceholder"
            @keydown.enter.exact.prevent="handleAsk"
          />
          <button class="btn-primary" type="submit" :disabled="isStreaming || !prompt.trim()">
            {{ isStreaming ? 'Đang trả lời...' : text.workspace.send }}
          </button>
        </form>
        <p v-if="streamingStatus" class="text-sm opacity-70">{{ streamingStatus }}</p>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import ChatMessageBubble from '@/components/shared/chat/ChatMessageBubble.vue'
import ChatSessionSidebar from '@/components/shared/chat/ChatSessionSidebar.vue'
import { getContextChatRoute } from '@/constants/navigation'

const props = defineProps<{
  initialSlug: string
  initialSessionId?: string | null
}>()

const route = useRoute()
const router = useRouter()
const { text } = useAppLocale()
const {
  getMessages,
  getSessions,
  getSuggestions,
  getHasMoreSessions,
  askQuestion,
  loadContext,
  loadMoreSessions,
  loadMessages,
  getStreamingStatus,
  getIsStreaming
} = useChatbot()
const { organizations, loadOrganizations } = useOrganization()

const selectedSlug = ref(props.initialSlug)
const selectedSessionId = ref<string | null>(props.initialSessionId ?? null)
const prompt = ref('')

const messages = computed(() => getMessages(selectedSlug.value, selectedSessionId.value))
const sessions = computed(() => getSessions(selectedSlug.value))
const suggestions = computed(() => getSuggestions(selectedSlug.value))
const hasMoreSessions = computed(() => getHasMoreSessions(selectedSlug.value))
const streamingStatus = computed(() => getStreamingStatus(selectedSlug.value))
const isStreaming = computed(() => getIsStreaming(selectedSlug.value))
const showPersonalContext = computed(() => organizations.value.length === 0)

const syncSessionFromRoute = async () => {
  const nextSessionId = props.initialSessionId ?? null
  selectedSessionId.value = nextSessionId
  if (nextSessionId) {
    await loadMessages(selectedSlug.value, nextSessionId)
  }
}

const primeWorkspace = async () => {
  await loadOrganizations()
  await loadContext(selectedSlug.value)
  await syncSessionFromRoute()
}

const handleAsk = async () => {
  const currentPrompt = prompt.value.trim()
  if (!currentPrompt || isStreaming.value) {
    return
  }

  prompt.value = ''
  try {
    const sessionId = await askQuestion(selectedSlug.value, currentPrompt, selectedSessionId.value)
    selectedSessionId.value = sessionId
    if (sessionId) {
      await router.push(getContextChatRoute(selectedSlug.value, sessionId))
    }
  } catch (error) {
    prompt.value = currentPrompt
    throw error
  }
}

onMounted(() => {
  primeWorkspace()
})

watch(
  () => props.initialSlug,
  async (nextSlug) => {
    selectedSlug.value = nextSlug
    selectedSessionId.value = props.initialSessionId ?? null
    await loadContext(nextSlug)
    if (selectedSessionId.value) {
      await loadMessages(nextSlug, selectedSessionId.value)
    }
  }
)

watch(
  () => props.initialSessionId,
  async () => {
    await syncSessionFromRoute()
  }
)

watch(selectedSlug, async (nextSlug, previousSlug) => {
  if (nextSlug === previousSlug) {
    return
  }

  selectedSessionId.value = null
  await loadContext(nextSlug)
})

watch(selectedSessionId, (value) => {
  if (value) {
    loadMessages(selectedSlug.value, value)
  }
})

watch(
  () => route.fullPath,
  () => {
    prompt.value = ''
  }
)
</script>

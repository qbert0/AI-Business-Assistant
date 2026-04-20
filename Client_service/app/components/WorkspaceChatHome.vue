<template>
  <main class="workspace-chat-page">
    <ChatSessionSidebar
      v-model:slug="selectedSlug"
      v-model:selected-session-id="selectedSessionId"
      :sessions="sessions"
      :organizations="organizations"
    />

    <section class="workspace-chat-main">
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
          <div v-if="message.citations?.length" class="mt-3 flex flex-wrap gap-2">
            <span v-for="citation in message.citations" :key="citation" class="pill">{{ citation }}</span>
          </div>
        </article>
      </div>

      <div class="chat-composer">
        <div class="chat-suggestion-row">
          <button v-for="item in suggestions.slice(0, 3)" :key="item.id" class="question-chip" @click="prompt = item.question">
            {{ item.question }}
          </button>
        </div>
        <div class="chat-input-shell">
          <textarea v-model="prompt" class="chat-input" rows="2" :placeholder="text.workspace.inputPlaceholder" />
          <button class="btn-primary" type="button" @click="handleAsk">{{ text.workspace.send }}</button>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
const { text } = useAppLocale()
const { organizations, getOrganizationBySlug } = useOrganization()
const { getMessages, getSessions, getSuggestions, askQuestion, loadContext, loadMessages } = useChatbot()

const selectedSlug = ref('personal')
const selectedSessionId = ref<string | null>(null)
const messages = computed(() => getMessages(selectedSlug.value, selectedSessionId.value))
const sessions = computed(() => getSessions(selectedSlug.value))
const suggestions = computed(() => getSuggestions(selectedSlug.value))
const prompt = ref('')

const handleAsk = async () => {
  if (!prompt.value.trim()) {
    return
  }

  selectedSessionId.value = await askQuestion(selectedSlug.value, prompt.value.trim(), selectedSessionId.value)
  prompt.value = ''
}

onMounted(async () => {
  await loadContext(selectedSlug.value)
  await loadMessages(selectedSlug.value, selectedSessionId.value)
})

watch(organizations, (value) => {
  if (!selectedSlug.value && value[0]) {
    selectedSlug.value = 'personal'
  }
})

watch(selectedSlug, () => {
  selectedSessionId.value = null
  loadContext(selectedSlug.value)
})

watch(sessions, (value) => {
  if (selectedSessionId.value && value.some((session) => session.id === selectedSessionId.value)) {
    return
  }

  selectedSessionId.value = value[0]?.id ?? null
}, { immediate: true })

watch(selectedSessionId, (value) => {
  loadMessages(selectedSlug.value, value)
})
</script>

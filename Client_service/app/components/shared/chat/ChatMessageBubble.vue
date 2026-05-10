<template>
  <article :class="message.role === 'assistant' ? 'chat-bubble assistant' : 'chat-bubble user'">
    <ChatMarkdownContent v-if="message.role === 'assistant'" :content="message.content" />
    <p v-else class="chat-user-message">{{ message.content }}</p>
    <p v-if="message.activity" class="chat-message-activity">{{ message.activity }}</p>
    <div v-if="message.artifacts?.length" class="mt-3 flex flex-col gap-2">
      <a
        v-for="artifact in message.artifacts"
        :key="`${message.id}-${artifact.kind}-${artifact.fileName}`"
        class="chat-report-artifact"
        :href="artifact.downloadUrl || artifact.sourceUrl || undefined"
        target="_blank"
        rel="noreferrer"
      >
        <span class="chat-report-artifact__label">{{ artifact.label }}</span>
        <strong class="chat-report-artifact__file">{{ artifact.fileName }}</strong>
      </a>
    </div>
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
  </article>
</template>

<script setup lang="ts">
import type { ChatMessage } from '@/types/organization'
import ChatMarkdownContent from '@/components/shared/chat/ChatMarkdownContent.vue'

defineProps<{
  message: ChatMessage
}>()
</script>

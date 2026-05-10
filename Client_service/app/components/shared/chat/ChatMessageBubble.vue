<template>
  <article v-bind="$attrs" :class="message.role === 'assistant' ? 'chat-bubble assistant' : 'chat-bubble user'">
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
  <section v-if="canShowFeedback" class="chat-feedback-shell">
    <div class="chat-feedback-toolbar">
      <button
        :class="['chat-feedback-trigger', { 'chat-feedback-trigger--icon': !isLatestAssistant }]"
        type="button"
        title="Gửi phản hồi"
        :aria-expanded="showFeedbackForm"
        @click="$emit('toggleFeedback', message.id)"
      >
        <Icon name="lucide:message-square-plus" />
        <span v-if="isLatestAssistant">{{ feedbackTitle }}</span>
      </button>
      <span v-if="feedbackSubmitted && !showFeedbackForm" class="chat-feedback-saved">Đã ghi nhận phản hồi.</span>
    </div>
    <div v-if="showFeedbackForm" class="chat-feedback-panel">
      <div class="chat-feedback-heading">
        <span>Góp ý riêng cho câu trả lời này</span>
        <button
          class="chat-feedback-close"
          type="button"
          aria-label="Thu gọn phản hồi"
          @click="$emit('toggleFeedback', message.id)"
        >
          <Icon name="lucide:x" />
        </button>
      </div>
      <textarea
        class="app-textarea"
        rows="2"
        :placeholder="feedbackPlaceholder"
        :value="feedbackComment"
        @input="$emit('update:feedbackComment', ($event.target as HTMLTextAreaElement).value)"
      />
      <div class="chat-feedback-actions">
        <button class="btn-primary" type="button" :disabled="feedbackPending" @click="$emit('submitFeedback', message.id, 'positive')">
          {{ positiveLabel }}
        </button>
        <button class="btn-secondary" type="button" :disabled="feedbackPending" @click="$emit('submitFeedback', message.id, 'negative')">
          {{ negativeLabel }}
        </button>
        <span v-if="feedbackSubmitted" class="chat-feedback-saved">Đã ghi nhận phản hồi.</span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { ChatMessage } from '@/types/organization'
import ChatMarkdownContent from '@/components/shared/chat/ChatMarkdownContent.vue'

defineOptions({
  inheritAttrs: false
})

const props = withDefaults(defineProps<{
  message: ChatMessage
  isLatestAssistant?: boolean
  feedbackExpanded?: boolean
  feedbackComment?: string
  feedbackPending?: boolean
  feedbackSubmitted?: boolean
  feedbackTitle?: string
  feedbackPlaceholder?: string
  positiveLabel?: string
  negativeLabel?: string
}>(), {
  isLatestAssistant: false,
  feedbackExpanded: false,
  feedbackComment: '',
  feedbackPending: false,
  feedbackSubmitted: false,
  feedbackTitle: 'Đánh giá câu trả lời',
  feedbackPlaceholder: 'Nhận xét ngắn về chất lượng câu trả lời',
  positiveLabel: 'Phản hồi tốt',
  negativeLabel: 'Cần cải thiện'
})

defineEmits<{
  'update:feedbackComment': [value: string]
  toggleFeedback: [messageId: string]
  submitFeedback: [messageId: string, rating: 'positive' | 'negative']
}>()

const canShowFeedback = computed(() => (
  props.message.role === 'assistant'
  && Boolean(props.message.content?.trim())
  && props.message.status !== 'thinking'
  && props.message.status !== 'streaming'
  && props.message.status !== 'error'
))
const showFeedbackForm = computed(() => canShowFeedback.value && props.feedbackExpanded)
</script>

<template>
  <div class="chat-markdown" v-html="renderedHtml" />
</template>

<script setup lang="ts">
import { renderMarkdownToHtml } from '@/utils/chat/render-markdown'

const props = defineProps<{
  content: string
}>()

const renderedHtml = computed(() => renderMarkdownToHtml(props.content || ''))
</script>

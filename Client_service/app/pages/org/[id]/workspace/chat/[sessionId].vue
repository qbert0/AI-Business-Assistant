<template>
  <ChatWorkspaceSurface :initial-slug="slug" :initial-session-id="sessionId" />
</template>

<script setup lang="ts">
import ChatWorkspaceSurface from '@/components/shared/chat/ChatWorkspaceSurface.vue'

definePageMeta({
  layout: 'default'
})

const route = useRoute()
const slug = computed(() => (route.params.slug ?? route.params.id) as string)
const sessionId = computed(() => route.params.sessionId as string)
</script>

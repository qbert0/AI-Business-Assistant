<template>
  <ChatWorkspaceSurface initial-slug="personal" :initial-session-id="sessionId" />
</template>

<script setup lang="ts">
import ChatWorkspaceSurface from '@/components/shared/chat/ChatWorkspaceSurface.vue'

const route = useRoute()
const sessionId = computed(() => route.params.id as string)
</script>

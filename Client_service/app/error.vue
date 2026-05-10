<script setup lang="ts">
import { useAppLocale } from '@/composables/system/useAppLocale'

type NuxtErrorLike = {
  statusCode?: number
  statusMessage?: string
  message?: string
}

const { text } = useAppLocale()

const props = defineProps<{
  error?: NuxtErrorLike | null
}>()

const errorText = computed(() => text?.error ?? {
  title: 'Something went wrong.',
  home: 'Back to home'
})

const statusCode = computed(() => props.error?.statusCode ?? 500)
const statusMessage = computed(
  () => props.error?.statusMessage || props.error?.message || 'Unexpected application error'
)

const handleError = () => {
  clearError({ redirect: '/' })
}
</script>

<template>
  <div class="flex min-h-screen flex-col items-center justify-center bg-parchment text-center">
    <div class="max-w-md rounded-panel border border-cream bg-ivory p-5 shadow-ring">
      <h1 class="mb-3 text-4xl font-bold text-crimson">{{ statusCode }}</h1>
      <h2 class="mb-2 page-title">{{ errorText.title }}</h2>
      <p class="mb-5 text-olive">{{ statusMessage }}</p>
      <button class="btn-primary" @click="handleError">
        {{ errorText.home }}
      </button>
    </div>
  </div>
</template>

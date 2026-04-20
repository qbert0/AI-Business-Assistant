<script setup lang="ts">
const { text } = useAppLocale()


defineProps({
  error: Object
})

const handleError = () => {
  clearError({ redirect: '/' })
}
</script>

<template>
  <div class="flex min-h-screen flex-col items-center justify-center bg-parchment text-center">
    <div class="max-w-md rounded-panel border border-cream bg-ivory p-5 shadow-ring">
      <h1 class="mb-3 text-4xl font-bold text-crimson">{{ error.statusCode }}</h1>
      <h2 class="mb-2 page-title">{{ text.error.title }}</h2>
      <p class="mb-5 text-olive">{{ error.statusMessage || error.message }}</p>
      <button class="btn-primary" @click="handleError">
        {{ text.error.home }}
      </button>
    </div>
  </div>
</template>


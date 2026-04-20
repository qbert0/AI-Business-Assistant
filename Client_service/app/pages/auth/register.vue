<script setup lang="ts">
import { APP_ROUTES } from '@/constants/navigation'

const { text } = useAppLocale()


definePageMeta({
  layout: 'auth'
})
</script>

<template>
  <div>
    <h1 class="mb-5 text-center page-title">{{ text.auth.registerTitle }}</h1>
    <div class="space-y-3">
      <input type="text" :placeholder="text.auth.usernameOnlyPlaceholder" class="app-input" />
      <input type="email" :placeholder="text.auth.emailPlaceholder" class="app-input" />
      <input type="password" :placeholder="text.auth.passwordPlaceholder" class="app-input" />
      <button class="btn-primary w-full">{{ text.auth.registerButton }}</button>
    </div>
    <p class="mt-4 text-center text-caption">
      {{ text.auth.hasAccount }} <NuxtLink :to="APP_ROUTES.authLogin" class="text-terracotta hover:underline">{{ text.auth.loginButton }}</NuxtLink>
    </p>
  </div>
</template>


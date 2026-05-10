<script setup lang="ts">
import { APP_ROUTES } from '@/constants/navigation'
import { useAuth } from '@/composables/auth/useAuth'
import { useAppLocale } from '@/composables/system/useAppLocale'
import { registerSchema } from '@/schemas/auth'

const { text } = useAppLocale()

definePageMeta({
  layout: 'auth'
})

const { register, error, isLoading } = useAuth()
const form = reactive({
  full_name: '',
  email: '',
  password: ''
})
const formError = ref('')

const registerWithPassword = async () => {
  const parsed = registerSchema.safeParse(form)
  if (!parsed.success) {
    formError.value = parsed.error.issues[0]?.message ?? 'Invalid register input'
    return
  }

  formError.value = ''
  await register(parsed.data)
}
</script>

<template>
  <div>
    <h1 class="mb-5 text-center page-title">{{ text.auth.registerTitle }}</h1>
    <div class="space-y-3">
      <input v-model="form.full_name" type="text" :placeholder="text.auth.usernameOnlyPlaceholder" class="app-input" />
      <input v-model="form.email" type="email" :placeholder="text.auth.emailPlaceholder" class="app-input" />
      <input
        v-model="form.password"
        type="password"
        :placeholder="text.auth.passwordPlaceholder"
        class="app-input"
        @keyup.enter="registerWithPassword"
      />
      <p v-if="formError || error" class="text-caption text-orange">{{ formError || error }}</p>
      <button class="btn-primary w-full" :disabled="isLoading" @click="registerWithPassword">
        {{ isLoading ? text.auth.signingIn : text.auth.registerButton }}
      </button>
    </div>
    <p class="mt-4 text-center text-caption">
      {{ text.auth.hasAccount }}
      <NuxtLink :to="APP_ROUTES.authLogin" class="text-terracotta hover:underline">{{ text.auth.loginButton }}</NuxtLink>
    </p>
  </div>
</template>

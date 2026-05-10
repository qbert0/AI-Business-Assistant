<script setup lang="ts">
import { APP_ROUTES } from '@/constants/navigation'
import { useAuth } from '@/composables/auth/useAuth'
import { useAppLocale } from '@/composables/system/useAppLocale'
import { loginSchema } from '@/schemas/auth'
import { AUTH_REDIRECT_QUERY, getAuthRedirectTarget } from '@/utils/auth-redirect'

const { text } = useAppLocale()
const route = useRoute()


definePageMeta({
  layout: 'auth'
})

const { error, isLoading } = useAuth()
const form = reactive({
  email: 'chau@example.com',
  password: 'demo123456'
})
const formError = ref('')
const rawRedirect = computed(() => route.query[AUTH_REDIRECT_QUERY])
const sanitizedRedirect = computed(() =>
  getAuthRedirectTarget(rawRedirect.value, APP_ROUTES.dashboard)
)
const googleAuthHref = computed(() => {
  const redirect = sanitizedRedirect.value
  const query = redirect ? `?${AUTH_REDIRECT_QUERY}=${encodeURIComponent(redirect)}` : ''
  return `/api/auth/google/start${query}`
})

if (rawRedirect.value !== undefined && rawRedirect.value !== sanitizedRedirect.value) {
  await navigateTo({
    path: APP_ROUTES.authLogin,
    query: sanitizedRedirect.value === APP_ROUTES.dashboard
      ? {}
      : { [AUTH_REDIRECT_QUERY]: sanitizedRedirect.value }
  }, { replace: true })
}

const loginWithPassword = async () => {
  const parsed = loginSchema.safeParse(form)
  if (!parsed.success) {
    formError.value = parsed.error.issues[0]?.message ?? 'Invalid login input'
    return
  }

  formError.value = ''
  await login(parsed.data)
}
</script>

<template>
  <div>
    <div class="mb-6 text-center">
      <div class="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-charcoal text-lg font-bold text-white">{{ text.auth.providerMark }}</div>
      <h1 class="page-title">{{ text.auth.loginTitle }}</h1>
    </div>

    <div class="mb-5 space-y-2.5">
      <a :href="googleAuthHref" class="btn-secondary block w-full text-center">
        {{ text.auth.google }}
      </a>
    </div>

    <div class="mb-5 text-center text-caption font-medium text-olive">{{ text.auth.emailDivider }}</div>

    <div class="space-y-3">
      <input v-model="form.email" type="email" :placeholder="text.auth.usernamePlaceholder" class="app-input" />
      <input v-model="form.password" type="password" :placeholder="text.auth.passwordPlaceholder" class="app-input" />
      <p v-if="formError || error" class="text-caption text-orange">{{ formError || error }}</p>
      <button class="btn-primary mt-1 w-full" :disabled="isLoading" @click="loginWithPassword">
        {{ isLoading ? text.auth.signingIn : text.auth.loginButton }}
      </button>
    </div>

    <p class="mt-5 border-t border-cream pt-5 text-center text-caption">
      {{ text.auth.noAccount }}
      <NuxtLink :to="APP_ROUTES.authRegister" class="font-medium text-terracotta hover:underline">{{ text.auth.createAccount }}</NuxtLink>
    </p>
  </div>
</template>



<script setup lang="ts">
import type { AuthUser } from '@/types/auth'
import { APP_ROUTES } from '@/constants/navigation'
import { persistClientAuthToken } from '@/utils/auth-token'

definePageMeta({
  layout: 'auth'
})

const { text } = useAppLocale()
const route = useRoute()
const auth = useAuthStore()

const isLoading = ref(true)
const error = ref('')
const exchangeKey = useState<string>('google-oauth-exchange-key', () => '')

const getErrorMessage = (err: unknown) => {
  if (!err || typeof err !== 'object') {
    return 'Google sign-in failed'
  }

  const fetchError = err as {
    data?: { statusMessage?: string, message?: string, detail?: string }
    statusMessage?: string
    message?: string
  }

  return fetchError.data?.statusMessage
    || fetchError.data?.message
    || fetchError.data?.detail
    || fetchError.statusMessage
    || fetchError.message
    || 'Google sign-in failed'
}

const finishGoogleLogin = async () => {
  const code = typeof route.query.code === 'string' ? route.query.code : ''
  const state = typeof route.query.state === 'string' ? route.query.state : ''
  const googleError = typeof route.query.error === 'string' ? route.query.error : ''
  const attemptKey = `${code}:${state}`

  if (googleError) {
    error.value = googleError
    isLoading.value = false
    return
  }

  if (!code || !state) {
    error.value = 'Missing Google OAuth response.'
    isLoading.value = false
    return
  }

  if (exchangeKey.value === attemptKey) {
    return
  }

  exchangeKey.value = attemptKey

  try {
    const response = await $fetch<{ token: string, user: AuthUser, redirectTo: string }>('/api/auth/google/callback', {
      query: { code, state }
    })
    persistClientAuthToken(response.token)
    auth.user = response.user
    auth.isReady = true
    await navigateTo(response.redirectTo || APP_ROUTES.dashboard, { replace: true })
  } catch (err) {
    error.value = getErrorMessage(err)
    exchangeKey.value = ''
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  finishGoogleLogin()
})
</script>

<template>
  <div class="space-y-4 text-center">
    <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-charcoal text-lg font-bold text-white">
      {{ text.auth.providerMark }}
    </div>

    <template v-if="isLoading">
      <h1 class="page-title">{{ text.auth.googleSigningInTitle }}</h1>
      <p class="text-body text-olive">{{ text.auth.googleSigningInDescription }}</p>
      <div class="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-cream border-t-azure" />
    </template>

    <template v-else>
      <h1 class="page-title">{{ text.auth.googleErrorTitle }}</h1>
      <p class="text-body text-orange">{{ error }}</p>
      <NuxtLink class="btn-primary inline-flex px-5 py-2" :to="APP_ROUTES.authLogin">
        {{ text.auth.googleRetry }}
      </NuxtLink>
    </template>
  </div>
</template>

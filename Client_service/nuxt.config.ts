// https://nuxt.com/docs/api/configuration/nuxt-config

const nodeEnv = (globalThis as typeof globalThis & { process?: { env?: Record<string, string | undefined> } }).process?.env ?? {}

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  components: [
    { path: '~/components/shared', pathPrefix: false },
    { path: '~/components/form', pathPrefix: false },
    { path: '~/components/card', pathPrefix: false }
  ],
  modules: [
    '@nuxtjs/tailwindcss',
    '@nuxt/icon',
    '@nuxt/image',
    '@nuxtjs/google-fonts',
    '@pinia/nuxt'
  ],
  devtools: { enabled: true },
  imports: {
    // `srcDir` mặc định là thư mục `app/`. Tiền tố `app/` sai → chỉ utils (hoặc mặc định khác)
    // lên build, không quét được composables/stores ⇒ useAppLocale is not defined.
    dirs: [
      'composables',
      'composables/**',
      'stores',
      'stores/**',
      'utils',
      'utils/**'
    ]
  },
  runtimeConfig: {
    backendApiBaseUrl: nodeEnv.NUXT_BACKEND_API_BASE_URL || 'http://localhost:8000',
    ragServiceBaseUrl: nodeEnv.NUXT_RAG_SERVICE_BASE_URL || 'http://localhost:8000/rag',
    public: {
      backendApiBaseUrl: nodeEnv.NUXT_PUBLIC_BACKEND_API_BASE_URL || 'http://localhost:8000',
      googleClientId: nodeEnv.NUXT_PUBLIC_GOOGLE_CLIENT_ID || nodeEnv.GOOGLE_OAUTH_CLIENT_ID || ''
    }
  },
  tailwindcss: {
    cssPath: '~/assets/css/tailwind-core.css',
    configPath: 'tailwind.config.ts'
  },
  vite: {
    optimizeDeps: {
      include: [
        '@vue/devtools-core',
        '@vue/devtools-kit'
      ]
    }
  },
  googleFonts: {
    families: {
      Inter: [400, 500, 600, 700],
      'Noto Sans': [400, 500, 600, 700]
    },
    subsets: ['latin', 'vietnamese'],
    display: 'swap'
  }
})

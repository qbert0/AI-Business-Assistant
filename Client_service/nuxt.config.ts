// https://nuxt.com/docs/api/configuration/nuxt-config

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
  imports: {
    dirs: [
      '~/composables',
      '~/composables/**',
      '~/stores',
      '~/stores/**',
      '~/utils',
      '~/utils/**',
      'composables',
      'composables/**',
      'stores',
      'stores/**',
      'utils',
      'utils/**',
      'app/composables',
      'app/composables/**',
      'app/stores',
      'app/stores/**',
      'app/utils',
      'app/utils/**'
    ]
  },
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
    backendApiBaseUrl: process.env.NUXT_BACKEND_API_BASE_URL || 'http://localhost:8000',
    public: {
      backendApiBaseUrl: process.env.NUXT_PUBLIC_BACKEND_API_BASE_URL || 'http://localhost:8000',
      googleClientId: process.env.NUXT_PUBLIC_GOOGLE_CLIENT_ID || process.env.GOOGLE_OAUTH_CLIENT_ID || ''
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

// https://nuxt.com/docs/api/configuration/nuxt-config

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  modules: [
    '@nuxtjs/tailwindcss',
    '@nuxt/icon',
    '@nuxt/image',
    '@nuxtjs/google-fonts',
    '@pinia/nuxt'
  ],
  devtools: { enabled: true },
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

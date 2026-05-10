import { useAppLocale } from '@/composables/system/useAppLocale'

export default defineNuxtPlugin(() => {
  const { hydrateLocale } = useAppLocale()
  hydrateLocale()
})

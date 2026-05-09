import { DEFAULT_LOCALE, LOCALE_MESSAGES, SUPPORTED_LOCALES, isAppLocale, type AppLocale, type AppMessages } from '@/locales'

const storageKey = 'ai-business-assistant-locale'

export const useAppLocale = () => {
  const locale = useState<AppLocale>('app-locale', () => DEFAULT_LOCALE)
  const messages = computed(() => LOCALE_MESSAGES[locale.value])

  const text = new Proxy({} as AppMessages, {
    get(_, key: keyof AppMessages) {
      return messages.value[key]
    }
  })

  const setLocale = (nextLocale: AppLocale) => {
    locale.value = nextLocale

    if (import.meta.client) {
      window.localStorage.setItem(storageKey, nextLocale)
      document.documentElement.lang = nextLocale
    }
  }

  const hydrateLocale = () => {
    if (!import.meta.client) {
      return
    }

    const savedLocale = window.localStorage.getItem(storageKey)
    const browserLocale = window.navigator.language.split('-')[0]
    const nextLocale = savedLocale && isAppLocale(savedLocale)
      ? savedLocale
      : isAppLocale(browserLocale)
        ? browserLocale
        : DEFAULT_LOCALE

    setLocale(nextLocale)
  }

  return {
    locale,
    text,
    supportedLocales: SUPPORTED_LOCALES,
    setLocale,
    hydrateLocale
  }
}

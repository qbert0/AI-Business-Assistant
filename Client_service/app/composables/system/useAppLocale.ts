import { DEFAULT_LOCALE, LOCALE_MESSAGES, SUPPORTED_LOCALES, isAppLocale, type AppLocale, type AppMessages } from '@/locales'

const storageKey = 'ai-business-assistant-locale'
const cookieKey = 'ai-business-assistant-locale'

const getBrowserLocale = () => {
  if (!import.meta.client) {
    return undefined
  }

  const browserLocale = window.navigator.language.split('-')[0]
  return isAppLocale(browserLocale) ? browserLocale : undefined
}

const getServerLocale = () => {
  if (!import.meta.server) {
    return undefined
  }

  const acceptLanguage = useRequestHeaders(['accept-language'])['accept-language']
  if (!acceptLanguage) {
    return undefined
  }

  for (const segment of acceptLanguage.split(',')) {
    const candidate = segment.trim().split(';')[0]?.split('-')[0]
    if (candidate && isAppLocale(candidate)) {
      return candidate
    }
  }

  return undefined
}

export const useAppLocale = () => {
  const localeCookie = useCookie<AppLocale | undefined>(cookieKey, {
    sameSite: 'lax',
    path: '/'
  })

  const locale = useState<AppLocale>('app-locale', () => {
    if (localeCookie.value && isAppLocale(localeCookie.value)) {
      return localeCookie.value
    }

    if (import.meta.client) {
      const savedLocale = window.localStorage.getItem(storageKey)
      if (savedLocale && isAppLocale(savedLocale)) {
        localeCookie.value = savedLocale
        return savedLocale
      }

      return getBrowserLocale() ?? DEFAULT_LOCALE
    }

    return getServerLocale() ?? DEFAULT_LOCALE
  })
  const messages = computed(() => LOCALE_MESSAGES[locale.value])

  const text = new Proxy({} as AppMessages, {
    get(_, key: keyof AppMessages) {
      return messages.value[key]
    }
  })

  const syncClientLocale = (nextLocale: AppLocale) => {
    if (!import.meta.client) {
      return
    }

    window.localStorage.setItem(storageKey, nextLocale)
    document.documentElement.lang = nextLocale
  }

  const setLocale = (nextLocale: AppLocale) => {
    if (locale.value === nextLocale) {
      localeCookie.value = nextLocale
      syncClientLocale(nextLocale)
      return
    }

    localeCookie.value = nextLocale
    locale.value = nextLocale
    syncClientLocale(nextLocale)
  }

  const hydrateLocale = () => {
    if (!import.meta.client) {
      return
    }

    const savedLocale = window.localStorage.getItem(storageKey)
    const nextLocale = savedLocale && isAppLocale(savedLocale)
      ? savedLocale
      : localeCookie.value && isAppLocale(localeCookie.value)
        ? localeCookie.value
        : getBrowserLocale() ?? DEFAULT_LOCALE

    if (locale.value === nextLocale) {
      localeCookie.value = nextLocale
      syncClientLocale(nextLocale)
      return
    }

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

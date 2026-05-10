import { EN_MESSAGES } from './en'
import { VI_MESSAGES } from './vi'

export const DEFAULT_LOCALE = 'vi'

export const SUPPORTED_LOCALES = [
  { code: 'vi', label: 'Tiếng Việt', shortLabel: 'VI' },
  { code: 'en', label: 'English', shortLabel: 'EN' }
] as const

export type AppLocale = (typeof SUPPORTED_LOCALES)[number]['code']
type WidenLocaleValue<T> = T extends string
  ? string
  : T extends readonly (infer U)[]
    ? readonly WidenLocaleValue<U>[]
    : T extends object
      ? { readonly [K in keyof T]: WidenLocaleValue<T[K]> }
      : T

type WidenLocaleMessages<T> = { readonly [K in keyof T]: WidenLocaleValue<T[K]> }

export type AppMessages = WidenLocaleMessages<typeof VI_MESSAGES>

export const LOCALE_MESSAGES: Record<AppLocale, AppMessages> = {
  vi: VI_MESSAGES,
  en: EN_MESSAGES
}

export const isAppLocale = (value: string): value is AppLocale =>
  SUPPORTED_LOCALES.some((locale) => locale.code === value)

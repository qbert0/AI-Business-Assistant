export default defineNuxtPlugin(() => {
  const { hydrateLocale } = useAppLocale()
  hydrateLocale()
})

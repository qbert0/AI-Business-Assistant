export default defineNuxtRouteMiddleware(async (to) => {
  const { resolveRouteAccess } = useRbac()
  const access = await resolveRouteAccess(to.path)

  if (!access.allowed) {
    return navigateTo({
      path: '/permission-denied',
      query: { reason: access.reason ?? 'forbidden', from: to.fullPath }
    })
  }
})

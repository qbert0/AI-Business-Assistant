export default defineEventHandler(() => {
  throw createError({
    statusCode: 501,
    statusMessage: 'Google OAuth is not connected to the backend service yet'
  })
})

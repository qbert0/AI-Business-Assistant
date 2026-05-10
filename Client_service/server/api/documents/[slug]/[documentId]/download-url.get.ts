import { AUTH_CLIENT_TOKEN_COOKIE, AUTH_TOKEN_COOKIE } from '../../../../../app/constants/auth'
import { backendFetch } from '../../../../utils/backend'

const getEventToken = (event: Parameters<typeof getCookie>[0]) => {
  const authorization = getHeader(event, 'authorization')
  if (authorization?.startsWith('Bearer ')) {
    return authorization.slice('Bearer '.length)
  }

  return getCookie(event, AUTH_TOKEN_COOKIE) || getCookie(event, AUTH_CLIENT_TOKEN_COOKIE) || null
}

export default defineEventHandler(async (event) => {
  const documentId = getRouterParam(event, 'documentId') || ''
  const token = getEventToken(event)

  if (!documentId || !token) {
    throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })
  }

  const me = await $fetch<{ id: string }>('/api/auth/me', {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })

  return backendFetch<{
    document_id: string
    file_name: string
    download_url: string
    expires_in: number
  }>(event, `/documents/${documentId}/download-url?acting_user_id=${encodeURIComponent(me.id)}&expires=3600`)
})

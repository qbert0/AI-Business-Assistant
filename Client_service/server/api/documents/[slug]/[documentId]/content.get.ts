import { AUTH_CLIENT_TOKEN_COOKIE, AUTH_TOKEN_COOKIE } from '../../../../../app/constants/auth'
import { getBackendBaseUrl } from '../../../../utils/backend'

const getEventToken = (event: Parameters<typeof getCookie>[0]) => {
  const authorization = getHeader(event, 'authorization')
  if (authorization?.startsWith('Bearer ')) {
    return authorization.slice('Bearer '.length)
  }

  return getCookie(event, AUTH_TOKEN_COOKIE) || getCookie(event, AUTH_CLIENT_TOKEN_COOKIE) || null
}

export default defineEventHandler(async (event) => {
  const slug = getRouterParam(event, 'slug') || ''
  const documentId = getRouterParam(event, 'documentId') || ''
  const token = getEventToken(event)

  if (!slug || !documentId || !token) {
    throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })
  }

  const me = await $fetch<{ id: string }>('/api/auth/me', {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })

  const response = await fetch(
    `${getBackendBaseUrl()}/documents/${documentId}/content?acting_user_id=${encodeURIComponent(me.id)}`,
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  )

  if (!response.ok) {
    throw createError({ statusCode: response.status, statusMessage: response.statusText })
  }

  const contentType = response.headers.get('content-type') || 'application/octet-stream'
  const contentDisposition = response.headers.get('content-disposition')
  setHeader(event, 'content-type', contentType)
  if (contentDisposition) {
    setHeader(event, 'content-disposition', contentDisposition)
  }

  const buffer = Buffer.from(await response.arrayBuffer())
  return buffer
})

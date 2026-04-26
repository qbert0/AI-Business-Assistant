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

  return $fetch(`${getBackendBaseUrl()}/documents/${documentId}/preview`, {
    headers: {
      Authorization: `Bearer ${token}`
    },
    query: {
      acting_user_id: me.id
    }
  })
})

import { backendFetch, getBackendUser } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const documentId = getRouterParam(event, 'documentId') || ''

  if (!documentId) {
    throw createError({ statusCode: 400, statusMessage: 'Thiếu mã tài liệu cần xóa.' })
  }

  await backendFetch(event, `/documents/${documentId}?acting_user_id=${encodeURIComponent(user.id)}`, {
    method: 'DELETE'
  })

  return { ok: true }
})

import { z } from 'zod'
import { backendFetch, getBackendUser } from '../../../utils/backend'

const presignSchema = z.object({
  fileName: z.string().min(1),
  contentType: z.string().min(1).optional(),
  expires: z.number().int().min(60).max(86400).optional()
})

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const body = presignSchema.parse(await readBody(event))

  return backendFetch<{
    bucket: string
    object_key: string
    upload_url: string
    source_url: string
    expires_in: number
    content_type?: string | null
  }>(event, `/organizations/${orgId}/documents/presign-upload`, {
    method: 'POST',
    body: {
      acting_user_id: user.id,
      file_name: body.fileName,
      content_type: body.contentType,
      expires: body.expires ?? 3600
    }
  })
})

import { z } from 'zod'
import { backendFetch, getBackendUser, mapDocument } from '../../../utils/backend'

const completeSchema = z.object({
  fileName: z.string().min(1),
  bucket: z.string().min(1),
  objectKey: z.string().min(1),
  sourceUrl: z.string().min(1),
  contentType: z.string().min(1).optional(),
  visibility: z.enum(['public', 'private']).default('private'),
  metadata: z.record(z.string(), z.unknown()).optional()
})

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const body = completeSchema.parse(await readBody(event))

  const document = await backendFetch<any>(event, `/organizations/${orgId}/documents/complete-upload`, {
    method: 'POST',
    body: {
      acting_user_id: user.id,
      file_name: body.fileName,
      bucket: body.bucket,
      object_key: body.objectKey,
      source_url: body.sourceUrl,
      content_type: body.contentType,
      metadata: {
        ...(body.metadata ?? {}),
        visibility: body.visibility,
        folder: body.visibility
      }
    }
  })

  return { document: mapDocument(document) }
})

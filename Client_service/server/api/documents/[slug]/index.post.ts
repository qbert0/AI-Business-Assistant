import { z } from 'zod'
import { backendFetch, getBackendUser, mapDocument } from '../../../utils/backend'

const uploadSchema = z.object({
  title: z.string().min(2).max(160)
})

const createUploadFormData = (fileName: string, data: Uint8Array, contentType?: string, actingUserId?: string) => {
  const formData = new FormData()
  formData.append('acting_user_id', actingUserId || '')
  formData.append('file', new Blob([data], { type: contentType || 'application/octet-stream' }), fileName)
  return formData
}

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const contentType = getHeader(event, 'content-type') || ''

  if (contentType.includes('multipart/form-data')) {
    const parts = await readMultipartFormData(event)
    const filePart = parts?.find((part) => part.name === 'file' && part.filename)

    if (!filePart?.filename) {
      throw createError({ statusCode: 400, statusMessage: 'File is required' })
    }

    const document = await backendFetch<any>(event, `/organizations/${orgId}/documents/upload`, {
      method: 'POST',
      body: createUploadFormData(filePart.filename, filePart.data, filePart.type, user.id)
    })

    return { document: mapDocument(document) }
  }

  const body = uploadSchema.parse(await readBody(event))
  const document = await backendFetch<any>(event, `/organizations/${orgId}/documents`, {
    method: 'POST',
    body: {
      uploaded_by_user_id: user.id,
      file_name: body.title,
      source_url: `minio://documents/${orgId}/${body.title}`,
      metadata: {
        uploaded_by_email: user.email,
        source: 'client-metadata-only'
      }
    }
  })

  return { document: mapDocument(document) }
})

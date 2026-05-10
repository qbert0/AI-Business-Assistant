import { z } from 'zod'
import { backendFetch, getBackendUser, mapDocument } from '../../../utils/backend'

const uploadSchema = z.object({
  title: z.string().min(2).max(160),
  visibility: z.enum(['public', 'private']).default('private')
})

const uploadToPresignedUrl = async (uploadUrl: string, data: Uint8Array, contentType?: string) => {
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    headers: {
      'Content-Type': contentType || 'application/octet-stream'
    },
    body: new Uint8Array(data)
  })

  if (!response.ok) {
    const responseText = await response.text().catch(() => '')
    throw createError({
      statusCode: 502,
      statusMessage: `Storage upload failed: ${response.status} ${responseText || response.statusText}`
    })
  }
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

    const presignedUpload = await backendFetch<any>(event, `/organizations/${orgId}/documents/presign-upload`, {
      method: 'POST',
      body: {
        acting_user_id: user.id,
        file_name: filePart.filename,
        content_type: filePart.type || 'application/octet-stream',
        expires: 3600
      }
    })

    await uploadToPresignedUrl(
      presignedUpload.upload_url,
      filePart.data,
      filePart.type || 'application/octet-stream'
    )

    const document = await backendFetch<any>(event, `/organizations/${orgId}/documents/complete-upload`, {
      method: 'POST',
      body: {
        acting_user_id: user.id,
        file_name: filePart.filename,
        bucket: presignedUpload.bucket,
        object_key: presignedUpload.object_key,
        source_url: presignedUpload.source_url,
        content_type: filePart.type || 'application/octet-stream',
        metadata: {
          uploaded_by_email: user.email,
          source: 'client-presigned-upload',
          visibility: 'private',
          folder: 'private'
        }
      }
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
        source: 'client-metadata-only',
        visibility: body.visibility,
        folder: body.visibility
      }
    }
  })

  return { document: mapDocument(document) }
})

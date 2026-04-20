import { z } from 'zod'
import { requireAuthPayload } from '../../../utils/jwt'
import { mockDocumentsByOrg } from '../../../utils/mockData'

const uploadSchema = z.object({
  title: z.string().min(2).max(160)
})

export default defineEventHandler(async (event) => {
  const payload = requireAuthPayload(event)
  const slug = getRouterParam(event, 'slug') || ''
  const body = uploadSchema.parse(await readBody(event))

  const document = {
    id: `doc-${Date.now()}`,
    organizationSlug: slug,
    title: body.title,
    uploadedBy: payload.email,
    uploadedAt: new Date().toISOString().slice(0, 10),
    chunkCount: 0,
    embeddingModel: 'queued',
    vectorIndex: `${slug}-draft`,
    sourceStorage: `mock://${slug}/${body.title}`,
    status: 'uploaded' as const
  }

  mockDocumentsByOrg[slug] = [document, ...(mockDocumentsByOrg[slug] ?? [])]

  return { document }
})

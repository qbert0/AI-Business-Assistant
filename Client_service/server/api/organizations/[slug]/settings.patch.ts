import { z } from 'zod'
import { backendFetch, getBackendUser } from '../../../utils/backend'

const documentTreeNodeSchema: z.ZodType<any> = z.lazy(() =>
  z.object({
    id: z.string().min(1),
    type: z.enum(['folder', 'file']),
    name: z.string().min(1).max(255),
    parentId: z.string().nullable().optional(),
    documentId: z.string().nullable().optional(),
    children: z.array(documentTreeNodeSchema).optional()
  })
)

const payloadSchema = z.object({
  name: z.string().min(2).max(255).optional(),
  industry: z.string().min(1).max(255).optional(),
  description: z.string().min(1).max(2000).optional(),
  settings: z.object({
    identityKeywords: z.array(z.string().trim().min(1).max(50)).max(3).optional(),
    suggestedQuestions: z.array(z.string().trim().min(1).max(160)).max(3).optional(),
    allowJoinRequests: z.boolean().optional(),
    allowGuestChat: z.boolean().optional(),
    allowGuestDocumentAccess: z.boolean().optional(),
    documentTree: z.array(documentTreeNodeSchema).optional()
  }).optional()
})

interface BackendOrganizationSettingsResponse {
  settings?: {
    identity_keywords?: string[]
    suggested_questions?: string[]
    allow_join_requests?: boolean
    allow_guest_chat?: boolean
    allow_guest_document_access?: boolean
    document_tree?: unknown[]
  }
}

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const body = payloadSchema.parse(await readBody(event))
  const settings = body.settings

  const response = await backendFetch<BackendOrganizationSettingsResponse>(
    event,
    `/organizations/${orgId}/settings?acting_user_id=${encodeURIComponent(user.id)}`,
    {
      method: 'PATCH',
      body: {
        name: body.name,
        industry: body.industry,
        description: body.description,
        settings: settings
          ? {
              identity_keywords: settings.identityKeywords,
              suggested_questions: settings.suggestedQuestions,
              allow_join_requests: settings.allowJoinRequests,
              allow_guest_chat: settings.allowGuestChat,
              allow_guest_document_access: settings.allowGuestDocumentAccess,
              document_tree: settings.documentTree
            }
          : {}
      }
    }
  )

  return {
    settings: {
      identityKeywords: Array.isArray(response.settings?.identity_keywords) ? response.settings.identity_keywords : [],
      suggestedQuestions: Array.isArray(response.settings?.suggested_questions) ? response.settings.suggested_questions : [],
      allowJoinRequests: response.settings?.allow_join_requests !== false,
      allowGuestChat: response.settings?.allow_guest_chat === true,
      allowGuestDocumentAccess: response.settings?.allow_guest_document_access === true,
      documentTree: Array.isArray(response.settings?.document_tree) ? response.settings.document_tree : []
    }
  }
})

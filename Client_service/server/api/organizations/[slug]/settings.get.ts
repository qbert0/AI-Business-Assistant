import { backendFetch, getBackendUser } from '../../../utils/backend'

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
  const response = await backendFetch<BackendOrganizationSettingsResponse>(
    event,
    `/organizations/${orgId}/settings?acting_user_id=${encodeURIComponent(user.id)}`
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

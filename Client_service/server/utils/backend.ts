import { AUTH_TOKEN_COOKIE, AUTH_CLIENT_TOKEN_COOKIE } from '../../app/constants/auth'
import type { OrganizationPermission } from '../../app/constants/rbac'
import type { AuthUser } from '../../app/types/auth'
import type {
  ChatMessage,
  ChatSession,
  KnowledgeDocument,
  OrganizationMember,
  OrganizationSummary,
  PipelineStep,
  SuggestionQuestion
} from '../../app/types/organization'

interface BackendUser {
  id: string
  email: string
  full_name: string
  public_profile?: string | null
  avatar_url?: string | null
}

interface BackendOrganization {
  id: string
  name: string
  industry?: string | null
  description?: string | null
  billing_status?: string | null
}

interface BackendMember {
  id: string
  user_id: string
  organization_id: string
  role: 'admin' | 'user'
  permissions: OrganizationPermission[]
  status: 'active' | 'invited' | 'disabled'
  user: BackendUser
}

interface BackendDocument {
  id: string
  organization_id: string
  uploaded_by_user_id?: string | null
  file_name: string
  source_url: string
  status: string
  chunk_count: number
  embedding_model: string
  vector_index?: string | null
  metadata?: Record<string, unknown>
  created_at: string
}

interface BackendChatSession {
  id: string
  organization_id?: string | null
  title: string
  is_pinned?: boolean
  updated_at: string
}

interface BackendChatMessage {
  id: string
  sender_type: 'user' | 'ai' | 'assistant'
  content: string
  citations?: Array<{ document_id?: string, file_name: string, source_url?: string }>
}

interface BackendPipelineEvent {
  id: string
  stage: string
  status: string
  message?: string | null
}

export const getBackendBaseUrl = () => {
  const config = useRuntimeConfig()
  return (config.backendApiBaseUrl || process.env.NUXT_BACKEND_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')
}

const getEventToken = (event: Parameters<typeof getCookie>[0]) => {
  const authorization = getHeader(event, 'authorization')
  if (authorization?.startsWith('Bearer ')) {
    return authorization.slice('Bearer '.length)
  }

  return getCookie(event, AUTH_TOKEN_COOKIE) || getCookie(event, AUTH_CLIENT_TOKEN_COOKIE) || null
}

export const backendFetch = <T>(event: Parameters<typeof getCookie>[0], path: string, options: Parameters<typeof $fetch<T>>[1] = {}) => {
  const token = getEventToken(event)
  const headers = new Headers(options?.headers as HeadersInit | undefined)

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  return $fetch<T>(`${getBackendBaseUrl()}${path}`, {
    ...options,
    headers
  })
}

export const getBackendUser = (event: Parameters<typeof getCookie>[0]) => backendFetch<BackendUser>(event, '/auth/me')

export const mapUser = (user: BackendUser, role: 'admin' | 'user' = 'user'): AuthUser => ({
  id: user.id,
  name: user.full_name,
  email: user.email,
  title: user.public_profile || 'Workspace member',
  role
})

export const mapOrganization = (
  organization: BackendOrganization,
  role: 'admin' | 'user' = 'user',
  counts: Partial<Pick<OrganizationSummary, 'employeesCount' | 'documentsCount' | 'visits'>> = {}
): OrganizationSummary => ({
  id: organization.id,
  slug: organization.id,
  name: organization.name,
  industry: organization.industry || 'General',
  description: organization.description || '',
  role,
  employeesCount: counts.employeesCount ?? 0,
  documentsCount: counts.documentsCount ?? 0,
  visits: counts.visits ?? 0,
  status: organization.billing_status === 'pending' ? 'pending' : 'active'
})

export const mapMember = (member: BackendMember): OrganizationMember => ({
  id: member.id,
  name: member.user.full_name,
  email: member.user.email,
  department: 'Organization',
  title: member.user.public_profile || 'Employee',
  role: member.role,
  status: member.status === 'disabled' ? 'invited' : member.status,
  permissions: member.permissions
})

const mapDocumentStatus = (status: string): KnowledgeDocument['status'] => {
  if (status === 'completed') {
    return 'indexed'
  }

  if (
    status === 'uploaded'
    || status === 'processing'
    || status === 'chunked'
    || status === 'embedded'
    || status === 'indexing'
    || status === 'indexed'
    || status === 'failed'
    || status === 'cancelled'
  ) {
    return status
  }

  return 'uploaded'
}

export const mapDocument = (document: BackendDocument): KnowledgeDocument => ({
  id: document.id,
  organizationSlug: document.organization_id,
  title: document.file_name,
  uploadedBy: String(document.metadata?.uploaded_by_email || document.uploaded_by_user_id || 'Unknown'),
  uploadedAt: document.created_at.slice(0, 10),
  chunkCount: Number(document.chunk_count || 0),
  embeddingModel: document.embedding_model,
  vectorIndex: document.vector_index || '',
  sourceStorage: document.source_url,
  status: mapDocumentStatus(document.status),
  analysis: (document.metadata?.analysis && typeof document.metadata.analysis === 'object')
    ? document.metadata.analysis as KnowledgeDocument['analysis']
    : undefined
})

export const mapPipelineEvent = (event: BackendPipelineEvent): PipelineStep => ({
  id: event.id,
  name: event.stage,
  description: event.message || 'Pipeline event synced from backend service.',
  owner: 'Server pipeline',
  status: event.status === 'completed' ? 'done' : event.status === 'failed' ? 'queued' : 'running'
})

export const mapChatSession = (session: BackendChatSession): ChatSession => ({
  id: session.id,
  organizationSlug: session.organization_id || 'personal',
  title: session.title,
  updatedAt: session.updated_at.slice(0, 16).replace('T', ' '),
  preview: session.title,
  isPinned: Boolean(session.is_pinned)
})

export const mapChatMessage = (message: BackendChatMessage): ChatMessage => ({
  id: message.id,
  role: message.sender_type === 'user' ? 'user' : 'assistant',
  content: message.content,
  citations: message.citations?.map((citation) => ({
    documentId: citation.document_id || '',
    fileName: citation.file_name,
    sourceUrl: citation.source_url || ''
  })) ?? [],
  searchHits: [],
  status: 'complete',
  activity: null
})

export const mapSuggestions = (questions: string[]): SuggestionQuestion[] =>
  questions.map((question, index) => ({
    id: `suggestion-${index + 1}`,
    question,
    category: 'backend'
  }))

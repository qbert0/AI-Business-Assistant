import type { OrganizationPermission } from '@/constants/rbac'
import type { UserRole } from '../auth'

export interface OrganizationSummary {
  id: string
  slug: string
  name: string
  industry: string
  description: string
  searchKeywords: string[]
  role: UserRole
  employeesCount: number
  documentsCount: number
  visits: number
  status: 'active' | 'pending'
}

export interface OrganizationMember {
  id: string
  name: string
  email: string
  department: string
  title: string
  role: string
  status: 'active' | 'pending_response' | 'invited' | 'declined'
  permissions: OrganizationPermission[]
}

export interface JoinRequest {
  id: string
  organizationName: string
  note: string
  status: 'pending' | 'approved'
}

export interface CompanyForm {
  name: string
  industry: string
  description: string
}

export interface KnowledgeDocument {
  id: string
  organizationSlug: string
  title: string
  visibility: 'public' | 'private'
  folder: 'public' | 'private' | string
  uploadedBy: string
  uploadedAt: string
  chunkCount: number
  embeddingModel: string
  vectorIndex: string
  sourceStorage: string
  status: 'uploaded' | 'processing' | 'chunked' | 'embedded' | 'indexing' | 'indexed' | 'failed' | 'cancelled'
  analysis?: {
    state?: string
    locked?: boolean
    cancel_requested?: boolean
    stage?: string
    message?: string
    error?: string
    progress?: {
      parse?: number
      graph?: number
    }
  }
  chunks?: Array<{
    id: string
    index: number
    content: string
    length?: number
  }>
}

export interface DocumentGraphNode {
  id: string
  label: string
  summary?: string
  labels?: string[]
  x?: number
  y?: number
}

export interface DocumentGraphEdge {
  id: string
  source: string
  target: string
  type?: string
  label?: string
}

export interface DocumentGraph {
  documentId: string
  groupId: string
  nodes: DocumentGraphNode[]
  edges: DocumentGraphEdge[]
  episodes: Array<{
    id: string
    label: string
    source_description?: string
  }>
  counts: {
    nodes: number
    edges: number
    episodes: number
  }
}

export interface DocumentSearchResult {
  id: string
  documentId: string
  documentName: string
  title: string
  content: string
  type: 'fact' | 'node'
  score?: number | null
  sourceNodeId?: string | null
  targetNodeId?: string | null
}

export interface OrganizationDocumentTreeNode {
  id: string
  type: 'folder' | 'file'
  name: string
  parentId: string | null
  documentId?: string | null
  children?: OrganizationDocumentTreeNode[]
}

export interface OrganizationSettingsData {
  identityKeywords: string[]
  suggestedQuestions: string[]
  allowJoinRequests: boolean
  allowGuestChat: boolean
  allowGuestDocumentAccess: boolean
  documentTree: OrganizationDocumentTreeNode[]
}

export interface PipelineStep {
  id: string
  name: string
  description: string
  owner: string
  status: 'done' | 'running' | 'queued'
}

export interface SuggestionQuestion {
  id: string
  question: string
  category: string
}

export interface PopularQuestion {
  question: string
  count: number
}

export interface FeedbackEntry {
  id: string
  organizationSlug: string
  rating: 'positive' | 'negative'
  comment: string
  createdAt: string
}

export interface AnalyticsFeedbackItem {
  id: string
  message_id: string
  session_id: string
  session_title: string
  question: string
  answer_excerpt: string
  rating: 'positive' | 'negative'
  comment: string
  created_at: string | null
}

export interface OrganizationAnalytics {
  organization_id: string
  employee_count: number
  document_count: number
  indexed_document_count: number
  chat_session_count: number
  question_count: number
  popular_questions: string[]
  popular_question_stats: Array<{ question: string, count: number }>
  feedback_summary: {
    total: number
    positive: number
    negative: number
    unresolved: number
  }
  feedback_items: AnalyticsFeedbackItem[]
  sensitive_restrictions: string | null
}

export interface ChatCitation {
  documentId: string
  fileName: string
  sourceUrl: string
}

export interface ChatSearchHit {
  documentId: string
  fileName: string
  documentName?: string | null
  sourceUrl: string
  chunkId?: string | null
  hitType?: string | null
  score?: number | null
}

export interface ChatArtifact {
  kind: 'pdf'
  label: string
  fileName: string
  sourceUrl: string
  downloadUrl?: string | null
  contentType?: string | null
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: ChatCitation[]
  artifacts?: ChatArtifact[]
  searchHits?: ChatSearchHit[]
  status?: 'thinking' | 'streaming' | 'complete' | 'error'
  activity?: string | null
}

export interface ChatSession {
  id: string
  organizationSlug: string
  title: string
  updatedAt: string
  preview: string
  isPinned?: boolean
  isDeletionRestricted?: boolean
}

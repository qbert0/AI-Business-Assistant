import type { OrganizationPermission } from '@/constants/rbac'
import type { UserRole } from '../auth'

export interface OrganizationSummary {
  id: string
  slug: string
  name: string
  industry: string
  description: string
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
  status: 'active' | 'invited'
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

export interface ChatCitation {
  documentId: string
  fileName: string
  sourceUrl: string
}

export interface ChatSearchHit {
  documentId: string
  fileName: string
  sourceUrl: string
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

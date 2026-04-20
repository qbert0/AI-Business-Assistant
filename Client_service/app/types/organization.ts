import type { OrganizationPermission } from '@/constants/rbac'
import type { UserRole } from './auth'

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
  status: 'uploaded' | 'chunked' | 'embedded' | 'indexed'
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

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: string[]
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

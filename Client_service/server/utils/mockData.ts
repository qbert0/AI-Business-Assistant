import type {
  ChatMessage,
  ChatSession,
  FeedbackEntry,
  JoinRequest,
  KnowledgeDocument,
  OrganizationMember,
  OrganizationSummary,
  PipelineStep,
  PopularQuestion,
  SuggestionQuestion
} from '../../app/types/organization'
import type { AuthUser } from '../../app/types/auth'

const adminPermissions = [
  'access_org_settings',
  'chat_advisory',
  'read_documents',
  'view_employees',
  'upload_documents',
  'view_analytics',
  'edit_sensitive_restrictions',
  'delete_chat_sessions'
] as const

const userPermissions = ['chat_advisory', 'read_documents'] as const

export const mockUsers: Array<AuthUser & { password: string }> = [
  {
    id: 'user-1',
    name: 'Nguyen Chau',
    email: 'chau@example.com',
    title: 'Operations Lead',
    role: 'admin',
    password: 'demo123456'
  },
  {
    id: 'user-2',
    name: 'Minh Hoang',
    email: 'minh@example.com',
    title: 'Advisor',
    role: 'user',
    password: 'demo123456'
  }
]

export const mockOrganizations: OrganizationSummary[] = [
  {
    id: 'org-1',
    slug: 'acme-holdings',
    name: 'Acme Holdings',
    industry: 'Finance',
    description: 'Internal knowledge workspace for financial advisory operations.',
    role: 'admin',
    employeesCount: 42,
    documentsCount: 126,
    visits: 1840,
    status: 'active'
  },
  {
    id: 'org-2',
    slug: 'northstar-retail',
    name: 'Northstar Retail',
    industry: 'Retail',
    description: 'SOP, sales policy, and store support chatbot for frontline employees.',
    role: 'user',
    employeesCount: 18,
    documentsCount: 64,
    visits: 920,
    status: 'active'
  },
  {
    id: 'org-3',
    slug: 'zenith-logistics',
    name: 'Zenith Logistics',
    industry: 'Logistics',
    description: 'Workspace invitation is waiting for confirmation.',
    role: 'user',
    employeesCount: 0,
    documentsCount: 0,
    visits: 0,
    status: 'pending'
  }
]

export const mockMembersByOrg: Record<string, OrganizationMember[]> = {
  'acme-holdings': [
    {
      id: 'm-1',
      name: 'Nguyen Chau',
      email: 'chau@example.com',
      department: 'Operations',
      title: 'Operations Lead',
      role: 'admin',
      status: 'active',
      permissions: [...adminPermissions]
    },
    {
      id: 'm-2',
      name: 'Linh Tran',
      email: 'linh@example.com',
      department: 'Compliance',
      title: 'Compliance Manager',
      role: 'admin',
      status: 'active',
      permissions: [...adminPermissions]
    },
    {
      id: 'm-3',
      name: 'Minh Hoang',
      email: 'minh@example.com',
      department: 'Sales',
      title: 'Senior Advisor',
      role: 'user',
      status: 'active',
      permissions: [...userPermissions]
    }
  ],
  'northstar-retail': [
    {
      id: 'm-6',
      name: 'Nguyen Chau',
      email: 'chau@example.com',
      department: 'Operations',
      title: 'Operations Lead',
      role: 'user',
      status: 'active',
      permissions: [...userPermissions]
    },
    {
      id: 'm-4',
      name: 'Ha Le',
      email: 'ha@example.com',
      department: 'Store Ops',
      title: 'Store Manager',
      role: 'admin',
      status: 'active',
      permissions: [...adminPermissions]
    },
    {
      id: 'm-5',
      name: 'Ngoc Bui',
      email: 'ngoc@example.com',
      department: 'Sales',
      title: 'Floor Staff',
      role: 'user',
      status: 'active',
      permissions: [...userPermissions]
    }
  ],
  'zenith-logistics': []
}

export const mockJoinRequests: JoinRequest[] = [
  { id: 'req-1', organizationName: 'BluePeak Insurance', note: 'Needs a chatbot for contract support.', status: 'pending' },
  { id: 'req-2', organizationName: 'Zenith Logistics', note: 'HR invited me to the company workspace.', status: 'approved' }
]

export const mockSuggestions: Record<string, SuggestionQuestion[]> = {
  personal: [
    { id: 's-personal-1', question: 'How do I create a new organization?', category: 'onboarding' },
    { id: 's-personal-2', question: 'Summarize the organizations I have joined.', category: 'workspace' }
  ],
  'acme-holdings': [
    { id: 's-1', question: 'Which income items are taxable?', category: 'payroll' },
    { id: 's-2', question: 'How does quarterly sales bonus work?', category: 'benefits' }
  ],
  'northstar-retail': [
    { id: 's-3', question: 'How are part-time KPIs calculated?', category: 'sales' },
    { id: 's-4', question: 'What is the 24-hour return process?', category: 'SOP' }
  ]
}

export const mockPopularQuestions: Record<string, PopularQuestion[]> = {
  'acme-holdings': [
    { question: 'How is transportation allowance calculated?', count: 124 },
    { question: 'What are the performance bonus conditions?', count: 89 },
    { question: 'What is the contract approval process?', count: 75 }
  ],
  'northstar-retail': [
    { question: 'How are sales KPIs weighted?', count: 64 },
    { question: 'How do employees swap shifts?', count: 41 }
  ]
}

export const mockSessionsByOrg: Record<string, ChatSession[]> = {
  personal: [],
  'acme-holdings': [
    {
      id: 'session-1',
      organizationSlug: 'acme-holdings',
      title: 'Income and benefits',
      updatedAt: '2026-04-13 08:30',
      preview: 'Which income items are taxable?',
      isPinned: true,
      isDeletionRestricted: true
    }
  ],
  'northstar-retail': [
    {
      id: 'session-2',
      organizationSlug: 'northstar-retail',
      title: 'Employee KPI',
      updatedAt: '2026-04-11 10:00',
      preview: 'How are part-time KPIs calculated?'
    }
  ]
}

export const mockMessagesBySession: Record<string, ChatMessage[]> = {
  'session-1': [
    { id: 'c-1', role: 'user', content: 'Which income items are taxable?' },
    {
      id: 'c-2',
      role: 'assistant',
      content: 'Based on the 2026 benefits policy, taxable income includes base salary, performance bonus, and allowances that are not tax-exempt.',
      citations: ['Benefits Policy 2026.pdf', 'Internal Payroll FAQ']
    }
  ],
  'session-2': [
    { id: 'c-3', role: 'user', content: 'How are part-time KPIs calculated?' },
    {
      id: 'c-4',
      role: 'assistant',
      content: 'Part-time KPIs are normalized by actual working hours and the store target group for the registered shift.',
      citations: ['Store Playbook.md']
    }
  ]
}

export const mockFeedback: FeedbackEntry[] = [
  {
    id: 'f-1',
    organizationSlug: 'acme-holdings',
    rating: 'positive',
    comment: 'The answer was grounded and had clear source citations.',
    createdAt: '2026-04-12'
  }
]

export const mockDocumentsByOrg: Record<string, KnowledgeDocument[]> = {
  'acme-holdings': [
    {
      id: 'doc-1',
      organizationSlug: 'acme-holdings',
      title: 'Benefits Policy 2026.pdf',
      uploadedBy: 'Linh Tran',
      uploadedAt: '2026-04-10',
      chunkCount: 84,
      embeddingModel: 'text-embedding-3-large',
      vectorIndex: 'acme-benefits',
      sourceStorage: 's3://mock/acme/benefits-2026.pdf',
      status: 'indexed'
    }
  ],
  'northstar-retail': [
    {
      id: 'doc-2',
      organizationSlug: 'northstar-retail',
      title: 'Store Playbook.md',
      uploadedBy: 'Ha Le',
      uploadedAt: '2026-04-11',
      chunkCount: 46,
      embeddingModel: 'text-embedding-3-small',
      vectorIndex: 'northstar-store',
      sourceStorage: 's3://mock/northstar/store-playbook.md',
      status: 'embedded'
    }
  ]
}

export const mockPipelineByOrg: Record<string, PipelineStep[]> = {
  'acme-holdings': [
    { id: 'step-1', name: 'Document upload', description: 'Store original files with source metadata.', owner: 'Document service', status: 'done' },
    { id: 'step-2', name: 'Chunking', description: 'Split documents into business-aware sections.', owner: 'Chunk worker', status: 'done' },
    { id: 'step-3', name: 'Embedding', description: 'Generate vectors for each approved chunk.', owner: 'Embedding worker', status: 'running' },
    { id: 'step-4', name: 'Elastic indexing', description: 'Sync vectors and metadata to the search index.', owner: 'Vector sync', status: 'queued' }
  ],
  'northstar-retail': [
    { id: 'step-5', name: 'Document upload', description: 'Sync new SOP files from store operations.', owner: 'Document service', status: 'done' }
  ]
}

export const findUserById = (id: string) => mockUsers.find((user) => user.id === id)
export const findUserByEmail = (email: string) => mockUsers.find((user) => user.email === email)
export const stripPassword = ({ password: _password, ...user }: AuthUser & { password: string }) => user

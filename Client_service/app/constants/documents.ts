export const DOCUMENT_FOLDER_IDS = {
  people: 'people',
  operations: 'operations',
  finance: 'finance',
  faq: 'faq'
} as const

export type DocumentFolderId = (typeof DOCUMENT_FOLDER_IDS)[keyof typeof DOCUMENT_FOLDER_IDS]

export const DOCUMENT_FOLDER_KEYWORDS: Record<Exclude<DocumentFolderId, 'faq'>, string[]> = {
  people: ['benefit', 'policy', 'nhan-su', 'nhân sự'],
  operations: ['playbook', 'process', 'sop', 'quy-trinh'],
  finance: ['finance', 'payroll', 'tax', 'tai-chinh']
}

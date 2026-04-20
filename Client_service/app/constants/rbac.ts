export type OrganizationPermission =
  | 'access_org_settings'
  | 'chat_advisory'
  | 'read_documents'
  | 'view_employees'
  | 'view_analytics'
  | 'edit_sensitive_restrictions'
  | 'delete_chat_sessions'
  | 'upload_documents'

export interface PermissionOption {
  id: OrganizationPermission
  label: string
}

export interface OrganizationRoleDefinition {
  name: string
  permissions: OrganizationPermission[]
}

export const PERMISSION_OPTIONS: PermissionOption[] = [
  { id: 'access_org_settings', label: 'Cài đặt tổ chức' },
  { id: 'chat_advisory', label: 'Chat tư vấn' },
  { id: 'read_documents', label: 'Đọc tài liệu' },
  { id: 'view_employees', label: 'Xem nhân viên' },
  { id: 'upload_documents', label: 'Upload tài liệu' },
  { id: 'view_analytics', label: 'Xem phân tích' },
  { id: 'edit_sensitive_restrictions', label: 'Sửa hạn chế nội dung' },
  { id: 'delete_chat_sessions', label: 'Xóa đoạn chat' }
]

export const USER_DEFAULT_PERMISSIONS: OrganizationPermission[] = ['chat_advisory', 'read_documents']

export const ADMIN_DEFAULT_PERMISSIONS: OrganizationPermission[] = [
  'access_org_settings',
  'chat_advisory',
  'read_documents',
  'view_employees',
  'upload_documents',
  'view_analytics',
  'edit_sensitive_restrictions',
  'delete_chat_sessions'
]

export const DEFAULT_ORGANIZATION_ROLES: OrganizationRoleDefinition[] = [
  { name: 'admin', permissions: [...ADMIN_DEFAULT_PERMISSIONS] },
  { name: 'user', permissions: [...USER_DEFAULT_PERMISSIONS] }
]

export const getDefaultPermissionsByRole = (role: string) =>
  role === 'admin' ? ADMIN_DEFAULT_PERMISSIONS : USER_DEFAULT_PERMISSIONS


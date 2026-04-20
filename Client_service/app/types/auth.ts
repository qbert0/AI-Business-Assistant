export type UserRole = 'admin' | 'user'

export interface AuthUser {
  id: string
  name: string
  email: string
  title: string
  role: UserRole
}

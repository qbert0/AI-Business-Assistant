export interface RegisteredDirectoryUser {
  id: string
  name: string
  email: string
  department: string
  title: string
}

export const REGISTERED_DIRECTORY_USERS: RegisteredDirectoryUser[] = [
  {
    id: 'directory-1',
    name: 'Nguyen Chau',
    email: 'chau@example.com',
    department: 'Operations',
    title: 'Operations Lead'
  },
  {
    id: 'directory-2',
    name: 'Linh Tran',
    email: 'linh@example.com',
    department: 'Compliance',
    title: 'Compliance Manager'
  },
  {
    id: 'directory-3',
    name: 'Minh Hoang',
    email: 'minh@example.com',
    department: 'Sales',
    title: 'Senior Advisor'
  },
  {
    id: 'directory-4',
    name: 'An Pham',
    email: 'an@example.com',
    department: 'HR',
    title: 'People Ops'
  },
  {
    id: 'directory-5',
    name: 'Ha Le',
    email: 'ha@example.com',
    department: 'Store Ops',
    title: 'Store Manager'
  },
  {
    id: 'directory-6',
    name: 'Ngoc Bui',
    email: 'ngoc@example.com',
    department: 'Sales',
    title: 'Floor Staff'
  }
]

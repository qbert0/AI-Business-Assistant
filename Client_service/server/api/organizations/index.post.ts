import { z } from 'zod'
import { requireAuthPayload } from '../../utils/jwt'
import { mockMembersByOrg, mockOrganizations } from '../../utils/mockData'

const createOrganizationSchema = z.object({
  name: z.string().min(2).max(80),
  industry: z.string().min(2).max(80),
  description: z.string().min(8).max(500)
})

const createSlug = (value: string) =>
  value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)+/g, '')

export default defineEventHandler(async (event) => {
  const payload = requireAuthPayload(event)
  const body = createOrganizationSchema.parse(await readBody(event))
  const slug = createSlug(body.name)

  if (mockOrganizations.some((organization) => organization.slug === slug)) {
    throw createError({ statusCode: 409, statusMessage: 'Organization already exists' })
  }

  const organization = {
    id: `org-${Date.now()}`,
    slug,
    name: body.name,
    industry: body.industry,
    description: body.description,
    role: 'admin' as const,
    employeesCount: 1,
    documentsCount: 0,
    visits: 0,
    status: 'active' as const
  }

  mockOrganizations.unshift(organization)
  mockMembersByOrg[slug] = [
    {
      id: `m-${Date.now()}`,
      name: payload.email,
      email: payload.email,
      department: 'Founder',
      title: 'Organization Admin',
      role: 'admin',
      status: 'active',
      permissions: [
        'access_org_settings',
        'chat_advisory',
        'read_documents',
        'view_employees',
        'upload_documents',
        'view_analytics',
        'edit_sensitive_restrictions',
        'delete_chat_sessions'
      ]
    }
  ]

  return { organization }
})

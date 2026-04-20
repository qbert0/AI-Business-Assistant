import { z } from 'zod'
import { backendFetch, getBackendUser, mapOrganization } from '../../utils/backend'

const createOrganizationSchema = z.object({
  name: z.string().min(2).max(80),
  industry: z.string().min(2).max(80),
  description: z.string().min(8).max(500)
})

interface BackendOrganization {
  id: string
  name: string
  industry?: string | null
  description?: string | null
  billing_status?: string | null
}

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const body = createOrganizationSchema.parse(await readBody(event))
  const organization = await backendFetch<BackendOrganization>(event, '/organizations', {
    method: 'POST',
    body: {
      ...body,
      owner_user_id: user.id
    }
  })

  return {
    organization: mapOrganization(organization, 'admin', { employeesCount: 1 })
  }
})

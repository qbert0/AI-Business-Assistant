import { backendFetch, getBackendUser, mapMember } from '../../../utils/backend'

interface BackendMember {
  id: string
  user_id: string
  organization_id: string
  role: string
  permissions: any[]
  status: 'active' | 'pending_response' | 'invited' | 'disabled'
  user: {
    id: string
    email: string
    full_name: string
    public_profile?: string | null
  }
}

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const members = await backendFetch<BackendMember[]>(
    event,
    `/organizations/${orgId}/members?acting_user_id=${encodeURIComponent(user.id)}&limit=100`
  )

  return {
    members: members.map(mapMember)
  }
})

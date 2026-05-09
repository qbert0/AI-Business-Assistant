import type { CompanyForm, JoinRequest, OrganizationMember, OrganizationSummary } from '@/types/organization'

export const useApiOrganizations = () => {
  const apiFetch = useApiFetch()

  const list = () => apiFetch<{ organizations: OrganizationSummary[], joinRequests: JoinRequest[] }>('/api/organizations')

  const create = (payload: CompanyForm) =>
    apiFetch<{ organization: OrganizationSummary }>('/api/organizations', {
      method: 'POST',
      body: payload
    })

  const get = (slug: string) => apiFetch<{ organization: OrganizationSummary }>(`/api/organizations/${slug}`)

  const members = (slug: string) =>
    apiFetch<{ members: OrganizationMember[] }>(`/api/organizations/${slug}/members`)

  const addMember = (slug: string, payload: Omit<OrganizationMember, 'id' | 'status'>) =>
    apiFetch<{ member: OrganizationMember }>(`/api/organizations/${slug}/members`, {
      method: 'POST',
      body: payload
    })

  const patchMember = (
    slug: string,
    memberId: string,
    payload: Partial<Pick<OrganizationMember, 'department' | 'title' | 'role' | 'permissions'>>
  ) =>
    apiFetch<{ member: OrganizationMember }>(`/api/organizations/${slug}/members/${memberId}`, {
      method: 'PATCH',
      body: payload
    })

  const removeMember = (slug: string, memberId: string) =>
    apiFetch<{ ok: boolean }>(`/api/organizations/${slug}/members/${memberId}`, {
      method: 'DELETE'
    })

  return {
    list,
    create,
    get,
    members,
    addMember,
    patchMember,
    removeMember
  }
}

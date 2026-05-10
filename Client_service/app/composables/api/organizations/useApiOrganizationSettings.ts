import type { OrganizationSettingsData } from '@/types/organization'

export const useApiOrganizationSettings = () => {
  const apiFetch = useApiFetch()

  const get = (slug: string) =>
    apiFetch<{ settings: OrganizationSettingsData }>(`/api/organizations/${slug}/settings`)

  const update = (
    slug: string,
    payload: Partial<{
      name: string
      industry: string
      description: string
      settings: Partial<OrganizationSettingsData>
    }>
  ) =>
    apiFetch<{ settings: OrganizationSettingsData }>(`/api/organizations/${slug}/settings`, {
      method: 'PATCH',
      body: payload
    })

  return {
    get,
    update
  }
}

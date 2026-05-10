import { getDefaultPermissionsByRole, type OrganizationPermission } from '@/constants/rbac'
import type { CompanyForm, JoinRequest, OrganizationMember, OrganizationSummary } from '@/types/organization'
import { includesSearchTerm, scoreSearchMatch } from '@/utils/search'

export const useOrganizationStore = defineStore('organizations', () => {
  const organizations = ref<OrganizationSummary[]>([])
  const joinRequests = ref<JoinRequest[]>([])
  const membersByOrg = ref<Record<string, OrganizationMember[]>>({})
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const adminOrganizations = computed(() => organizations.value.filter((organization) => organization.role === 'admin'))
  const userOrganizations = computed(() => organizations.value.filter((organization) => organization.role === 'user'))

  const loadOrganizations = async () => {
    isLoading.value = true
    error.value = null

    try {
      const api = useApiOrganizations()
      const response = await api.list()
      organizations.value = response.organizations
      joinRequests.value = response.joinRequests
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Cannot load organizations'
    } finally {
      isLoading.value = false
    }
  }

  const loadMembers = async (slug: string) => {
    const api = useApiOrganizations()
    const response = await api.members(slug)
    membersByOrg.value = {
      ...membersByOrg.value,
      [slug]: response.members
    }
  }

  const getOrganizationBySlug = (slug: string) => organizations.value.find((organization) => organization.slug === slug)
  const getMembers = (slug: string) => membersByOrg.value[slug] ?? []

  const searchOrganizations = (query: string) => {
    if (!query.trim()) {
      return organizations.value
    }

    return organizations.value
      .map((organization) => {
        const searchableText = [
          organization.id,
          organization.name,
          organization.industry,
          organization.description,
          ...(organization.searchKeywords ?? [])
        ].join(' ')

        return {
          organization,
          score: scoreSearchMatch(searchableText, query)
        }
      })
      .filter(({ organization, score }) =>
        score > 0 || includesSearchTerm(
          [
            organization.id,
            organization.name,
            organization.industry,
            organization.description,
            ...(organization.searchKeywords ?? [])
          ].join(' '),
          query
        )
      )
      .sort((left, right) => right.score - left.score || left.organization.name.localeCompare(right.organization.name))
      .map(({ organization }) => organization)
  }

  const createOrganization = async (payload: CompanyForm) => {
    const api = useApiOrganizations()
    const response = await api.create(payload)
    organizations.value = [response.organization, ...organizations.value]
    return response.organization.slug
  }

  const addEmployees = async (
    slug: string,
    payload: { emails: string[], role: string, permissions: OrganizationPermission[] }
  ) => {
    const api = useApiOrganizations()
    const response = await api.addMembers(slug, payload)
    membersByOrg.value = {
      ...membersByOrg.value,
      [slug]: [...response.members, ...getMembers(slug)]
    }
  }

  const removeEmployee = async (slug: string, memberId: string) => {
    const api = useApiOrganizations()
    await api.removeMember(slug, memberId)
    membersByOrg.value = {
      ...membersByOrg.value,
      [slug]: getMembers(slug).filter((member) => member.id !== memberId)
    }
  }

  const updateEmployeeRole = async (slug: string, memberId: string, role: string, permissions = getDefaultPermissionsByRole(role === 'admin' ? 'admin' : 'user')) => {
    const api = useApiOrganizations()
    await api.patchMember(slug, memberId, {
      role,
      permissions: [...permissions]
    })
    membersByOrg.value = {
      ...membersByOrg.value,
      [slug]: getMembers(slug).map((member) =>
        member.id === memberId
          ? { ...member, role, permissions: [...permissions] }
          : member
      )
    }
  }

  const updateEmployeeDetails = async (
    slug: string,
    memberId: string,
    payload: Pick<OrganizationMember, 'department' | 'title' | 'role' | 'permissions'>
  ) => {
    const api = useApiOrganizations()
    await api.patchMember(slug, memberId, payload)
    membersByOrg.value = {
      ...membersByOrg.value,
      [slug]: getMembers(slug).map((member) => (member.id === memberId ? { ...member, ...payload } : member))
    }
  }

  const updateEmployeePermissions = async (slug: string, memberId: string, permissions: OrganizationPermission[]) => {
    const api = useApiOrganizations()
    await api.patchMember(slug, memberId, { permissions })
    membersByOrg.value = {
      ...membersByOrg.value,
      [slug]: getMembers(slug).map((member) => (member.id === memberId ? { ...member, permissions } : member))
    }
  }

  const requestJoinOrganization = async (organizationName: string, note: string) => {
    joinRequests.value = [
      { id: `req-${Date.now()}`, organizationName, note, status: 'pending' },
      ...joinRequests.value
    ]
  }

  return {
    organizations,
    joinRequests,
    membersByOrg,
    adminOrganizations,
    userOrganizations,
    isLoading,
    error,
    loadOrganizations,
    loadMembers,
    getOrganizationBySlug,
    getMembers,
    searchOrganizations,
    createOrganization,
    addEmployees,
    removeEmployee,
    updateEmployeeRole,
    updateEmployeeDetails,
    updateEmployeePermissions,
    requestJoinOrganization
  }
})

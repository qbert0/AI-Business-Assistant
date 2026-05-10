import { REGISTERED_DIRECTORY_USERS } from '@/constants/mock-data'
import { getDefaultPermissionsByRole, type OrganizationPermission } from '@/constants/rbac'
import type { CompanyForm, JoinRequest, OrganizationMember, OrganizationSummary } from '@/types/organization'
import { includesSearchTerm } from '@/utils/search'

import { useApiOrganizations } from '@/composables/api/organizations/useApiOrganizations'

export const useOrganizationStore = defineStore('organizations', () => {
  const api = useApiOrganizations()
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

    return organizations.value.filter((organization) =>
      includesSearchTerm(`${organization.id} ${organization.name} ${organization.industry} ${organization.description}`, query)
    )
  }

  const searchRegisteredUsersByEmail = (emailQuery: string) => {
    if (!emailQuery.trim()) {
      return []
    }

    return REGISTERED_DIRECTORY_USERS.filter((user) => includesSearchTerm(user.email, emailQuery))
  }

  const createOrganization = async (payload: CompanyForm) => {
    const response = await api.create(payload)
    organizations.value = [response.organization, ...organizations.value]
    return response.organization.slug
  }

  const addEmployee = async (slug: string, payload: Omit<OrganizationMember, 'id' | 'status'>) => {
    const response = await api.addMember(slug, payload)
    membersByOrg.value = {
      ...membersByOrg.value,
      [slug]: [response.member, ...getMembers(slug)]
    }
  }

  const removeEmployee = async (slug: string, memberId: string) => {
    await api.removeMember(slug, memberId)
    membersByOrg.value = {
      ...membersByOrg.value,
      [slug]: getMembers(slug).filter((member) => member.id !== memberId)
    }
  }

  const updateEmployeeRole = async (slug: string, memberId: string, role: string, permissions = getDefaultPermissionsByRole(role === 'admin' ? 'admin' : 'user')) => {
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
    await api.patchMember(slug, memberId, payload)
    membersByOrg.value = {
      ...membersByOrg.value,
      [slug]: getMembers(slug).map((member) => (member.id === memberId ? { ...member, ...payload } : member))
    }
  }

  const updateEmployeePermissions = async (slug: string, memberId: string, permissions: OrganizationPermission[]) => {
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
    searchRegisteredUsersByEmail,
    createOrganization,
    addEmployee,
    removeEmployee,
    updateEmployeeRole,
    updateEmployeeDetails,
    updateEmployeePermissions,
    requestJoinOrganization
  }
})

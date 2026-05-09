import type { OrganizationPermission } from '@/constants/rbac'
import type { CompanyForm, OrganizationMember } from '@/types/organization'

export const useOrganization = () => {
  const store = useOrganizationStore()

  return {
    organizations: computed(() => store.organizations),
    adminOrganizations: computed(() => store.adminOrganizations),
    userOrganizations: computed(() => store.userOrganizations),
    joinRequests: computed(() => store.joinRequests),
    isLoading: computed(() => store.isLoading),
    error: computed(() => store.error),
    loadOrganizations: store.loadOrganizations,
    loadMembers: store.loadMembers,
    getOrganizationBySlug: store.getOrganizationBySlug,
    getMembers: store.getMembers,
    searchOrganizations: store.searchOrganizations,
    searchRegisteredUsersByEmail: store.searchRegisteredUsersByEmail,
    addEmployee: (slug: string, payload: Omit<OrganizationMember, 'id' | 'status'>) => store.addEmployee(slug, payload),
    removeEmployee: store.removeEmployee,
    updateEmployeeRole: store.updateEmployeeRole,
    updateEmployeeDetails: store.updateEmployeeDetails,
    updateEmployeePermissions: (slug: string, memberId: string, permissions: OrganizationPermission[]) =>
      store.updateEmployeePermissions(slug, memberId, permissions),
    createOrganization: (payload: CompanyForm) => store.createOrganization(payload),
    requestJoinOrganization: store.requestJoinOrganization
  }
}

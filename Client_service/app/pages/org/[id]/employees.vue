<template>
  <div v-if="organization" class="org-content-page">
    <section class="surface-card org-hero-card space-y-4">
      <div class="section-heading">
        <h1 class="page-title">{{ text.employeesPage.titlePrefix }} {{ organization.name }}</h1>
        <button v-if="isOrganizationAdmin" class="btn-primary" @click="isAddModalOpen = true">{{ text.common.addEmployee }}</button>
      </div>

      <div class="employee-toolbar">
        <input v-model="memberSearch" class="app-input employee-search" :placeholder="text.employeesPage.searchPlaceholder" />
        <div class="pill">{{ text.employeesPage.roleHint }}</div>
      </div>
    </section>

    <section class="surface-card org-table-panel">
      <div class="org-table-scroll overflow-y-visible">
        <table class="app-table mt-3">
          <thead>
            <tr>
              <th>{{ text.employeesPage.nameColumn }}</th>
              <th>{{ text.employeesPage.emailColumn }}</th>
              <th>{{ text.employeesPage.roleColumn }}</th>
              <th>{{ text.employeesPage.statusColumn }}</th>
              <th>{{ text.employeesPage.actionColumn }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="member in paginatedMembers" :key="member.id">
              <td>
                <div>
                  <strong>{{ member.name }}</strong>
                </div>
              </td>
              <td>
                <span class="table-copy text-near">{{ member.email }}</span>
              </td>
              <td>
                <div class="employee-role-cell">
                  <span class="status-badge status-info">{{ roleLabel(member.role) }}</span>
                </div>
              </td>
              <td>
                <span :class="member.status === 'active' ? 'status-badge status-success' : 'status-badge status-warning'">
                  {{ statusLabel(member.status) }}
                </span>
              </td>
              <td>
                <AppPopup
                  :open="activeActionMemberId === member.id"
                  root-class="relative inline-block"
                  content-class="row-action-menu z-[30]"
                  @update:open="handleRowMenuUpdate(member.id, $event)"
                >
                  <template #trigger="{ toggle }">
                    <button class="icon-action-light" :aria-label="text.employeesPage.rowActions" @click="toggle">
                      <Icon name="lucide:more-horizontal" />
                    </button>
                  </template>

                  <template #default>
                    <button class="user-menu-link" @click="openEditEmployee(member)">
                      <Icon name="lucide:pencil" />
                      <span>{{ text.employeesPage.editEmployee }}</span>
                    </button>
                    <button class="user-menu-link danger" @click="deleteMember(member.id)">
                      <Icon name="lucide:trash-2" />
                      <span>{{ text.employeesPage.removeEmployee }}</span>
                    </button>
                  </template>
                </AppPopup>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="!paginatedMembers.length" class="table-copy mt-3">{{ text.employeesPage.empty }}</div>

      <div class="table-footer">
        <p class="table-copy">{{ text.common.page }} {{ currentPage }} / {{ totalPages }}</p>
        <div class="flex gap-2">
          <button class="btn-secondary" :disabled="currentPage === 1" @click="currentPage -= 1">{{ text.common.previous }}</button>
          <button class="btn-secondary" :disabled="currentPage === totalPages" @click="currentPage += 1">{{ text.common.next }}</button>
        </div>
      </div>
    </section>

    <AppPanel v-if="isOrganizationAdmin">
      <template #header-left>
        <h2 class="panel-title">{{ text.organizationSettings.rolesTitle }}</h2>
      </template>

      <template #header-right>
        <button class="btn-primary" @click="openCreateRole">
          <Icon name="lucide:plus" />
          {{ text.organizationSettings.createRole }}
        </button>
      </template>

      <template #content>
        <div class="role-card-grid">
          <article v-for="role in roles" :key="role.name" class="role-card">
            <div class="role-card-header">
              <h3>{{ roleLabel(role.name) }}</h3>
              <button class="icon-action-light" :aria-label="text.organizationSettings.editRole" @click="openEditRole(role)">
                <Icon name="lucide:pencil" />
              </button>
            </div>

            <div class="permission-list mt-3">
              <span v-for="permission in getPermissionOptions(role.permissions)" :key="permission.id" class="permission-chip active">
                {{ permission.label }}
              </span>
            </div>
          </article>
        </div>
      </template>
    </AppPanel>

    <EmployeeModal
      :open="isAddModalOpen"
      :role-options="roles"
      @close="closeAddModal"
      @submit="handleAddEmployees"
    />

    <AppPopup
      :open="Boolean(editingMember)"
      teleport
      content-class="modal-shell"
      backdrop-class="modal-backdrop"
      transition-name="zoom"
      close-on-content-self
      @update:open="handleEditModalUpdate"
    >
      <template #default>
        <section class="modal-card">
          <div class="modal-header">
            <h2 class="panel-title">{{ text.employeesPage.editEmployeeTitle }}</h2>
            <button class="icon-button" type="button" @click="closeEditEmployee">
              <Icon name="lucide:x" />
            </button>
          </div>

          <div class="grid gap-3 md:grid-cols-2">
            <div class="space-y-2 md:col-span-2">
              <label class="field-label">{{ text.employeeModal.role }}</label>
              <select v-model="employeeForm.role" class="app-select">
                <option v-for="role in roles" :key="role.name" :value="role.name">{{ roleLabel(role.name) }}</option>
              </select>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" type="button" @click="closeEditEmployee">{{ text.common.cancel }}</button>
            <button class="btn-primary" type="button" @click="saveEmployeeEdit">{{ text.common.saveChanges }}</button>
          </div>
        </section>
      </template>
    </AppPopup>

    <AppPopup
      :open="isRoleModalOpen"
      teleport
      content-class="modal-shell"
      backdrop-class="modal-backdrop"
      transition-name="zoom"
      close-on-content-self
      @update:open="handleRoleModalUpdate"
    >
      <template #default>
        <section class="modal-card">
          <div class="modal-header">
            <h2 class="panel-title">{{ roleModalTitle }}</h2>
            <button class="icon-button" type="button" @click="closeRoleModal">
              <Icon name="lucide:x" />
            </button>
          </div>

          <div class="space-y-4">
            <div class="space-y-2">
              <label class="field-label">{{ text.organizationSettings.roleName }}</label>
              <input v-model="roleForm.name" class="app-input" :disabled="isBuiltInRole(roleForm.originalName)" />
            </div>

            <div class="space-y-3">
              <p class="field-label">{{ text.organizationSettings.rolePermissions }}</p>
              <div class="permission-grid">
                <label v-for="permission in PERMISSION_OPTIONS" :key="permission.id" class="permission-option">
                  <input v-model="roleForm.permissions" type="checkbox" :value="permission.id" />
                  <span>{{ permission.label }}</span>
                </label>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" type="button" @click="closeRoleModal">{{ text.common.cancel }}</button>
            <button class="btn-primary" type="button" @click="saveRole">{{ text.common.saveChanges }}</button>
          </div>
        </section>
      </template>
    </AppPopup>
  </div>
</template>

<script setup lang="ts">
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
import EmployeeModal from '@/components/form/organization/EmployeeModal.vue'
import {
  DEFAULT_ORGANIZATION_ROLES,
  PERMISSION_OPTIONS,
  type OrganizationPermission,
  type OrganizationRoleDefinition
} from '@/constants/rbac'
import type { OrganizationMember } from '@/types/organization'

definePageMeta({
  layout: 'org',
  orgFullBleed: true
})

const { text } = useAppLocale()

const route = useRoute()
const {
  loadOrganizations,
  loadMembers,
  getOrganizationBySlug,
  getMembers,
  addEmployees,
  removeEmployee,
  updateEmployeeDetails
} = useOrganization()

const slug = computed(() => (route.params.slug ?? route.params.id) as string)
const organization = computed(() => getOrganizationBySlug(slug.value))
const isOrganizationAdmin = computed(() => organization.value?.role === 'admin')
const members = computed(() => getMembers(slug.value))
const memberSearch = ref('')
const isAddModalOpen = ref(false)
const activeActionMemberId = ref<string | null>(null)
const currentPage = ref(1)
const pageSize = 20
const roles = ref<OrganizationRoleDefinition[]>(DEFAULT_ORGANIZATION_ROLES.map((role: OrganizationRoleDefinition) => ({
  name: role.name,
  permissions: [...role.permissions]
})))
const editingMember = ref<OrganizationMember | null>(null)
const employeeForm = reactive({
  role: 'user'
})
const isRoleModalOpen = ref(false)
const roleForm = reactive({
  originalName: '',
  name: '',
  permissions: [] as OrganizationPermission[]
})

const filteredMembers = computed(() =>
  members.value.filter((member: OrganizationMember) =>
    `${member.name} ${member.email} ${member.role} ${member.status}`.toLowerCase().includes(memberSearch.value.trim().toLowerCase())
  )
)
const totalPages = computed(() => Math.max(1, Math.ceil(filteredMembers.value.length / pageSize)))
const paginatedMembers = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredMembers.value.slice(start, start + pageSize)
})
const roleModalTitle = computed(() => roleForm.originalName ? text.organizationSettings.editRole : text.organizationSettings.createRole)

const roleLabel = (role: string) => {
  if (role === 'admin') return text.common.admin
  if (role === 'user') return text.common.employee
  return role
}
const statusLabel = (status: OrganizationMember['status']) => (status === 'active' ? text.common.active : text.common.awaitingResponse)
const isBuiltInRole = (roleName: string) => ['admin', 'user'].includes(roleName)
const getPermissionOptions = (permissions: OrganizationPermission[]) =>
  PERMISSION_OPTIONS.filter((permission: { id: OrganizationPermission, label: string }) => permissions.includes(permission.id))

watch(filteredMembers, () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value
  }
})

watch(memberSearch, () => {
  currentPage.value = 1
})

onMounted(async () => {
  await loadOrganizations()
  await loadMembers(slug.value)
})

const handleAddEmployees = async (payload: {
  emails: string[]
  role: string
  permissions: OrganizationPermission[]
}) => {
  const role = roles.value.find((item: OrganizationRoleDefinition) => item.name === payload.role)
  await addEmployees(slug.value, {
    ...payload,
    permissions: [...(role?.permissions ?? payload.permissions)]
  })
  closeAddModal()
}

const closeAddModal = () => {
  isAddModalOpen.value = false
}

const deleteMember = async (memberId: string) => {
  if (!window.confirm(text.employeesPage.confirmRemove)) {
    return
  }

  await removeEmployee(slug.value, memberId)
  activeActionMemberId.value = null
}

const updateRowMenu = (open: boolean, memberId: string) => {
  activeActionMemberId.value = open ? memberId : null
}

const handleRowMenuUpdate = (memberId: string, open: boolean) => {
  updateRowMenu(open, memberId)
}

const handleEditModalUpdate = (open: boolean) => {
  if (!open) {
    closeEditEmployee()
  }
}

const handleRoleModalUpdate = (open: boolean) => {
  if (!open) {
    closeRoleModal()
  }
}

const openEditEmployee = (member: OrganizationMember) => {
  editingMember.value = member
  employeeForm.role = member.role
  activeActionMemberId.value = null
}

const closeEditEmployee = () => {
  editingMember.value = null
}

const saveEmployeeEdit = async () => {
  if (!editingMember.value) {
    return
  }

  const role = roles.value.find((item: OrganizationRoleDefinition) => item.name === employeeForm.role)
  await updateEmployeeDetails(slug.value, editingMember.value.id, {
    department: editingMember.value.department,
    title: editingMember.value.title,
    role: employeeForm.role,
    permissions: [...(role?.permissions ?? [])]
  })
  closeEditEmployee()
}

const openCreateRole = () => {
  roleForm.originalName = ''
  roleForm.name = ''
  roleForm.permissions = []
  isRoleModalOpen.value = true
}

const openEditRole = (role: OrganizationRoleDefinition) => {
  roleForm.originalName = role.name
  roleForm.name = role.name
  roleForm.permissions = [...role.permissions]
  isRoleModalOpen.value = true
}

const closeRoleModal = () => {
  isRoleModalOpen.value = false
}

const saveRole = async () => {
  const nextName = roleForm.name.trim()
  if (!nextName || !roleForm.permissions.length) {
    return
  }

  const nextRole = {
    name: nextName,
    permissions: [...roleForm.permissions]
  }

  if (!roleForm.originalName) {
    if (!roles.value.some((role: OrganizationRoleDefinition) => role.name === nextName)) {
      roles.value = [...roles.value, nextRole]
    }
    closeRoleModal()
    return
  }

  roles.value = roles.value.map((role: OrganizationRoleDefinition) => (role.name === roleForm.originalName ? nextRole : role))
  await Promise.all(
    members.value
      .filter((member: OrganizationMember) => member.role === roleForm.originalName)
      .map((member: OrganizationMember) =>
        updateEmployeeDetails(slug.value, member.id, {
          department: member.department,
          title: member.title,
          role: nextName,
          permissions: [...nextRole.permissions]
        })
      )
  )
  closeRoleModal()
}
</script>

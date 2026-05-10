<template>
  <AppPopup
    :open="open"
    teleport
    content-class="modal-shell"
    backdrop-class="modal-backdrop"
    transition-name="zoom"
    close-on-content-self
    @update:open="handleOpenUpdate"
  >
    <template #default>
        <section class="modal-card">
          <div class="modal-header">
            <h2 class="panel-title">{{ text.employeeModal.title }}</h2>
            <button class="icon-button" type="button" @click="$emit('close')">
              <Icon name="lucide:x" />
            </button>
          </div>

          <div class="space-y-4">
            <div class="space-y-2">
              <label class="field-label">{{ text.employeeModal.emailSearchLabel }}</label>
              <input v-model="emailSearch" class="app-input" :placeholder="text.employeeModal.emailSearchPlaceholder" />
            </div>

            <div v-if="matchedDirectoryUsers.length" class="space-y-2">
              <button
                v-for="user in matchedDirectoryUsers"
                :key="user.id"
                type="button"
                class="search-result"
                @click="applyRegisteredUser(user)"
              >
                <strong>{{ user.name }}</strong>
                <p>{{ user.email }}</p>
              </button>
            </div>

            <p v-else-if="emailSearch.trim()" class="table-copy">{{ emptyMembersMessage }}</p>

            <div class="grid gap-3 md:grid-cols-2">
              <div class="space-y-2">
                <label class="field-label">{{ text.employeeModal.fullName }}</label>
                <input v-model="form.name" class="app-input" />
              </div>
              <div class="space-y-2">
                <label class="field-label">{{ text.employeeModal.workEmail }}</label>
                <input v-model="form.email" class="app-input" />
              </div>
              <div class="space-y-2">
                <label class="field-label">{{ text.employeeModal.department }}</label>
                <input v-model="form.department" class="app-input" />
              </div>
              <div class="space-y-2">
                <label class="field-label">{{ text.employeeModal.titleLabel }}</label>
                <input v-model="form.title" class="app-input" />
              </div>
              <div class="space-y-2 md:col-span-2">
                <label class="field-label">{{ text.employeeModal.role }}</label>
                <select v-model="form.role" class="app-select">
                  <option v-for="role in roleOptions" :key="role.name" :value="role.name">{{ getRoleLabel(role.name) }}</option>
                </select>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" type="button" @click="$emit('close')">{{ text.common.cancel }}</button>
            <button class="btn-primary" type="button" @click="submit">{{ text.common.addEmployee }}</button>
          </div>
        </section>
    </template>
  </AppPopup>
</template>

<script setup lang="ts">
import { useAppLocale } from '@/composables/system/useAppLocale'
import { getDefaultPermissionsByRole, type OrganizationPermission, type OrganizationRoleDefinition } from '@/constants/rbac'
import type { RegisteredDirectoryUser } from '@/constants/mock-data'

const { text } = useAppLocale()

const props = defineProps<{
  open: boolean
  matchedDirectoryUsers: RegisteredDirectoryUser[]
  emptyMembersMessage: string
  roleOptions?: OrganizationRoleDefinition[]
}>()

const emit = defineEmits<{
  close: []
  search: [value: string]
  submit: [
    payload: {
      name: string
      email: string
      department: string
      title: string
      role: string
      permissions: OrganizationPermission[]
    }
  ]
}>()

const emailSearch = ref('')
const form = reactive({
  name: '',
  email: '',
  department: '',
  title: '',
  role: 'user',
  permissions: [...getDefaultPermissionsByRole('user')]
})

const roleOptions = computed(() => props.roleOptions?.length ? props.roleOptions : [
  { name: 'user', permissions: [...getDefaultPermissionsByRole('user')] },
  { name: 'admin', permissions: [...getDefaultPermissionsByRole('admin')] }
])

const getRoleLabel = (roleName: string) => {
  if (roleName === 'admin') return text.common.admin
  if (roleName === 'user') return text.common.employee
  return roleName
}

watch(emailSearch, (value: string) => {
  emit('search', value)
})

watch(
  () => form.role,
  (role: string) => {
    form.permissions = [...(roleOptions.value.find((item: OrganizationRoleDefinition) => item.name === role)?.permissions ?? getDefaultPermissionsByRole(role))]
  }
)

watch(
  () => props.open,
  (open: boolean) => {
    if (!open) {
      emailSearch.value = ''
      form.name = ''
      form.email = ''
      form.department = ''
      form.title = ''
      form.role = 'user'
      form.permissions = [...getDefaultPermissionsByRole('user')]
    }
  }
)

const applyRegisteredUser = (user: RegisteredDirectoryUser) => {
  form.name = user.name
  form.email = user.email
  form.department = user.department
  form.title = user.title
  emailSearch.value = user.email
}

const handleOpenUpdate = (open: boolean) => {
  if (!open) {
    emit('close')
  }
}

const submit = () => {
  if (!form.name || !form.email) {
    return
  }

  emit('submit', {
    name: form.name,
    email: form.email,
    department: form.department,
    title: form.title,
    role: form.role,
    permissions: form.permissions
  })
}
</script>



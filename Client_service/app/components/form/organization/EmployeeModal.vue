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
            <p class="table-copy">{{ text.employeeModal.selectionHint }}</p>
          </div>

          <div v-if="selectedUsers.length" class="space-y-2">
            <div class="modal-header">
              <p class="field-label">{{ text.employeeModal.selectedTitle }}</p>
              <span class="table-copy">{{ selectedUsers.length }} {{ text.employeeModal.selectedCount }}</span>
            </div>

            <div class="space-y-2">
              <div v-for="user in selectedUsers" :key="user.id" class="search-result">
                <div class="min-w-0">
                  <strong>{{ user.name }}</strong>
                  <p>{{ user.email }}</p>
                </div>
                <button class="icon-action-light shrink-0" type="button" @click="removeSelectedUser(user.id)">
                  <Icon name="lucide:x" />
                </button>
              </div>
            </div>
          </div>

          <div v-if="isSearching" class="table-copy">{{ text.employeeModal.searching }}</div>

          <div v-else-if="searchResults.length" class="space-y-2">
            <button
              v-for="user in searchResults"
              :key="user.id"
              type="button"
              class="search-result"
              @click="selectUser(user)"
            >
              <div class="min-w-0">
                <strong>{{ user.name }}</strong>
                <p>{{ user.email }}</p>
              </div>
              <span class="pill shrink-0">{{ text.employeeModal.pickAction }}</span>
            </button>
          </div>

          <p v-else-if="searchFeedback" class="table-copy">{{ searchFeedback }}</p>

          <div class="space-y-2">
            <label class="field-label">{{ text.employeeModal.role }}</label>
            <select v-model="form.role" class="app-select">
              <option v-for="role in roleOptions" :key="role.name" :value="role.name">{{ getRoleLabel(role.name) }}</option>
            </select>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-secondary" type="button" @click="$emit('close')">{{ text.common.cancel }}</button>
          <button class="btn-primary" type="button" :disabled="!selectedUsers.length" @click="submit">
            {{ text.employeeModal.inviteSelected }}
          </button>
        </div>
      </section>
    </template>
  </AppPopup>
</template>

<script setup lang="ts">
import { useAppLocale } from '@/composables/system/useAppLocale'
import { getDefaultPermissionsByRole, type OrganizationPermission, type OrganizationRoleDefinition } from '@/constants/rbac'

interface SearchUser {
  id: string
  name: string
  email: string
}

const { text } = useAppLocale()
const apiFetch = useApiFetch()

const props = defineProps<{
  open: boolean
  roleOptions?: OrganizationRoleDefinition[]
}>()

const emit = defineEmits<{
  close: []
  submit: [
    payload: {
      emails: string[]
      role: string
      permissions: OrganizationPermission[]
    }
  ]
}>()

const emailSearch = ref('')
const searchResults = ref<SearchUser[]>([])
const selectedUsers = ref<SearchUser[]>([])
const isSearching = ref(false)
const searchFeedback = ref('')
const form = reactive({
  role: 'user',
  permissions: [...getDefaultPermissionsByRole('user')]
})

let searchTimer: ReturnType<typeof setTimeout> | null = null

const roleOptions = computed(() => props.roleOptions?.length ? props.roleOptions : [
  { name: 'user', permissions: [...getDefaultPermissionsByRole('user')] },
  { name: 'admin', permissions: [...getDefaultPermissionsByRole('admin')] }
])

const getRoleLabel = (roleName: string) => {
  if (roleName === 'admin') return text.common.admin
  if (roleName === 'user') return text.common.employee
  return roleName
}

const resetModal = () => {
  emailSearch.value = ''
  searchResults.value = []
  selectedUsers.value = []
  isSearching.value = false
  searchFeedback.value = ''
  form.role = 'user'
  form.permissions = [...getDefaultPermissionsByRole('user')]
}

const selectUser = (user: SearchUser) => {
  if (selectedUsers.value.some((selectedUser) => selectedUser.id === user.id)) {
    return
  }

  selectedUsers.value = [...selectedUsers.value, user]
  emailSearch.value = ''
  searchResults.value = []
  searchFeedback.value = ''
}

const removeSelectedUser = (userId: string) => {
  selectedUsers.value = selectedUsers.value.filter((user) => user.id !== userId)
}

const handleOpenUpdate = (open: boolean) => {
  if (!open) {
    emit('close')
  }
}

const submit = () => {
  if (!selectedUsers.value.length) {
    return
  }

  emit('submit', {
    emails: selectedUsers.value.map((user) => user.email),
    role: form.role,
    permissions: form.permissions
  })
}

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
      resetModal()
    }
  }
)

watch(emailSearch, (value: string) => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }

  const normalizedValue = value.trim()
  if (!normalizedValue) {
    searchResults.value = []
    searchFeedback.value = ''
    isSearching.value = false
    return
  }

  searchTimer = setTimeout(async () => {
    isSearching.value = true
    searchFeedback.value = ''

    try {
      const response = await apiFetch<{ users: SearchUser[] }>(`/api/users?search=${encodeURIComponent(normalizedValue)}`)
      const availableUsers = response.users.filter(
        (user) => !selectedUsers.value.some((selectedUser) => selectedUser.id === user.id)
      )

      searchResults.value = availableUsers
      if (!availableUsers.length) {
        searchFeedback.value = text.employeeModal.emptySearchResult
      }
    } catch {
      searchResults.value = []
      searchFeedback.value = text.employeeModal.searchError
    } finally {
      isSearching.value = false
    }
  }, 250)
})

onBeforeUnmount(() => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
})
</script>

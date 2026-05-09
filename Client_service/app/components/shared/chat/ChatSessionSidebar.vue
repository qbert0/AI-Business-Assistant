<template>
  <aside class="chat-session-sidebar">
    <div class="chat-session-card">
      <AppPopup v-model:open="isContextMenuOpen" root-class="context-switcher" content-class="context-switcher-menu">
        <template #trigger="{ toggle }">
          <button class="context-switcher-trigger" type="button" @click="toggle">
            <span class="avatar-circle" :class="avatarToneClass">{{ initials }}</span>
            <span>
              <small>{{ currentContextLabel }}</small>
              <strong>{{ user.name }}</strong>
            </span>
            <Icon name="lucide:chevron-down" />
          </button>
        </template>

        <template #default>
            <button
              v-for="context in contextOptions"
              :key="context.slug"
              class="context-option"
              :class="{ active: context.slug === slug }"
              type="button"
              @click="selectContext(context.slug)"
            >
              <Icon :name="context.slug === 'personal' ? 'lucide:user-round' : 'lucide:building-2'" />
              <span>{{ context.name }}</span>
            </button>

            <div class="context-menu-divider" />

            <NuxtLink class="context-option" :to="APP_ROUTES.organizations" @click="isContextMenuOpen = false">
              <Icon name="lucide:building-2" />
              <span>{{ text.workspace.manageOrganizations }}</span>
            </NuxtLink>
            <NuxtLink class="context-option" :to="APP_ROUTES.organizationCreate" @click="isContextMenuOpen = false">
              <Icon name="lucide:plus" />
              <span>{{ text.workspace.create }}</span>
            </NuxtLink>
        </template>
      </AppPopup>

      <div class="space-y-2.5">
        <div class="chat-sidebar-heading">
          <h2 class="panel-title">{{ text.chatSidebar.title }}</h2>
          <button class="chat-search-trigger" type="button" @click="isSearchVisible = !isSearchVisible">
            <Icon name="lucide:search" />
          </button>
        </div>
        <input
          v-if="isSearchVisible"
          v-model="searchTerm"
          class="app-input"
          :placeholder="text.chatSidebar.searchPlaceholder"
        />
      </div>

      <div class="session-list">
        <div
          v-for="session in visibleSessions"
          :key="session.id"
          class="session-item"
          :class="{ active: session.id === selectedSessionId }"
        >
          <button class="session-select" type="button" @click="selectSession(session.id)">
            <Icon v-if="session.isPinned" name="lucide:pin" />
            <span class="session-title" :title="session.title">{{ session.title }}</span>
          </button>

          <AppPopup
            :open="activeSessionMenuId === session.id"
            root-class="session-actions-menu"
            content-class="session-menu"
            @update:open="handleSessionMenuUpdate(session.id, $event)"
          >
            <template #trigger="{ toggle }">
              <button class="session-action" type="button" :aria-label="text.chatSidebar.actions" @click.stop="toggle">
                <Icon name="lucide:more-horizontal" />
              </button>
            </template>

            <template #default>
                <button class="session-menu-item" type="button" @click="pinChatSession(session)">
                  <Icon name="lucide:pin" />
                  <span>{{ session.isPinned ? text.chatSidebar.unpin : text.chatSidebar.pin }}</span>
                </button>
                <button class="session-menu-item" type="button" @click="renameChatSession(session)">
                  <Icon name="lucide:pencil" />
                  <span>{{ text.common.rename }}</span>
                </button>
                <button
                  class="session-menu-item danger"
                  type="button"
                  :disabled="session.isDeletionRestricted"
                  :title="session.isDeletionRestricted ? text.chatSidebar.restrictedDelete : undefined"
                  @click="removeChatSession(session)"
                >
                  <Icon name="lucide:trash-2" />
                  <span>{{ text.common.delete }}</span>
                </button>
            </template>
          </AppPopup>
        </div>

        <p v-if="!visibleSessions.length" class="table-copy">{{ text.chatSidebar.empty }}</p>
      </div>

      <button
        v-if="filteredSessions.length > collapsedLimit"
        class="drawer-show-more"
        type="button"
        @click="isExpanded = !isExpanded"
      >
        {{ isExpanded ? text.common.showLess : text.common.showMore }}
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { APP_ROUTES, getContextChatRoute } from '@/constants/navigation'
import type { ChatSession, OrganizationSummary } from '@/types/organization'
import { createInitials, getAvatarToneClass } from '@/utils/avatar'
import { includesSearchTerm } from '@/utils/search'

const { text } = useAppLocale()
const { user } = useAuth()
const router = useRouter()

const props = defineProps<{
  slug: string
  selectedSessionId?: string | null
  sessions: ChatSession[]
  organizations?: OrganizationSummary[]
}>()

const emit = defineEmits<{
  'update:slug': [slug: string]
  'update:selectedSessionId': [sessionId: string | null]
}>()

const { renameSession, togglePinSession, deleteSession } = useChatbot()
const collapsedLimit = 8
const searchTerm = ref('')
const isExpanded = ref(false)
const isSearchVisible = ref(false)
const isContextMenuOpen = ref(false)
const activeSessionMenuId = ref<string | null>(null)

const initials = computed(() => createInitials(user.value.name))
const avatarToneClass = computed(() => getAvatarToneClass(user.value.name))
const contextOptions = computed(() => [
  { slug: 'personal', name: user.value.name || text.navigation.workspace },
  ...(props.organizations ?? []).map((organization: OrganizationSummary) => ({
    slug: organization.slug,
    name: organization.name
  }))
])
const currentContextLabel = computed(() => contextOptions.value.find((context) => context.slug === props.slug)?.name ?? text.navigation.workspace)

const filteredSessions = computed(() => {
  if (!searchTerm.value.trim()) {
    return props.sessions
  }

  return props.sessions.filter((session: ChatSession) => includesSearchTerm(session.title, searchTerm.value))
})
const visibleSessions = computed(() => (isExpanded.value ? filteredSessions.value : filteredSessions.value.slice(0, collapsedLimit)))

const selectContext = async (slug: string) => {
  emit('update:slug', slug)
  emit('update:selectedSessionId', null)
  isContextMenuOpen.value = false
  await router.push(getContextChatRoute(slug))
}

const selectSession = (sessionId: string) => {
  emit('update:selectedSessionId', sessionId)
  activeSessionMenuId.value = null
}

const updateSessionMenu = (open: boolean, sessionId: string) => {
  activeSessionMenuId.value = open ? sessionId : null
}

const handleSessionMenuUpdate = (sessionId: string, open: boolean) => {
  updateSessionMenu(open, sessionId)
}

const pinChatSession = async (session: ChatSession) => {
  await togglePinSession(props.slug, session.id)
  activeSessionMenuId.value = null
}

const renameChatSession = async (session: ChatSession) => {
  const nextTitle = window.prompt(text.chatSidebar.renamePrompt, session.title)?.trim()
  if (!nextTitle) {
    return
  }

  await renameSession(props.slug, session.id, nextTitle)
  activeSessionMenuId.value = null
}

const removeChatSession = async (session: ChatSession) => {
  const isDeleted = await deleteSession(props.slug, session.id)
  if (!isDeleted) {
    window.alert(text.chatSidebar.restrictedDelete)
    return
  }

  if (props.selectedSessionId === session.id) {
    emit('update:selectedSessionId', null)
  }
  activeSessionMenuId.value = null
}

watch(
  () => props.slug,
  () => {
    searchTerm.value = ''
    isExpanded.value = false
    isContextMenuOpen.value = false
    activeSessionMenuId.value = null
  }
)
</script>

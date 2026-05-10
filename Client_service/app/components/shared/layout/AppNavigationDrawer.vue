<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="isAppDrawerOpen" class="drawer-backdrop" @click="closeAppDrawer" />
    </Transition>

    <Transition name="slide">
      <aside v-if="isAppDrawerOpen" class="drawer-panel">
        <div class="drawer-header">
          <NuxtLink to="/" class="brand" @click="closeAppDrawer">
            <span class="brand-mark">{{ text.header.brandMark }}</span>
            <span class="brand-title">{{ text.header.brand }}</span>
          </NuxtLink>
          <button class="drawer-close" @click="closeAppDrawer">
            <Icon name="lucide:x" />
          </button>
        </div>

        <nav class="drawer-list">
          <NuxtLink
            v-for="item in appNavigation"
            :key="item.to"
            :to="item.to"
            class="drawer-link"
            @click="closeAppDrawer"
          >
            <span class="drawer-link-main">
              <Icon :name="item.icon" />
              <strong>{{ item.label }}</strong>
            </span>
          </NuxtLink>
        </nav>

        <div class="drawer-divider" />

        <section class="drawer-chat-section">
          <div class="space-y-2">
            <div class="drawer-chat-header">
              <h2 class="panel-title">{{ text.drawer.chatHistory }}</h2>
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

          <div class="drawer-chat-list">
            <NuxtLink
              v-for="session in visibleSessions"
              :key="session.id"
              :to="getContextChatRoute(session.organizationSlug)"
              class="drawer-chat-item"
              @click="closeAppDrawer"
            >
              <span :title="session.title">{{ session.title }}</span>
            </NuxtLink>

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
        </section>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { useChatbot } from '@/composables/chat/useChatbot'
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
import { useUiState } from '@/composables/system/useUiState'
import { getAppNavigation, getContextChatRoute } from '@/constants/navigation'
import type { ChatSession, OrganizationSummary } from '@/types/organization'
import { includesSearchTerm } from '@/utils/search'

const { text } = useAppLocale()
const { isAppDrawerOpen, closeAppDrawer } = useUiState()
const { organizations } = useOrganization()
const { getSessions } = useChatbot()

const collapsedLimit = 6
const searchTerm = ref('')
const isExpanded = ref(false)
const isSearchVisible = ref(false)

const appNavigation = computed(() => getAppNavigation(text))
const sessions = computed(() => [
  ...getSessions('personal'),
  ...organizations.value.flatMap((organization: OrganizationSummary) => getSessions(organization.slug))
])
const filteredSessions = computed(() => {
  if (!searchTerm.value.trim()) {
    return sessions.value
  }

  return sessions.value.filter((session: ChatSession) => includesSearchTerm(session.title, searchTerm.value))
})
const visibleSessions = computed(() => (isExpanded.value ? filteredSessions.value : filteredSessions.value.slice(0, collapsedLimit)))

watch(organizations, () => {
  searchTerm.value = ''
  isExpanded.value = false
})
</script>

<template>
  <header class="header-shell">
    <div class="header-inner">
      <div class="header-start">
        <button v-if="isAuthenticated" class="menu-trigger" :aria-label="text.drawer.title" @click="toggleAppDrawer">
          <Icon name="lucide:menu" />
        </button>

        <NuxtLink to="/" class="brand">
          <span class="brand-mark">{{ text.header.brandMark }}</span>
          <span class="brand-title">{{ text.header.brand }}</span>
        </NuxtLink>

        <span class="header-page-title">{{ pageTitle }}</span>
      </div >

      <div class=" flex items-center justify-end ">
        <AppPopup
          v-if="isAuthenticated"
          v-model:open="isSearchOpen"
          :root-class="`header-search ${isSearchOpen || organizationSearch ? 'active' : ''}`"
          content-class="header-search-popover"
        >
          <template #trigger="{ toggle }">
            <button class="header-search-button" type="button" :aria-label="text.common.search" @click="openSearch(toggle)">
              <Icon name="lucide:search" />
            </button>
            <input
              ref="searchInput"
              v-model="organizationSearch"
              class="header-search-input"
              :placeholder="text.header.searchPlaceholder"
              @focus="isSearchOpen = true"
              @keydown.enter="submitSearch"
              @keydown.esc="closeSearch"
            />
          </template>

          <template #default>
              <p class="search-popover-title">
                {{ organizationSearch ? text.header.searchHint : text.header.popularSuggestions }}
              </p>

              <button
                v-for="organization in searchSuggestions"
                :key="organization.id"
                class="search-suggestion"
                type="button"
                @mousedown.prevent="goToOrganization(organization.slug)"
              >
                <span>
                  <strong>{{ organization.name }}</strong>
                  <small>{{ organization.id }} · {{ organization.industry }}</small>
                </span>
                <Icon name="lucide:arrow-up-right" />
              </button>

              <p v-if="!searchSuggestions.length" class="search-empty">{{ text.header.noSearchResults }}</p>
          </template>
        </AppPopup>

        <div class="header-user">
          <NuxtLink v-if="isAuthenticated" class="icon-button" :to="APP_ROUTES.notifications" :aria-label="text.common.notifications">
            <Icon name="lucide:bell" />
          </NuxtLink>

          <select v-model="selectedLocale" class="locale-select" @change="handleLocaleChange">
            <option v-for="item in supportedLocales" :key="item.code" :value="item.code">
              {{ item.shortLabel }}
            </option>
          </select>

          <AppPopup v-if="isAuthenticated" v-model:open="isUserMenuOpen" root-class="user-menu-shell" content-class="user-menu">
            <template #trigger="{ toggle }">
              <button class="avatar-trigger" @click="toggle">
                <span class="avatar-circle" :class="avatarToneClass">{{ initials }}</span>
                <!-- <Icon class="avatar-chevron" name="lucide:chevron-down" /> -->
              </button>
            </template>

            <template #default>
                <div class="user-menu-profile">
                  <span class="avatar-circle large" :class="avatarToneClass">{{ initials }}</span>
                  <div>
                    <strong class=" text-black">{{ user.name }}</strong>
                    <p>{{ user.email }}</p>
                  </div>
                </div>

                <div class="user-menu-section">
                  <NuxtLink class="user-menu-link" :to="APP_ROUTES.profile" @click="closeUserMenu">
                    <Icon name="lucide:user-round" />
                    <span>{{ text.header.profile }}</span>
                  </NuxtLink>
                <NuxtLink class="user-menu-link" :to="APP_ROUTES.settingProfile" @click="closeUserMenu">
                    <Icon name="lucide:settings" />
                    <span>{{ text.header.settings }}</span>
                  </NuxtLink>
                  <NuxtLink class="user-menu-link" :to="APP_ROUTES.organizations" @click="closeUserMenu">
                    <Icon name="lucide:building-2" />
                    <span>{{ text.header.organizations }}</span>
                  </NuxtLink>
                  <button class="user-menu-link" @click="closeUserMenu">
                    <Icon name="lucide:repeat" />
                    <span>{{ text.header.switchAccount }}</span>
                  </button>
                </div>

                <div class="user-menu-divider" />

                <button class="user-menu-link danger" @click="handleLogout">
                  <Icon name="lucide:log-out" />
                  <span>{{ text.header.logout }}</span>
                </button>
            </template>
          </AppPopup>
          <NuxtLink v-else class="btn-primary" :to="APP_ROUTES.authLogin">{{ text.header.login }}</NuxtLink>
        </div>
      </div>

    </div>
  </header>
</template>

<script setup lang="ts">
import { useAuth } from '@/composables/auth/useAuth'
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
import { useUiState } from '@/composables/system/useUiState'
import { APP_ROUTES, getOrganizationRoute } from '@/constants/navigation'
import type { AppLocale } from '@/locales'
import { createInitials, getAvatarToneClass } from '@/utils/avatar'

const { text, locale, supportedLocales, setLocale } = useAppLocale()

const route = useRoute()
const router = useRouter()
const { toggleAppDrawer } = useUiState()
const { isAuthenticated, user, logout } = useAuth()
const { searchOrganizations, organizations } = useOrganization()

const organizationSearch = ref(typeof route.query.q === 'string' ? route.query.q : '')
const isUserMenuOpen = ref(false)
const isSearchOpen = ref(false)
const searchInput = ref<HTMLInputElement | null>(null)
const selectedLocale = ref(locale.value)

const initials = computed(() => createInitials(user.value.name))
const avatarToneClass = computed(() => getAvatarToneClass(user.value.name))
const pageTitle = computed(() => {
  const path = route.path
  if (path === APP_ROUTES.home) return text.navigation.home
  if (path.startsWith(APP_ROUTES.dashboard)) return text.workspace.title
  if (path.startsWith(APP_ROUTES.profile)) return text.common.profile
  if (path.startsWith(APP_ROUTES.settings)) return text.common.settings
  if (path.startsWith(APP_ROUTES.notifications)) return text.common.notifications
  if (path.startsWith(APP_ROUTES.organizations)) return text.navigation.organizations
  return text.header.brand
})
const searchSuggestions = computed(() => {
  const results = organizationSearch.value.trim()
    ? searchOrganizations(organizationSearch.value)
    : organizations.value

  return results.slice(0, 5)
})

const openSearch = async (toggle: () => void) => {
  if (isSearchOpen.value && !organizationSearch.value) {
    toggle()
    return
  }

  isSearchOpen.value = true
  await nextTick()
  searchInput.value?.focus()
}

const closeSearch = () => {
  isSearchOpen.value = false
  organizationSearch.value = ''
}

const submitSearch = () => {
  router.push({
    path: APP_ROUTES.organizations,
    query: organizationSearch.value ? { q: organizationSearch.value } : {}
  })
  isSearchOpen.value = false
}

const goToOrganization = (slug: string) => {
  router.push(getOrganizationRoute(slug, 'dashboard'))
  isSearchOpen.value = false
}

const closeUserMenu = () => {
  isUserMenuOpen.value = false
}

const handleLogout = async () => {
  closeUserMenu()
  await logout()
}

const handleLocaleChange = () => {
  setLocale(selectedLocale.value)
}

watch(locale, (value: AppLocale) => {
  selectedLocale.value = value
})

watch(
  () => route.query.q,
  (value: unknown) => {
    organizationSearch.value = typeof value === 'string' ? value : ''
  }
)

watch(
  () => route.fullPath,
  () => {
    closeUserMenu()
    isSearchOpen.value = false
  }
)
</script>

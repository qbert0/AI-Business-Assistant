<template>
  <main class="org-hub-page">
    <section class="surface-card org-hub-container space-y-4">
      <div>
        <p class="eyebrow">{{ text.common.search }}</p>
        <h1 class="page-title">{{ text.organizationSearch.title }}</h1>
        <p class="muted-copy">{{ text.organizationSearch.description }}</p>
      </div>

      <div class="org-filter-search">
        <Icon name="lucide:search" />
        <input v-model="search" :placeholder="text.organizationSearch.searchPlaceholder" />
      </div>
    </section>

    <section class="org-hub-container surface-card space-y-4">
      <div class="section-heading">
        <h2 class="panel-title">{{ text.organizationSearch.resultTitle }}</h2>
        <span class="text-caption text-stone">{{ organizations.length }} {{ text.organizations.resultUnit }}</span>
      </div>

      <div class="org-list">
        <article v-for="organization in organizations" :key="organization.id" class="org-row">
          <div class="org-row-main">
            <div class="org-logo-mark">{{ getInitials(organization.name) }}</div>
            <div class="min-w-0">
              <div class="org-row-title">
                <h3>{{ organization.name }}</h3>
                <span class="status-badge status-info">{{ organization.industry }}</span>
              </div>
              <p>{{ organization.description }}</p>
            </div>
          </div>

          <div class="org-row-actions">
            <NuxtLink class="btn-secondary" :to="getOrganizationPublicRoute(organization.slug)">
              {{ text.organizationPublic.openPublicPage }}
            </NuxtLink>
            <NuxtLink class="btn-primary" :to="getOrganizationPublicRoute(organization.slug)">
              {{ text.organizationPublic.joinTitle }}
            </NuxtLink>
          </div>
        </article>
      </div>

      <p v-if="!organizations.length" class="table-copy">{{ text.organizationSearch.empty }}</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { getOrganizationPublicRoute } from '@/constants/navigation'
import type { OrganizationSummary } from '@/types/organization'

const { text } = useAppLocale()
const route = useRoute()
const router = useRouter()

const search = ref(typeof route.query.id === 'string' ? route.query.id : '')
const organizations = ref<OrganizationSummary[]>([])

const getInitials = (name: string) =>
  name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()

const loadOrganizations = async () => {
  const response = await $fetch<{ organizations: OrganizationSummary[] }>('/api/public/organizations', {
    query: { q: search.value }
  })
  organizations.value = response.organizations
}

watch(search, async (value) => {
  await router.replace({
    path: '/org/search',
    query: value ? { id: value } : {}
  })
  await loadOrganizations()
})

onMounted(loadOrganizations)
</script>

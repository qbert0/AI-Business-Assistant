<template>
  <div v-if="organization" class="org-dashboard-page">
    <section class="org-dashboard-hero">
      <div class="surface-card org-dashboard-hero-primary space-y-3">
        <p class="eyebrow">{{ organization.industry }}</p>
        <h1 class="page-title">{{ organization.name }}</h1>
        <p class="muted-copy">{{ organization.description }}</p>

        <div class="flex flex-wrap gap-2.5">
          <NuxtLink v-if="canChat" class="btn-primary" :to="getOrganizationRoute(organization.slug, 'workspace')">{{ text.workspace.openChat }}</NuxtLink>
          <NuxtLink v-else-if="allowGuestChat" class="btn-primary" :to="getOrganizationRoute(organization.slug, 'chat')">{{ text.organizationPublic.guestEnterCompany }}</NuxtLink>
          <NuxtLink v-if="canViewEmployees" class="btn-primary" :to="getOrganizationRoute(organization.slug, 'employees')">{{ text.organizationDetail.manageEmployees }}</NuxtLink>
          <NuxtLink v-if="canReadDocuments" class="btn-secondary" :to="getOrganizationRoute(organization.slug, 'documents')">{{ text.organizationDetail.documentStore }}</NuxtLink>
          <NuxtLink v-if="canAccessSettings" class="btn-dark" :to="getOrganizationRoute(organization.slug, 'settings')">{{ text.common.settings }}</NuxtLink>
        </div>
      </div>

      <StatsCard class="org-dashboard-stats" :title="text.organizationDetail.statsTitle" :items="stats" />
    </section>

    <section class="org-dashboard-shortcuts">
      <ActionCard v-for="item in shortcuts" :key="item.title" :item="item" />
    </section>

    <section class="org-dashboard-insights">
      <div class="surface-card org-dashboard-panel space-y-3">
        <div class="section-heading">
          <div>
            <p class="section-kicker">{{ text.organizationDetail.popularEyebrow }}</p>
            <h2>{{ text.organizationDetail.popularTitle }}</h2>
          </div>
        </div>

        <div class="space-y-2">
          <div v-for="question in popularQuestions" :key="question.question" class="rounded-xl border border-cream bg-white p-3">
            <div class="flex items-center justify-between gap-3">
              <p>{{ question.question }}</p>
              <strong>{{ question.count }}</strong>
            </div>
          </div>
        </div>
      </div>

      <div class="surface-card org-dashboard-panel space-y-3">
        <div class="section-heading">
          <div>
            <p class="section-kicker">{{ text.organizationDetail.suggestionsEyebrow }}</p>
            <h2>{{ text.organizationDetail.suggestionsTitle }}</h2>
          </div>
        </div>

        <div class="flex flex-wrap gap-2.5">
          <span v-for="item in suggestions" :key="item.id" class="question-chip">{{ item.question }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
import ActionCard from '@/components/card/ActionCard.vue'
import StatsCard from '@/components/card/StatsCard.vue'
import { getOrganizationRoute } from '@/constants/navigation'
import type { OrganizationPermission } from '@/constants/rbac'
import type { ActionCardItem, StatItem } from '@/types/dashboard'
import type { OrganizationSummary, PopularQuestion, SuggestionQuestion } from '@/types/organization'

definePageMeta({
  layout: 'org',
  orgFullBleed: true
})

const { text } = useAppLocale()

const route = useRoute()
const { user, isAuthenticated } = useAuth()
const { loadOrganizations, loadMembers, getOrganizationBySlug, getMembers } = useOrganization()

const slug = computed(() => (route.params.slug ?? route.params.id) as string)
const { data: publicData } = await useFetch<{
  organization: OrganizationSummary
  allowJoinRequests: boolean
  allowGuestChat: boolean
  allowGuestDocumentAccess: boolean
  suggestedQuestions: string[]
}>(() => `/api/public/organizations/${slug.value}`)

const memberOrganization = computed(() => getOrganizationBySlug(slug.value))
const organization = computed(() => memberOrganization.value ?? publicData.value?.organization)
const publicSuggestedQuestions = computed(() => publicData.value?.suggestedQuestions ?? [])
const popularQuestions = computed<PopularQuestion[]>(() =>
  publicSuggestedQuestions.value.map((question, index) => ({
    question,
    count: Math.max(1, publicSuggestedQuestions.value.length - index)
  }))
)
const suggestions = computed<SuggestionQuestion[]>(() =>
  publicSuggestedQuestions.value.map((question, index) => ({
    id: `public-suggestion-${index}`,
    question,
    category: text.organizationDetail.suggestionsTitle
  }))
)
const currentMember = computed(() => getMembers(slug.value).find((member) => member.email === user.value?.email))
const allowGuestChat = computed(() => publicData.value?.allowGuestChat ?? false)
const allowGuestDocumentAccess = computed(() => publicData.value?.allowGuestDocumentAccess ?? false)
const hasPermission = (permission: OrganizationPermission) =>
  memberOrganization.value?.role === 'admin' || currentMember.value?.permissions.includes(permission)
const canChat = computed(() => hasPermission('chat_advisory'))
const canReadDocuments = computed(() => hasPermission('read_documents') || (!memberOrganization.value && allowGuestDocumentAccess.value))
const canViewEmployees = computed(() => hasPermission('view_employees'))
const canAccessSettings = computed(() => hasPermission('access_org_settings'))

const stats = computed<StatItem[]>(() => {
  if (!organization.value) {
    return []
  }

  return [
    { label: text.common.employees, value: String(organization.value.employeesCount), hint: 'bao gồm admin và user' },
    { label: text.common.documents, value: String(organization.value.documentsCount), hint: 'file gốc và tập dữ liệu đã xử lý' },
    { label: text.organizations.visits, value: String(organization.value.visits), hint: '7 ngày gần nhất' }
  ]
})

const shortcuts = computed<ActionCardItem[]>(() => [
  ...(canChat.value ? [{
    title: text.workspace.openChat,
    description: 'Hỏi đáp theo tài liệu đã index trong workspace tổ chức.',
    icon: 'lucide:message-square-text',
    link: getOrganizationRoute(slug.value, 'workspace')
  }] : []),
  ...(canViewEmployees.value ? [{
    title: text.common.employees,
    description: 'Thêm người dùng, role và trạng thái lời mời.',
    icon: 'lucide:user-plus',
    link: getOrganizationRoute(slug.value, 'employees')
  }] : []),
  ...(canReadDocuments.value ? [{
    title: text.common.documents,
    description: 'Upload, chunking, embedding và lưu source link.',
    icon: 'lucide:file-up',
    link: getOrganizationRoute(slug.value, 'documents')
  }] : []),
  ...(hasPermission('view_analytics') ? [{
    title: text.common.analytics,
    description: 'Theo dõi lượt dùng, tài liệu và bộ câu hỏi gợi ý của tổ chức.',
    icon: 'lucide:chart-column-big',
    link: getOrganizationRoute(slug.value, 'analytics')
  }] : [])
])

onMounted(async () => {
  if (!isAuthenticated.value) {
    return
  }

  await loadOrganizations()
  if (memberOrganization.value?.role !== 'admin' && memberOrganization.value) {
    await loadMembers(slug.value)
  }
})
</script>

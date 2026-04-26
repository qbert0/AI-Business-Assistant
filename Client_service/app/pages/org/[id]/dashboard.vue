<template>
  <div v-if="organization" class="space-y-6">
    <section class="two-column-layout">
      <div class="surface-card space-y-3">
        <p class="eyebrow">{{ organization.industry }}</p>
        <h1 class="page-title">{{ organization.name }}</h1>
        <p class="muted-copy">{{ organization.description }}</p>

        <div class="flex flex-wrap gap-2.5">
          <NuxtLink class="btn-primary" :to="getOrganizationRoute(organization.slug, 'employees')">{{ text.organizationDetail.manageEmployees }}</NuxtLink>
          <NuxtLink class="btn-secondary" :to="getOrganizationRoute(organization.slug, 'documents')">{{ text.organizationDetail.documentStore }}</NuxtLink>
          <NuxtLink class="btn-dark" :to="getOrganizationRoute(organization.slug, 'workspace')">{{ text.navigation.workspace }}</NuxtLink>
        </div>
      </div>

      <StatsCard :title="text.organizationDetail.statsTitle" :items="stats" />
    </section>

    <section class="grid gap-3 xl:grid-cols-3">
      <ActionCard v-for="item in shortcuts" :key="item.title" :item="item" />
    </section>

    <section class="grid gap-3 lg:grid-cols-2">
      <div class="surface-card space-y-3">
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

      <div class="surface-card space-y-3">
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
import ActionCard from '@/components/ActionCard.vue'
import StatsCard from '@/components/StatsCard.vue'
import { getOrganizationRoute } from '@/constants/navigation'
import type { ActionCardItem, StatItem } from '@/types/dashboard'

definePageMeta({
  layout: 'org'
})

const { text } = useAppLocale()

const route = useRoute()
const { loadOrganizations, getOrganizationBySlug } = useOrganization()
const { loadContext, getPopularQuestions, getSuggestions } = useChatbot()

const slug = computed(() => (route.params.slug ?? route.params.id) as string)
const organization = computed(() => getOrganizationBySlug(slug.value))
const popularQuestions = computed(() => getPopularQuestions(slug.value))
const suggestions = computed(() => getSuggestions(slug.value))

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
  {
    title: text.common.employees,
    description: 'Thêm người dùng, role và trạng thái lời mời.',
    icon: 'lucide:user-plus',
    link: getOrganizationRoute(slug.value, 'employees')
  },
  {
    title: text.common.documents,
    description: 'Upload, chunking, embedding và lưu source link.',
    icon: 'lucide:file-up',
    link: getOrganizationRoute(slug.value, 'documents')
  },
  {
    title: text.common.pipeline,
    description: 'Multi-agent orchestration, retrieval và rerank.',
    icon: 'lucide:git-branch-plus',
    link: getOrganizationRoute(slug.value, 'pipeline')
  }
])

onMounted(async () => {
  await loadOrganizations()
  await loadContext(slug.value)
})
</script>


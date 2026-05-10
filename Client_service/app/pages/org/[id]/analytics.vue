<template>
  <div v-if="organization" class="org-content-page">
    <section class="surface-card org-hero-card space-y-3">
      <p class="eyebrow">{{ text.analytics.eyebrow }}</p>
      <h1 class="page-title">{{ text.analytics.titlePrefix }} {{ organization.name }}</h1>
      <p class="muted-copy">{{ text.analytics.description }}</p>
    </section>

    <section class="org-metric-grid">
      <article v-for="item in metrics" :key="item.label" class="surface-card analytics-metric-card space-y-2">
        <p class="text-caption text-stone">{{ item.label }}</p>
        <strong class="text-3xl">{{ item.value }}</strong>
        <p class="muted-copy">{{ item.delta }}</p>
      </article>
    </section>

    <section class="surface-card org-table-panel">
      <div class="section-heading">
        <div>
          <p class="section-kicker">{{ text.analytics.questionsEyebrow }}</p>
          <h2>{{ text.analytics.questionsTitle }}</h2>
        </div>
      </div>

      <div class="org-table-scroll mt-3">
        <table class="app-table">
          <thead>
            <tr>
              <th>{{ text.analytics.questionColumn }}</th>
              <th>{{ text.analytics.countColumn }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in popularQuestions" :key="item.question">
              <td>{{ item.question }}</td>
              <td>{{ item.count }}</td>
            </tr>
            <tr v-if="!popularQuestions.length">
              <td colspan="2" class="table-copy">Chua co cau hoi nao duoc ghi nhan.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="surface-card org-table-panel">
      <div class="section-heading">
        <div>
          <p class="section-kicker">Chat feedback</p>
          <h2>Phan hoi can cap nhat tai lieu</h2>
        </div>
        <div class="analytics-feedback-summary">
          <span>{{ feedbackSummary.negative }} can cai thien</span>
          <span>{{ feedbackSummary.positive }} dap ung tot</span>
        </div>
      </div>

      <div class="org-table-scroll mt-3">
        <table class="app-table">
          <thead>
            <tr>
              <th>Cau hoi</th>
              <th>Phan hoi</th>
              <th>Trang thai</th>
              <th>Khac phuc</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in feedbackItems" :key="item.id">
              <td>
                <strong class="analytics-question-cell">{{ item.question || item.session_title }}</strong>
                <p class="table-copy">{{ item.answer_excerpt }}</p>
              </td>
              <td>{{ item.comment || 'Nguoi dung khong de lai ghi chu.' }}</td>
              <td>
                <span :class="item.rating === 'negative' ? 'status-badge status-warning' : 'status-badge status-success'">
                  {{ item.rating === 'negative' ? 'Can bo sung tai lieu' : 'Da dap ung' }}
                </span>
              </td>
              <td>
                <NuxtLink
                  v-if="item.rating === 'negative'"
                  class="table-action"
                  :to="`${getOrganizationRoute(slug, 'documents')}?feedbackQuestion=${encodeURIComponent(item.question || item.session_title)}`"
                >
                  Upload tai lieu
                </NuxtLink>
              </td>
            </tr>
            <tr v-if="!feedbackItems.length">
              <td colspan="4" class="table-copy">Chua co phan hoi tu nguoi dung.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="surface-card space-y-3">
      <div>
        <p class="section-kicker">{{ text.analytics.restrictionEyebrow }}</p>
        <h2 class="panel-title">{{ text.analytics.restrictionTitle }}</h2>
      </div>
      <textarea v-model="sensitiveRestrictions" class="app-textarea" rows="8" :maxlength="3000" :placeholder="text.analytics.restrictionPlaceholder" />
      <div class="org-textarea-actions">
        <p class="table-copy">{{ sensitiveWordCount }} / 500 {{ text.analytics.wordUnit }}</p>
        <div class="org-inline-actions">
          <button class="btn-primary">{{ text.common.openPage }}</button>
          <button class="btn-secondary">{{ text.common.cancel }}</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
import { getOrganizationRoute } from '@/constants/navigation'
import type { OrganizationAnalytics } from '@/types/organization'
definePageMeta({
  layout: 'org',
  orgFullBleed: true
})

const { text } = useAppLocale()

const route = useRoute()
const { loadOrganizations, getOrganizationBySlug } = useOrganization()

const slug = computed(() => (route.params.slug ?? route.params.id) as string)
const organization = computed(() => getOrganizationBySlug(slug.value))
const { data: analyticsData, refresh: refreshAnalytics } = await useFetch<OrganizationAnalytics>(() => `/api/organizations/${slug.value}/analytics`)
const popularQuestions = computed(() => analyticsData.value?.popular_question_stats ?? [])
const feedbackSummary = computed(() => analyticsData.value?.feedback_summary ?? { total: 0, positive: 0, negative: 0, unresolved: 0 })
const feedbackItems = computed(() => analyticsData.value?.feedback_items ?? [])
const sensitiveRestrictions = ref('')
const sensitiveWordCount = computed(() => sensitiveRestrictions.value.trim().split(/\s+/).filter(Boolean).length)

const metrics = computed(() => {
  if (!organization.value) {
    return []
  }

  return [
    { label: 'Luot truy cap', value: String(organization.value.visits), delta: `${analyticsData.value?.chat_session_count ?? 0} doan chat` },
    { label: 'Cau hoi', value: String(analyticsData.value?.question_count ?? 0), delta: `${feedbackSummary.value.negative} phan hoi can xu ly` },
    { label: 'Tai lieu index', value: String(analyticsData.value?.indexed_document_count ?? organization.value.documentsCount), delta: `${analyticsData.value?.document_count ?? organization.value.documentsCount} tai lieu tong cong` }
  ]
})

onMounted(async () => {
  await loadOrganizations()
  await refreshAnalytics()
  sensitiveRestrictions.value = analyticsData.value?.sensitive_restrictions || 'Khong tra loi cac cau hoi yeu cau tiet lo luong ca nhan, du lieu khach hang, ma hop dong, thong tin phap ly chua cong bo hoac cac chinh sach chua duoc phe duyet.'
})
</script>

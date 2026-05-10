<template>
  <div v-if="organization" class="space-y-6">
    <section class="surface-card space-y-3">
      <p class="eyebrow">{{ text.analytics.eyebrow }}</p>
      <h1 class="page-title">{{ text.analytics.titlePrefix }} {{ organization.name }}</h1>
      <p class="muted-copy">{{ text.analytics.description }}</p>
    </section>

    <section class="grid gap-3 md:grid-cols-3">
      <article v-for="item in metrics" :key="item.label" class="surface-card space-y-2">
        <p class="text-caption text-stone">{{ item.label }}</p>
        <strong class="text-3xl">{{ item.value }}</strong>
        <p class="muted-copy">{{ item.delta }}</p>
      </article>
    </section>

    <section class="surface-card">
      <div class="section-heading">
        <div>
          <p class="section-kicker">{{ text.analytics.questionsEyebrow }}</p>
          <h2>{{ text.analytics.questionsTitle }}</h2>
        </div>
      </div>

      <table class="app-table mt-3">
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
        </tbody>
      </table>
    </section>

    <section class="surface-card space-y-3">
      <div>
        <p class="section-kicker">{{ text.analytics.restrictionEyebrow }}</p>
        <h2 class="panel-title">{{ text.analytics.restrictionTitle }}</h2>
      </div>
      <textarea v-model="sensitiveRestrictions" class="app-textarea" rows="8" :maxlength="3000" :placeholder="text.analytics.restrictionPlaceholder" />
      <div class="flex items-center justify-between gap-3">
        <p class="table-copy">{{ sensitiveWordCount }} / 500 {{ text.analytics.wordUnit }}</p>
        <div class="flex gap-2">
          <button class="btn-primary">{{ text.common.openPage }}</button>
          <button class="btn-secondary">{{ text.common.cancel }}</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useChatbot } from '@/composables/chat/useChatbot'
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
definePageMeta({
  layout: 'org'
})

const { text } = useAppLocale()

const route = useRoute()
const { loadOrganizations, getOrganizationBySlug } = useOrganization()
const { loadContext, getPopularQuestions } = useChatbot()

const slug = computed(() => (route.params.slug ?? route.params.id) as string)
const organization = computed(() => getOrganizationBySlug(slug.value))
const popularQuestions = computed(() => getPopularQuestions(slug.value))
const sensitiveRestrictions = ref('Không trả lời các câu hỏi yêu cầu tiết lộ lương cá nhân, dữ liệu khách hàng, mã hợp đồng, thông tin pháp lý chưa công bố hoặc các chính sách chưa được phê duyệt.')
const sensitiveWordCount = computed(() => sensitiveRestrictions.value.trim().split(/\s+/).filter(Boolean).length)

const metrics = computed(() => {
  if (!organization.value) {
    return []
  }

  return [
    { label: 'Lượt truy cập', value: String(organization.value.visits), delta: '+18% so với tuần trước' },
    { label: 'Nhân viên', value: String(organization.value.employeesCount), delta: '4 lời mời đang chờ kích hoạt' },
    { label: 'Tài liệu index', value: String(organization.value.documentsCount), delta: '2 file mới đang embed' }
  ]
})

onMounted(async () => {
  await loadOrganizations()
  await loadContext(slug.value)
})
</script>


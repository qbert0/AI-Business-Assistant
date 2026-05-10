<template>
  <div v-if="organization" class="org-content-page">
    <section class="surface-card org-hero-card space-y-3">
      <p class="eyebrow">{{ text.pipelinePage.eyebrow }}</p>
      <h1 class="page-title">{{ text.pipelinePage.titlePrefix }} {{ organization.name }}</h1>
      <p class="muted-copy">{{ text.pipelinePage.description }}</p>
    </section>

    <section class="org-card-grid-2">
      <article v-for="step in pipeline" :key="step.id" class="surface-card space-y-3">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="section-kicker">{{ step.owner }}</p>
            <h2 class="panel-title">{{ step.name }}</h2>
          </div>
          <span :class="step.status === 'done' ? 'status-badge status-success' : step.status === 'running' ? 'status-badge status-info' : 'status-badge status-warning'">
            {{ step.status }}
          </span>
        </div>
        <p class="muted-copy">{{ step.description }}</p>
      </article>
    </section>

    <section class="surface-dark space-y-3">
      <div>
        <p class="eyebrow">{{ text.pipelinePage.flowEyebrow }}</p>
        <h2 class="text-title font-medium">{{ text.pipelinePage.flowTitle }}</h2>
      </div>
      <ul class="feature-list text-ivory">
        <li v-for="item in text.pipelinePage.flowItems" :key="item">{{ item }}</li>
      </ul>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useDocuments } from '@/composables/documents/useDocuments'
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
definePageMeta({
  layout: 'org',
  orgFullBleed: true
})

const { text } = useAppLocale()

const route = useRoute()
const { loadOrganizations, getOrganizationBySlug } = useOrganization()
const { getPipeline, loadPipeline } = useDocuments()

const slug = computed(() => (route.params.slug ?? route.params.id) as string)
const organization = computed(() => getOrganizationBySlug(slug.value))
const pipeline = computed(() => getPipeline(slug.value))

onMounted(async () => {
  await loadOrganizations()
  await loadPipeline(slug.value)
})
</script>

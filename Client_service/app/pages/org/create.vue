<template>
  <main class="two-column-layout">
    <section class="surface-card space-y-4">
      <div>
        <p class="eyebrow">{{ text.createOrganization.eyebrow }}</p>
        <h1 class="page-title">{{ text.createOrganization.title }}</h1>
        <p class="muted-copy">{{ text.createOrganization.description }}</p>
      </div>

      <div class="space-y-3">
        <input v-model="form.name" class="app-input" :placeholder="text.createOrganization.namePlaceholder" />
        <input v-model="form.industry" class="app-input" :placeholder="text.createOrganization.industryPlaceholder" />
        <textarea v-model="form.description" class="app-textarea" rows="4" :placeholder="text.createOrganization.descriptionPlaceholder" />
      </div>

      <div class="flex flex-wrap gap-2.5">
        <button class="btn-primary" @click="handleCreate">{{ text.createOrganization.submit }}</button>
        <NuxtLink class="btn-secondary" :to="APP_ROUTES.dashboard">{{ text.createOrganization.back }}</NuxtLink>
      </div>
    </section>

    <aside class="surface-dark space-y-3">
      <div>
        <p class="eyebrow">{{ text.createOrganization.scopeEyebrow }}</p>
        <h2 class="text-title font-medium">{{ text.createOrganization.scopeTitle }}</h2>
      </div>
      <ul class="feature-list text-ivory">
        <li v-for="item in text.createOrganization.scopeItems" :key="item">{{ item }}</li>
      </ul>
    </aside>
  </main>
</template>

<script setup lang="ts">
import { APP_ROUTES, getOrganizationRoute } from '@/constants/navigation'

definePageMeta({
  layout: 'org'
})

const { text } = useAppLocale()


const router = useRouter()
const { createOrganization } = useOrganization()

const form = reactive({
  name: '',
  industry: '',
  description: ''
})

const handleCreate = async () => {
  if (!form.name || !form.industry) {
    return
  }

  const slug = await createOrganization(form)
  router.push(getOrganizationRoute(slug, 'dashboard'))
}
</script>


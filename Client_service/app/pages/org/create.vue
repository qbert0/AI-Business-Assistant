<template>
  <main class="org-content-page">
    <section class="two-column-layout">
      <section class="surface-card space-y-4">
        <div>
          <p class="eyebrow">{{ text.createOrganization.eyebrow }}</p>
          <h1 class="page-title">{{ text.createOrganization.title }}</h1>
          <p class="muted-copy">{{ text.createOrganization.description }}</p>
        </div>

        <div class="space-y-3">
          <div class="space-y-1.5">
            <input
              v-model="form.name"
              class="app-input"
              :class="fieldErrorClass(errors.name)"
              :placeholder="text.createOrganization.namePlaceholder"
              @blur="touched.name = true"
            />
            <p class="text-caption text-stone">{{ text.createOrganization.nameHint }}</p>
            <p v-if="errors.name" class="text-caption font-medium text-orange">{{ errors.name }}</p>
          </div>

          <div class="space-y-1.5">
            <input
              v-model="form.industry"
              class="app-input"
              :class="fieldErrorClass(errors.industry)"
              :placeholder="text.createOrganization.industryPlaceholder"
              @blur="touched.industry = true"
            />
            <p class="text-caption text-stone">{{ text.createOrganization.industryHint }}</p>
            <p v-if="errors.industry" class="text-caption font-medium text-orange">{{ errors.industry }}</p>
          </div>

          <div class="space-y-1.5">
            <textarea
              v-model="form.description"
              class="app-textarea"
              :class="fieldErrorClass(errors.description)"
              rows="4"
              :placeholder="text.createOrganization.descriptionPlaceholder"
              @blur="touched.description = true"
            />
            <p class="text-caption text-stone">{{ text.createOrganization.descriptionHint }}</p>
            <p v-if="errors.description" class="text-caption font-medium text-orange">{{ errors.description }}</p>
          </div>
        </div>

        <div class="flex flex-wrap gap-2.5">
          <button class="btn-primary" :disabled="isSubmitting" @click="handleCreate">
            {{ isSubmitting ? text.createOrganization.submitting : text.createOrganization.submit }}
          </button>
          <NuxtLink class="btn-secondary" :to="APP_ROUTES.dashboard">{{ text.createOrganization.back }}</NuxtLink>
        </div>
      </section>

      <aside class="surface-dark space-y-4 overflow-hidden">
        <div class="space-y-2">
          <p class="eyebrow">{{ text.createOrganization.scopeEyebrow }}</p>
          <h2 class="text-title font-medium">{{ text.createOrganization.scopeTitle }}</h2>
          <p class="text-caption leading-[1.5] text-white/72">{{ text.createOrganization.scopeDescription }}</p>
        </div>

        <div class="grid gap-3">
          <div class="rounded-[18px] border border-white/10 bg-white/5 p-4">
            <div class="mb-3 flex items-center justify-between text-micro font-semibold uppercase tracking-[0.12em] text-white/60">
              <span>{{ text.createOrganization.decorativeCardLabel }}</span>
              <span>01</span>
            </div>
            <div class="grid grid-cols-[1.1fr_0.9fr] gap-3">
              <div class="space-y-2">
                <div class="h-3 w-24 rounded-full bg-white/20" />
                <div class="h-3 w-full rounded-full bg-white/10" />
                <div class="h-3 w-4/5 rounded-full bg-white/10" />
              </div>
              <div class="rounded-[14px] bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.28),_rgba(255,255,255,0.04))] p-3">
                <div class="mb-2 h-16 rounded-[10px] bg-black/20" />
                <div class="flex gap-2">
                  <div class="h-2.5 flex-1 rounded-full bg-white/20" />
                  <div class="h-2.5 w-10 rounded-full bg-white/10" />
                </div>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-3 gap-3">
            <div
              v-for="item in text.createOrganization.scopeItems"
              :key="item.title"
              class="rounded-[16px] border border-white/10 bg-white/6 p-3"
            >
              <p class="text-micro font-semibold uppercase tracking-[0.08em] text-white/55">{{ item.kicker }}</p>
              <div class="mt-4 h-10 rounded-[10px] bg-white/8" />
              <p class="mt-3 text-caption font-medium text-white">{{ item.title }}</p>
            </div>
          </div>
        </div>
      </aside>
    </section>
  </main>
</template>

<script setup lang="ts">
import { APP_ROUTES, getOrganizationRoute } from '@/constants/navigation'

definePageMeta({
  layout: 'org',
  orgFullBleed: true
})

const { text } = useAppLocale()


const router = useRouter()
const { createOrganization } = useOrganization()
const isSubmitting = ref(false)

const form = reactive({
  name: '',
  industry: '',
  description: ''
})

const touched = reactive({
  name: false,
  industry: false,
  description: false
})

const normalizeValue = (value: string) => value.trim()

const validationState = computed(() => {
  const name = normalizeValue(form.name)
  const industry = normalizeValue(form.industry)
  const description = normalizeValue(form.description)

  return {
    name: !name
      ? text.value.createOrganization.errors.nameRequired
      : name.length < 8
        ? text.value.createOrganization.errors.nameMin
        : '',
    industry: !industry
      ? text.value.createOrganization.errors.industryRequired
      : industry.length < 3
        ? text.value.createOrganization.errors.industryMin
        : '',
    description: !description
      ? text.value.createOrganization.errors.descriptionRequired
      : description.length < 8
        ? text.value.createOrganization.errors.descriptionMin
        : ''
  }
})

const errors = computed(() => ({
  name: touched.name ? validationState.value.name : '',
  industry: touched.industry ? validationState.value.industry : '',
  description: touched.description ? validationState.value.description : ''
}))

const hasValidationErrors = computed(() => Object.values(validationState.value).some(Boolean))

const fieldErrorClass = (error: string) => (error ? 'border-orange focus:border-orange focus:ring-orange/15' : '')

const handleCreate = async () => {
  touched.name = true
  touched.industry = true
  touched.description = true

  if (hasValidationErrors.value || isSubmitting.value) {
    return
  }

  isSubmitting.value = true

  try {
    const slug = await createOrganization({
      name: normalizeValue(form.name),
      industry: normalizeValue(form.industry),
      description: normalizeValue(form.description)
    })
    router.push(getOrganizationRoute(slug, 'dashboard'))
  } finally {
    isSubmitting.value = false
  }
}
</script>

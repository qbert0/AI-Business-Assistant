<template>
  <main class="grid gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
    <section class="surface-card space-y-4">
      <div class="rounded-[28px] bg-[linear-gradient(135deg,#1f3c88_0%,#39a0ed_100%)] p-6 text-white">
        <span class="avatar-circle large border border-white/20 bg-white/10 text-white" :class="avatarToneClass">{{ initials }}</span>
        <div class="mt-4 space-y-1">
          <h1 class="page-title text-white">{{ user.name }}</h1>
          <p class="text-body text-white/80">{{ user.title }}</p>
          <p class="text-caption text-white/70">{{ user.email }}</p>
        </div>
      </div>
    </section>

    <section class="space-y-4">
      <section class="surface-card space-y-3">
        <p class="eyebrow">{{ text.common.profile }}</p>
        <h2 class="page-title">{{ text.personal.profileTitle }}</h2>
        <p class="muted-copy">{{ text.personal.profileDescription }}</p>
      </section>

      <section class="surface-card public-profile-card">
        <div>
          <h2 class="panel-title">{{ user.name }}</h2>
          <p class="muted-copy">{{ user.title }}</p>
          <p class="table-copy mt-2">{{ user.email }}</p>
        </div>
      </section>
    </section>
  </main>
</template>

<script setup lang="ts">
import { useAuth } from '@/composables/auth/useAuth'
import { useAppLocale } from '@/composables/system/useAppLocale'
import { createInitials, getAvatarToneClass } from '@/utils/avatar'

const { text } = useAppLocale()
const { user } = useAuth()
const initials = computed(() => createInitials(user.value.name))
const avatarToneClass = computed(() => getAvatarToneClass(user.value.name))
</script>

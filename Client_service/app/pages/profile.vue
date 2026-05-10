<template>
  <main class="space-y-4">
    <section class="surface-card space-y-3">
      <p class="eyebrow">{{ text.common.profile }}</p>
      <h1 class="page-title">{{ text.personal.profileTitle }}</h1>
      <p class="muted-copy">{{ text.personal.profileDescription }}</p>
    </section>

    <section class="surface-card public-profile-card">
      <span class="avatar-circle large" :class="avatarToneClass">{{ initials }}</span>
      <div>
        <h2 class="panel-title">{{ user.name }}</h2>
        <p class="muted-copy">{{ user.title }}</p>
        <p class="table-copy">{{ user.email }}</p>
      </div>
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

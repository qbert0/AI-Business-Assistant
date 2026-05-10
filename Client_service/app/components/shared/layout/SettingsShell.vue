<template>
  <main class="settings-shell">
    <aside class="settings-sidebar">
      <div class="settings-account-card">
        <span class="avatar-circle large" :class="avatarToneClass">{{ initials }}</span>
        <div>
          <strong>{{ user.name }}</strong>
          <p>{{ user.email }}</p>
        </div>
      </div>

      <nav class="settings-nav">
        <NuxtLink v-for="item in settingNavigation" :key="item.to" class="settings-nav-link" :to="item.to">
          <Icon :name="item.icon" />
          <span>{{ item.label }}</span>
        </NuxtLink>
      </nav>
    </aside>

    <section class="settings-content">
      <slot />
    </section>
  </main>
</template>

<script setup lang="ts">
import { useAuth } from '@/composables/auth/useAuth'
import { useAppLocale } from '@/composables/system/useAppLocale'
import { getSettingNavigation } from '@/constants/navigation'
import { createInitials, getAvatarToneClass } from '@/utils/avatar'

const { text } = useAppLocale()
const { user } = useAuth()

const settingNavigation = computed(() => getSettingNavigation(text))
const initials = computed(() => createInitials(user.value.name))
const avatarToneClass = computed(() => getAvatarToneClass(user.value.name))
</script>

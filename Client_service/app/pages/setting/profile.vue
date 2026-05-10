<template>
  <!--
    Layout page:
    - Khối 1: heading mô tả màn hình profile setting
    - Khối 2: form chỉnh hồ sơ public
    - Khối 3: nhóm quyền hiển thị thông tin
  -->
  <div class="settings-content">
    <!-- Block 1: page heading -->
    <section class="settings-page-heading">
      <p class="eyebrow">{{ text.settingsNavigation.profile }}</p>
      <h1 class="page-title">{{ text.settingsProfile.title }}</h1>
      <p class="muted-copy">{{ text.settingsProfile.description }}</p>
    </section>

    <!-- Block 2: public profile form -->
    <section class="settings-panel">
      <div class="settings-panel-heading">
        <h2 class="panel-title">{{ text.settingsProfile.publicPreviewTitle }}</h2>
        <NuxtLink class="btn-secondary" :to="APP_ROUTES.profile">{{ text.settingsProfile.viewPublicProfile }}</NuxtLink>
      </div>

      <div class="grid gap-3 md:grid-cols-2">
        <label class="space-y-1">
          <span class="field-label">{{ text.settingsProfile.displayName }}</span>
          <input v-model="form.displayName" class="app-input" />
        </label>
        <label class="space-y-1">
          <span class="field-label">{{ text.settingsProfile.headline }}</span>
          <input v-model="form.headline" class="app-input" />
        </label>
        <label class="space-y-1 md:col-span-2">
          <span class="field-label">{{ text.settingsProfile.bio }}</span>
          <textarea v-model="form.bio" class="app-textarea" rows="4" :placeholder="text.settingsProfile.bioPlaceholder" />
        </label>
      </div>
      <p v-if="profileErrors" class="text-caption text-orange">{{ profileErrors }}</p>
      <button class="btn-primary" @click="saveProfile">{{ text.common.openPage }}</button>
    </section>

    <!-- Block 3: visibility toggles -->
    <section class="settings-panel">
      <h2 class="panel-title">{{ text.settingsProfile.visibilityTitle }}</h2>
      <label v-for="item in text.settingsProfile.visibilityOptions" :key="item" class="settings-toggle-row">
        <span>{{ item }}</span>
        <input type="checkbox" checked />
      </label>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useAuth } from '@/composables/auth/useAuth'
import { useAppLocale } from '@/composables/system/useAppLocale'
import { useSettingsForms } from '@/composables/settings/useSettingsForms'
import { APP_ROUTES } from '@/constants/navigation'

definePageMeta({
  layout: 'settings'
})

const { text } = useAppLocale()
const { user } = useAuth()
const { profileErrors, validateProfile } = useSettingsForms()
const form = reactive({
  displayName: user.value.name,
  headline: user.value.title,
  bio: '',
  showEmail: true,
  showOrganizations: true,
  allowInvites: true
})

const saveProfile = () => {
  validateProfile(form)
}

/*
Layout map

+-----------------------------------------------+
| Heading                                       |
|-----------------------------------------------|
| Public profile form                           |
| display name | headline                       |
| bio                                           |
| save                                          |
|-----------------------------------------------|
| Visibility toggles                            |
+-----------------------------------------------+
*/
</script>

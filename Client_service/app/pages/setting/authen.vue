<template>
  <div class="settings-content">
    <section class="settings-page-heading">
      <p class="eyebrow">{{ text.settingsNavigation.authen }}</p>
      <h1 class="page-title">{{ text.settingsAuthen.title }}</h1>
      <p class="muted-copy">{{ text.settingsAuthen.description }}</p>
    </section>

    <section class="settings-panel">
      <h2 class="panel-title">{{ text.settingsAuthen.passwordTitle }}</h2>
      <div class="grid gap-3 md:grid-cols-2">
        <input v-model="form.currentPassword" class="app-input" type="password" :placeholder="text.settingsAuthen.currentPassword" />
        <input v-model="form.newPassword" class="app-input" type="password" :placeholder="text.settingsAuthen.newPassword" />
      </div>
      <p v-if="passwordErrors" class="text-caption text-orange">{{ passwordErrors }}</p>
      <button class="btn-primary" @click="savePassword">{{ text.settingsAuthen.updatePassword }}</button>
    </section>

    <section class="settings-panel">
      <h2 class="panel-title">{{ text.settingsAuthen.sessionTitle }}</h2>
      <div v-for="item in text.settingsAuthen.sessions" :key="item" class="settings-info-row">
        <span>{{ item }}</span>
        <button class="btn-secondary">{{ text.common.delete }}</button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'settings'
})

const { text } = useAppLocale()
const { passwordErrors, validatePassword } = useSettingsForms()
const form = reactive({
  currentPassword: '',
  newPassword: ''
})

const savePassword = () => {
  validatePassword(form)
}
</script>

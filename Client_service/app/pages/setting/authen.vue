<template>
  <div class="settings-content">
    <section class="settings-page-heading">
      <p class="eyebrow">{{ text.settingsNavigation.authen }}</p>
      <h1 class="page-title">{{ text.settingsAuthen.title }}</h1>
      <p class="muted-copy">{{ text.settingsAuthen.description }}</p>
    </section>

    <section class="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(280px,0.65fr)]">
      <article class="settings-panel space-y-4">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="panel-title">{{ text.settingsAuthen.passwordTitle }}</h2>
            <p class="muted-copy">{{ text.settingsAuthen.passwordDescription }}</p>
          </div>
          <button class="btn-primary" type="button" @click="togglePasswordForm">
            {{ showPasswordForm ? text.settingsAuthen.hidePasswordForm : text.common.change }}
          </button>
        </div>

        <Transition name="fade">
          <div v-if="showPasswordForm" class="space-y-3 overflow-hidden">
            <div class="grid gap-3 md:grid-cols-2">
              <input v-model="form.currentPassword" class="app-input" type="password" :placeholder="text.settingsAuthen.currentPassword" />
              <input v-model="form.newPassword" class="app-input" type="password" :placeholder="text.settingsAuthen.newPassword" />
              <input v-model="form.confirmPassword" class="app-input md:col-span-2" type="password" :placeholder="text.settingsAuthen.confirmPassword" />
            </div>
            <p v-if="passwordErrors" class="text-caption text-orange">{{ passwordErrors }}</p>
            <button class="btn-primary" type="button" @click="savePassword">{{ text.settingsAuthen.changePassword }}</button>
          </div>
        </Transition>
      </article>

      <aside class="space-y-4">
        <article class="settings-panel space-y-2">
          <p class="eyebrow">{{ text.common.settings }}</p>
          <h2 class="panel-title">{{ text.settingsAuthen.passwordCardTitle }}</h2>
          <p class="muted-copy">{{ text.settingsAuthen.passwordCardDescription }}</p>
        </article>

        <article class="settings-panel space-y-2">
          <p class="eyebrow">OAuth</p>
          <h2 class="panel-title">{{ text.settingsAuthen.socialCardTitle }}</h2>
          <p class="muted-copy">{{ text.settingsAuthen.socialCardDescription }}</p>
          <a class="btn-secondary inline-flex" href="/api/auth/google/start">{{ text.auth.google }}</a>
        </article>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'settings'
})

const { text } = useAppLocale()
const { passwordErrors, validatePassword } = useSettingsForms()

const showPasswordForm = ref(false)
const form = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const togglePasswordForm = () => {
  showPasswordForm.value = !showPasswordForm.value
  if (!showPasswordForm.value) {
    form.currentPassword = ''
    form.newPassword = ''
    form.confirmPassword = ''
  }
}

const savePassword = () => {
  if (form.newPassword !== form.confirmPassword) {
    passwordErrors.value = text.settingsAuthen.confirmMismatch
    return
  }

  validatePassword({
    currentPassword: form.currentPassword,
    newPassword: form.newPassword
  })
}
</script>

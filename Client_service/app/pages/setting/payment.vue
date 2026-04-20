<template>
  <div class="settings-content">
    <section class="settings-page-heading">
      <p class="eyebrow">{{ text.settingsNavigation.payment }}</p>
      <h1 class="page-title">{{ text.settingsPayment.title }}</h1>
      <p class="muted-copy">{{ text.settingsPayment.description }}</p>
    </section>

    <section class="settings-panel">
      <div class="settings-panel-heading">
        <div>
          <p class="section-kicker">{{ text.settingsPayment.currentPlan }}</p>
          <h2 class="panel-title">{{ text.settingsPayment.planName }}</h2>
        </div>
        <button class="btn-primary" @click="savePayment">{{ text.settingsPayment.changePlan }}</button>
      </div>
      <p class="muted-copy">{{ text.settingsPayment.planDescription }}</p>
    </section>

    <section class="settings-panel">
      <h2 class="panel-title">{{ text.settingsPayment.methodTitle }}</h2>
      <div class="settings-info-row">
        <input v-model="form.cardLabel" class="app-input" />
        <button class="btn-secondary">{{ text.common.rename }}</button>
      </div>
      <p v-if="paymentErrors" class="text-caption text-orange">{{ paymentErrors }}</p>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'settings'
})

const { text } = useAppLocale()
const { paymentErrors, validatePayment } = useSettingsForms()
const form = reactive({
  plan: 'personal-trial' as const,
  cardLabel: text.settingsPayment.cardLabel
})

const savePayment = () => {
  validatePayment(form)
}
</script>

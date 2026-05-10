<template>
  <main class="landing-page">
    <section class="apple-hero apple-section-dark">
      <div class="apple-hero-copy">
        <p class="eyebrow">{{ text.home.eyebrow }}</p>
        <h1 class="apple-hero-title">{{ text.home.title }}</h1>
        <p class="apple-hero-description">{{ text.home.description }}</p>
        <div class="apple-cta-row">
          <NuxtLink class="btn-primary" :to="APP_ROUTES.authLogin">{{ text.home.loginCta }}</NuxtLink>
          <NuxtLink class="btn-secondary dark" :to="APP_ROUTES.authRegister">{{ text.home.registerCta }}</NuxtLink>
        </div>
      </div>

      <div class="apple-product-frame" :aria-label="text.home.heroAlt">
        <div class="product-chat-window">
          <div class="product-chat-topbar">
            <span />
            <span />
            <span />
          </div>
          <div class="product-chat-message user">{{ text.home.adminFeatures[0] }}</div>
          <div class="product-chat-message assistant">{{ text.home.employeeFeatures[1] }}</div>
        </div>
      </div>
    </section>

    <section class="apple-section-light">
      <div class="apple-feature-copy">
        <p class="eyebrow">{{ text.home.productEyebrow }}</p>
        <h2 class="apple-section-title">{{ text.home.productTitle }}</h2>
        <p class="apple-section-description">{{ text.home.productDescription }}</p>
        <div class="apple-cta-row">
          <NuxtLink class="pill-link" :to="APP_ROUTES.authLogin">{{ text.home.workspaceCta }}</NuxtLink>
          <NuxtLink class="pill-link" :to="APP_ROUTES.organizations">{{ text.home.organizationCta }}</NuxtLink>
        </div>
      </div>
    </section>

    <section class="apple-product-grid">
      <article class="apple-product-card">
        <h3>{{ text.home.adminTitle }}</h3>
        <p>{{ text.home.adminFeatures[1] }}</p>
      </article>
      <article class="apple-product-card dark">
        <h3>{{ text.home.employeeTitle }}</h3>
        <p>{{ text.home.employeeFeatures[2] }}</p>
      </article>
    </section>
  </main>
</template>

<script setup lang="ts">
import { APP_ROUTES } from '@/constants/navigation'
import { useAppLocale } from '@/composables/system/useAppLocale'

const { text } = useAppLocale()
</script>

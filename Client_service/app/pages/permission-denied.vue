<template>
  <main class="content-page-shell">
    <section class="surface-card space-y-3">
      <p class="eyebrow">Permission denied</p>
      <h1 class="page-title">This workspace area is restricted</h1>
      <p class="muted-copy">Your current role is authenticated, but it does not include the permission needed for this page.</p>
      <NuxtLink class="btn-primary" :to="APP_ROUTES.dashboard">Back to workspace</NuxtLink>
    </section>
  </main>
</template>

<script setup lang="ts">
import { APP_ROUTES } from '@/constants/navigation'
</script>

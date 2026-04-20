<script setup lang="ts">
import { APP_ROUTES } from '@/constants/navigation'

definePageMeta({
  layout: 'settings'
})

await navigateTo(APP_ROUTES.settingProfile, { replace: true })
</script>

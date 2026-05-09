<script setup lang="ts">
import { APP_ROUTES } from '@/constants/navigation'

definePageMeta({
  layout: 'settings'
})

/*
Page role:
- Đây là route điều hướng mặc định của khu vực setting
- Không render nội dung riêng
- Tự động chuyển sang tab profile để giữ một entry point rõ ràng

Layout map

/setting
  -> redirect
  -> /setting/profile
*/

await navigateTo(APP_ROUTES.settingProfile, { replace: true })
</script>

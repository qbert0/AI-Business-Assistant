<script setup lang="ts">
import { getOrganizationRoute } from '@/constants/navigation'

const route = useRoute()

/*
Page role:
- Đây là route alias nghiệp vụ cho chat tổ chức
- Không chứa bố cục trực tiếp
- Chuẩn hóa điều hướng về route workspace hiện tại của tổ chức

Layout map

/org/[id]/chat
  -> redirect
  -> /org/[id]/workspace
*/

await navigateTo(getOrganizationRoute((route.params.id ?? route.params.slug) as string, 'workspace'), {
  replace: true
})
</script>

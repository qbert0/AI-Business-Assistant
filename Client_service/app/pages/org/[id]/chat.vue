<script setup lang="ts">
import { getOrganizationRoute } from '@/constants/navigation'

const route = useRoute()

await navigateTo(getOrganizationRoute((route.params.id ?? route.params.slug) as string, 'workspace'), {
  replace: true
})
</script>

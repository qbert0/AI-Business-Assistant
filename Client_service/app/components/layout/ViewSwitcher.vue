<script setup>
    const { viewMode, toggleMode } = useAppMode()
</script>

<template>
  <button 
    @click="toggleMode"
    class="px-3 py-1 text-xs font-semibold rounded-md border border-gray-500 hover:border-gray-300 transition-colors"
  >
    Chế độ: {{ viewMode === 'personal' ? '👤 Cá nhân' : '🏢 Tổ chức' }}
  </button>
</template>
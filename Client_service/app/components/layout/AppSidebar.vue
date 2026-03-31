<script setup>
const { viewMode } = useAppMode()
</script>

<template>
  <aside class="w-64 border-r border-gray-200 bg-white hidden md:flex flex-col">
    <div class="p-4 border-b border-gray-200">
      <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wider">
        {{ viewMode === 'personal' ? 'Cá nhân' : 'Tổ chức' }} Context
      </h2>
    </div>
    <nav class="flex-1 p-4 space-y-2 text-sm">
      <NuxtLink to="/dashboard" class="block px-3 py-2 rounded-md hover:bg-gray-100 text-gray-700 font-medium">
        Tổng quan
      </NuxtLink>
      <NuxtLink to="/organizations/search" class="block px-3 py-2 rounded-md hover:bg-gray-100 text-gray-700 font-medium">
        Khám phá
      </NuxtLink>
      <a href="#" class="block px-3 py-2 rounded-md hover:bg-gray-100 text-gray-700 font-medium">Cài đặt</a>
    </nav>
  </aside>
</template>
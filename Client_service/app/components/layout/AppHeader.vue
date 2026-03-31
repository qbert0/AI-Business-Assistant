<script setup>
// Gọi hàm logout
const { logout } = useAuth()
</script>

<template>
  <header class="bg-[#24292f] text-white px-4 py-3 flex items-center justify-between">
    <div class="flex items-center gap-4">
      <div class="w-8 h-8 bg-white rounded-full flex items-center justify-center text-[#24292f] font-bold">G</div>
      <nav class="hidden md:flex gap-4 text-sm font-semibold">
        <NuxtLink to="/dashboard" class="hover:text-gray-300">Dashboard</NuxtLink>
        <NuxtLink to="/organizations/search" class="hover:text-gray-300">Tìm Tổ chức</NuxtLink>
      </nav>
    </div>

    <div class="flex items-center gap-4">
      <SharedViewSwitcher />
      <button 
        @click="logout" 
        class="text-sm font-medium hover:text-red-400 transition-colors"
      >
        Đăng xuất
      </button>
      <div class="w-8 h-8 bg-gray-600 rounded-full cursor-pointer"></div>
    </div>
  </header>
</template>
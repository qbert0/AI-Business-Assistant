<script setup>
const { viewMode } = useAppMode()
</script>

<template>
  <div>
    <div class="border-b border-gray-200 pb-4 mb-6">
      <h1 class="text-2xl font-semibold">Dashboard</h1>
      <p class="text-gray-500 mt-1">
        Bạn đang xem dữ liệu dưới tư cách: 
        <strong class="text-black">{{ viewMode === 'personal' ? 'Cá nhân' : 'Tổ chức' }}</strong>
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div class="bg-white p-6 rounded-md border border-gray-200 shadow-sm h-48">
        </div>
      <div class="bg-white p-6 rounded-md border border-gray-200 shadow-sm h-48">
        </div>
      <div class="bg-white p-6 rounded-md border border-gray-200 shadow-sm h-48">
        </div>
    </div>
  </div>
</template>
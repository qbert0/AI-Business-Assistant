<script setup>
// Nhận object error từ Nuxt truyền vào
const props = defineProps({
  error: Object
})

// Hàm xử lý khi người dùng muốn quay lại
const handleError = () => {
  clearError({ redirect: '/dashboard' }) // Xóa lỗi và đưa về Dashboard
}
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-gray-50 text-center">
    <div class="max-w-md p-8 bg-white rounded-lg shadow-md border border-gray-200">
      <h1 class="text-6xl font-bold text-red-500 mb-4">{{ error.statusCode }}</h1>
      <h2 class="text-2xl font-semibold mb-2">Oops! Có lỗi xảy ra.</h2>
      
      <p class="text-gray-600 mb-6">{{ error.statusMessage || error.message }}</p>
      
      <button 
        @click="handleError"
        class="bg-[#2da44e] text-white px-4 py-2 rounded-md font-semibold hover:bg-[#2c974b]"
      >
        Quay lại trang chủ
      </button>
    </div>
  </div>
</template>
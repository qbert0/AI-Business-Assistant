<script setup>
definePageMeta({
  layout: 'auth'
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-light text-center mb-6">Tạo tài khoản</h1>
    <div class="space-y-4">
      <input type="text" placeholder="Tên đăng nhập" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500" />
      <input type="email" placeholder="Email" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500" />
      <input type="password" placeholder="Mật khẩu" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500" />
      <button class="w-full bg-[#2da44e] text-white py-2 rounded-md font-semibold hover:bg-[#2c974b]">Đăng ký</button>
    </div>
    <p class="mt-4 text-sm text-center">
      Đã có tài khoản? <NuxtLink to="/login" class="text-blue-600 hover:underline">Đăng nhập</NuxtLink>
    </p>
  </div>
</template>
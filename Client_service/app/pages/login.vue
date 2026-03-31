<script setup>
definePageMeta({
  layout: 'auth'
})

// Gọi hàm login giả lập từ composable
const { login } = useAuth()

// Hàm xử lý khi bấm nút mạng xã hội (Tạm thời giả lập)
const loginWithSocial = (provider) => {
  console.log(`Đang gọi API chuyển hướng đến ${provider}...`)
  // Sau khi OAuth thành công, ta gọi login() để gán token và vào app
  login()
}

const loginWithGoogle = () => {
  const clientId = 'ma_client_id_cua_ban.apps.googleusercontent.com' // Dán trực tiếp hoặc lấy từ runtime config
  const redirectUri = encodeURIComponent('http://localhost:3000/api/auth/google/callback')
  
  // Xây dựng URL chuẩn của Google OAuth 2.0
  const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&scope=email profile&access_type=offline`
  
  // Đẩy người dùng sang Google
  window.location.href = authUrl
}
</script>

<template>
  <div>
    <div class="text-center mb-8">
      <div class="w-12 h-12 bg-[#24292f] text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">G</div>
      <h1 class="text-2xl font-light text-gray-900">Đăng nhập vào hệ thống</h1>
    </div>

    <div class="space-y-3 mb-6">
      <button 
        @click="loginWithGoogle"
        class="w-full flex items-center justify-center gap-3 px-4 py-2 border border-gray-300 rounded-md bg-white text-gray-700 font-medium hover:bg-gray-50 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" class="w-5 h-5">
          <path fill="#FFC107" d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12c0-6.627,5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24c0,11.045,8.955,20,20,20c11.045,0,20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z"/>
          <path fill="#FF3D00" d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z"/>
          <path fill="#4CAF50" d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36c-5.202,0-9.619-3.317-11.283-7.946l-6.522,5.025C9.505,39.556,16.227,44,24,44z"/>
          <path fill="#1976D2" d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571c0.001-0.001,0.002-0.001,0.003-0.002l6.19,5.238C36.971,39.205,44,34,44,24C44,22.659,43.862,21.35,43.611,20.083z"/>
        </svg>
        Tiếp tục với Google
      </button>

      <button 
        @click="loginWithSocial('Facebook')"
        class="w-full flex items-center justify-center gap-3 px-4 py-2 border border-transparent rounded-md bg-[#1877F2] text-white font-medium hover:bg-[#166FE5] transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 320 512" class="w-5 h-5">
          <path d="M279.14 288l14.22-92.66h-88.91v-60.13c0-25.35 12.42-50.06 52.24-50.06h40.42V6.26S260.43 0 225.36 0c-73.22 0-121.08 44.38-121.08 124.72v70.62H22.89V288h81.39v224h100.17V288z"/>
        </svg>
        Tiếp tục với Facebook
      </button>
    </div>

    <div class="relative flex items-center justify-center mb-6">
      <div class="absolute inset-0 flex items-center">
        <div class="w-full border-t border-gray-300"></div>
      </div>
      <div class="relative bg-white px-4 text-sm text-gray-500 font-medium">
        Hoặc đăng nhập bằng Email
      </div>
    </div>

    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Tên đăng nhập / Email</label>
        <input type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow" />
      </div>
      
      <div>
        <div class="flex items-center justify-between mb-1">
          <label class="block text-sm font-medium text-gray-700">Mật khẩu</label>
          <a href="#" class="text-xs text-blue-600 hover:underline">Quên mật khẩu?</a>
        </div>
        <input type="password" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow" />
      </div>

      <button 
        @click="login"
        class="w-full bg-[#2da44e] text-white py-2.5 rounded-md font-semibold hover:bg-[#2c974b] transition-colors mt-2"
      >
        Đăng nhập
      </button>
    </div>

    <p class="mt-6 text-sm text-center border-t border-gray-200 pt-6">
      Chưa có tài khoản? <NuxtLink to="/register" class="text-blue-600 hover:underline font-medium">Tạo tài khoản mới</NuxtLink>
    </p>
  </div>
</template>
<template>
  <div>
    <div class="border-b border-gray-200 pb-4 mb-6">
      <h1 class="text-2xl font-semibold">Tìm kiếm tổ chức</h1>
    </div>

    <div class="flex gap-4 mb-6">
      <input 
        type="text" 
        placeholder="Nhập tên tổ chức cần tìm..." 
        class="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button class="bg-gray-100 border border-gray-300 px-4 py-2 rounded-md font-medium hover:bg-gray-200">
        Tìm kiếm
      </button>
    </div>

    <div class="bg-white border border-gray-200 rounded-md">
      <div class="p-4 border-b border-gray-100 flex items-center gap-4">
        <div class="w-10 h-10 bg-gray-200 rounded-md"></div>
        <div>
          <h3 class="font-semibold text-blue-600">Vue.js Vietnam</h3>
          <p class="text-sm text-gray-500">Cộng đồng lập trình viên Vue.js</p>
        </div>
      </div>
      <div class="p-4 flex items-center gap-4">
        <div class="w-10 h-10 bg-gray-200 rounded-md"></div>
        <div>
          <h3 class="font-semibold text-blue-600">Nuxt Core Team</h3>
          <p class="text-sm text-gray-500">Official Nuxt.js organization</p>
        </div>
      </div>
    </div>
  </div>
</template>
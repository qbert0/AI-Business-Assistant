<template>
  <div class="min-h-screen bg-white text-gray-900 flex flex-col font-sans">
    <LayoutAppHeader />
    
    <div class="flex flex-1 overflow-hidden">
      <LayoutAppSidebar />
      
      <main class="flex-1 overflow-y-auto p-6 bg-gray-50">
        <slot />
      </main>
    </div>
  </div>
</template>
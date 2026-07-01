<template>
  <div class="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950">
    <!-- Sidebar desktop -->
    <AppSidebar class="hidden lg:flex flex-col" />

    <!-- Sidebar mobile drawer -->
    <USlideover v-model="sidebarOpen" side="left" :ui="{ width: 'max-w-[232px]' }">
      <AppSidebar class="flex flex-col h-full" />
    </USlideover>

    <!-- Main content -->
    <div class="flex flex-col flex-1 overflow-hidden">
      <AppTopbar @toggle-sidebar="sidebarOpen = !sidebarOpen" />
      <main class="flex-1 overflow-y-auto p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
const sidebarOpen = ref(false)
</script>

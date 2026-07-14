<template>
  <div class="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950">
    <!-- Sidebar desktop -->
    <AppSidebar
      class="hidden lg:flex flex-col"
      :collapsed="sidebarCollapsed"
      collapsible
      @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
    />

    <!-- Sidebar mobile drawer -->
    <USlideover v-model:open="sidebarOpen" side="left" :ui="{ content: 'max-w-[232px]' }">
      <template #body>
        <AppSidebar class="flex flex-col h-full" />
      </template>
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

// Persisted so the collapsed/expanded preference survives page reloads.
const sidebarCollapsed = useCookie<boolean>('sidebar_collapsed', { default: () => false })
</script>

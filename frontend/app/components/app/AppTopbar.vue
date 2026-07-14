<template>
  <header class="h-14 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex items-center px-4 gap-4">
    <!-- Hamburger (mobile) -->
    <button
      class="lg:hidden p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
      @click="$emit('toggle-sidebar')"
    >
      <UIcon name="i-lucide-menu" class="w-5 h-5" />
    </button>

    <!-- Search (placeholder) -->
    <div class="flex-1 max-w-sm">
      <UInput
        placeholder="Cari kontak, deal, perusahaan..."
        icon="i-lucide-search"
        :ui="{ base: 'w-full' }"
        disabled
      />
    </div>

    <div class="ml-auto flex items-center gap-2">
      <!-- Theme toggle -->
      <AppThemeToggle />
      <!-- AI (placeholder) -->
      <UButton icon="i-lucide-sparkles" color="neutral" variant="ghost" disabled />
      <!-- Notifications (placeholder) -->
      <UButton icon="i-lucide-bell" color="neutral" variant="ghost" disabled />
      <!-- New deal CTA -->
      <UButton icon="i-lucide-plus" color="primary" size="sm" disabled>
        Deal baru
      </UButton>
    </div>
  </header>
</template>

<script setup lang="ts">
defineEmits<{ 'toggle-sidebar': [] }>()
</script>

<template>
  <li>
    <NuxtLink
      :to="to"
      class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors"
      :class="isActive
        ? 'bg-violet-600 text-white font-medium'
        : 'text-gray-300 hover:bg-gray-800 hover:text-white'"
    >
      <UIcon :name="icon" class="shrink-0 w-4 h-4" />
      <span class="truncate">{{ label }}</span>
      <UBadge v-if="badge" :label="String(badge)" size="xs" color="violet" class="ml-auto" />
    </NuxtLink>
  </li>
</template>

<script setup lang="ts">
const props = defineProps<{
  to: string
  label: string
  icon: string
  badge?: number
  exact?: boolean
}>()

const route = useRoute()
const isActive = computed(() =>
  props.exact ? route.path === props.to : route.path.startsWith(props.to),
)
</script>

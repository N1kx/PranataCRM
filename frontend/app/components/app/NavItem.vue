<template>
  <li>
    <UTooltip :text="label" :disabled="!collapsed" :content="{ side: 'right' }">
      <NuxtLink
        :to="to"
        class="flex items-center gap-3 rounded-lg text-sm transition-colors"
        :class="[
          collapsed ? 'justify-center px-2 py-2' : 'px-3 py-2',
          isActive
            ? 'bg-violet-600 text-white font-medium'
            : 'text-gray-300 hover:bg-gray-800 hover:text-white',
        ]"
      >
        <UIcon :name="icon" class="shrink-0 w-4 h-4" />
        <span v-if="!collapsed" class="truncate">{{ label }}</span>
        <UBadge v-if="badge && !collapsed" :label="String(badge)" size="xs" color="primary" class="ml-auto" />
      </NuxtLink>
    </UTooltip>
  </li>
</template>

<script setup lang="ts">
const props = defineProps<{
  to: string
  label: string
  icon: string
  badge?: number
  exact?: boolean
  collapsed?: boolean
}>()

const route = useRoute()
const isActive = computed(() =>
  props.exact ? route.path === props.to : route.path.startsWith(props.to),
)
</script>

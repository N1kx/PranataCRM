<template>
  <div class="flex items-center gap-2" :class="props.class">
    <!-- Symbol only -->
    <svg
      v-if="iconOnly"
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 80 80"
      :width="size"
      :height="size"
      aria-hidden="true"
    >
      <rect x="14" y="14" width="52" height="52" rx="13" transform="rotate(45 40 40)" fill="#7250ba" />
      <g fill="none" stroke="#ffffff" stroke-width="4.125" stroke-linecap="round" stroke-linejoin="round">
        <line x1="33.25" y1="36.25" x2="46.75" y2="43.75" />
        <circle cx="29.5" cy="33.25" r="5.25" />
        <circle cx="50.5" cy="46.75" r="5.25" />
      </g>
    </svg>

    <!-- Lockup: symbol + wordmark -->
    <template v-else>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 80 80"
        :width="size"
        :height="size"
        aria-hidden="true"
        class="shrink-0"
      >
        <rect x="14" y="14" width="52" height="52" rx="13" transform="rotate(45 40 40)" fill="#7250ba" />
        <g fill="none" stroke="#ffffff" stroke-width="4.125" stroke-linecap="round" stroke-linejoin="round">
          <line x1="33.25" y1="36.25" x2="46.75" y2="43.75" />
          <circle cx="29.5" cy="33.25" r="5.25" />
          <circle cx="50.5" cy="46.75" r="5.25" />
        </g>
      </svg>
      <span class="font-bold tracking-tight" :style="{ fontSize: `${wordmarkSize}px`, color: dark ? '#fff' : '#27252c' }">
        Pranata<span style="color: #7250ba;">CRM</span>
      </span>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  iconOnly?: boolean
  class?: string
  size?: number
  dark?: boolean
}>()

const size = computed(() => props.size ?? 36)
const wordmarkSize = computed(() => Math.round(size.value * 0.55))
</script>

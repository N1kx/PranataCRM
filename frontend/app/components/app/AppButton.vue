<template>
  <UButton
    v-bind="$attrs"
    :loading="loading"
    :disabled="disabled || loading"
    :color="color"
    :variant="variant"
    :size="size"
    :block="block"
    :type="type"
  >
    <slot />
  </UButton>
</template>

<script setup lang="ts">
defineOptions({ inheritAttrs: false })

defineProps<{
  loading?: boolean
  disabled?: boolean
  color?: string
  variant?: string
  size?: string
  block?: boolean
  type?: 'button' | 'submit' | 'reset'
}>()
</script>

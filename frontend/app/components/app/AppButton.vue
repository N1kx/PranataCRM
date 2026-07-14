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
import type { ButtonProps } from '#ui/types'

defineOptions({ inheritAttrs: false })

defineProps<{
  loading?: boolean
  disabled?: boolean
  color?: ButtonProps['color']
  variant?: ButtonProps['variant']
  size?: ButtonProps['size']
  block?: boolean
  type?: 'button' | 'submit' | 'reset'
}>()
</script>

<template>
  <UFormField :label="label" :name="name" :hint="hint" :error="error">
    <slot />
  </UFormField>
</template>

<script setup lang="ts">
defineProps<{
  label?: string
  name?: string
  hint?: string
  error?: string
}>()
</script>

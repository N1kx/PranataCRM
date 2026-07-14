<template>
  <UFormField :label="label" :name="name" :hint="hint" :error="error" :required="required">
    <slot />
  </UFormField>
</template>

<script setup lang="ts">
defineProps<{
  label?: string
  name?: string
  hint?: string
  error?: string
  required?: boolean
}>()
</script>

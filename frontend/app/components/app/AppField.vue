<template>
  <!-- Nuxt UI v2 component is UFormGroup (UFormField only exists in v3) -->
  <UFormGroup :label="label" :name="name" :hint="hint" :error="error">
    <slot />
  </UFormGroup>
</template>

<script setup lang="ts">
defineProps<{
  label?: string
  name?: string
  hint?: string
  error?: string
}>()
</script>

<template>
  <UDropdown :items="items" :ui="{ item: { padding: 'px-3 py-2' } }">
    <UButton
      :icon="activeIcon"
      color="gray"
      variant="ghost"
      :aria-label="t('theme.label')"
    />
  </UDropdown>
</template>

<script setup lang="ts">
const { t } = useI18n()
const colorMode = useColorMode()

const options = [
  { value: 'light', icon: 'i-lucide-sun' },
  { value: 'dark', icon: 'i-lucide-moon' },
  { value: 'system', icon: 'i-lucide-monitor' },
] as const

// preference is 'system' | 'light' | 'dark'; value is the resolved theme.
const activeIcon = computed(() =>
  options.find(o => o.value === colorMode.preference)?.icon ?? 'i-lucide-monitor',
)

const items = computed(() => [
  options.map(o => ({
    label: t(`theme.${o.value}`),
    icon: o.icon,
    // A trailing check marks the active preference.
    trailingIcon: colorMode.preference === o.value ? 'i-lucide-check' : undefined,
    click: () => { colorMode.preference = o.value },
  })),
])
</script>

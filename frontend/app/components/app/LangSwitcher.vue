<template>
  <div class="relative inline-flex items-center rounded-lg" :style="boxStyle">
    <select
      v-model="selected"
      class="appearance-none bg-transparent text-sm font-semibold pl-3 pr-8 py-1.5 rounded-lg outline-none cursor-pointer"
      :style="dark ? 'color:#d8d2e6;' : 'color:#4b4556;'"
    >
      <option value="id" style="color:#27252c;">Indonesia</option>
      <option value="en" style="color:#27252c;">English</option>
    </select>
    <span
      class="absolute right-2.5 pointer-events-none"
      style="font-size:9px; opacity:0.5;"
      :style="dark ? 'color:#d8d2e6;' : 'color:#4b4556;'"
    >
      v
    </span>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ dark?: boolean }>()

const { locale, setLocale } = useI18n()

const selected = ref(locale.value)

watch(selected, async (val) => {
  await setLocale(val as 'id' | 'en')
})

// Keep select in sync if locale changes elsewhere
watch(locale, (val) => {
  selected.value = val
})

const boxStyle = computed(() =>
  props.dark
    ? 'border:1px solid rgba(255,255,255,.15);'
    : 'border:1px solid #e3e0ea; background:#fff;',
)
</script>

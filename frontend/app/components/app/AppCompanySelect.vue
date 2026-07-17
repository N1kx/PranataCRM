<template>
  <USelectMenu
    :model-value="selected"
    :items="items"
    :loading="isLoading"
    :disabled="disabled"
    :search-term="searchTerm"
    ignore-filter
    label-key="name"
    description-key="domain"
    by="id"
    clear
    :placeholder="placeholder ?? t('company_select.placeholder')"
    :search-input="{ placeholder: t('company_select.search_placeholder') }"
    class="w-full"
    @update:model-value="onSelect"
    @update:search-term="onSearchTerm"
  >
    <template #empty>
      <span class="text-sm text-gray-400">{{ t('company_select.no_results') }}</span>
    </template>
  </USelectMenu>
</template>

<script setup lang="ts">
import type { CompanySummary } from '~/types/companies'

const props = defineProps<{
  modelValue?: string | null
  /** A CompanySummary already resolved by the parent, so the label renders without a lookup call. */
  initial?: CompanySummary | null
  placeholder?: string
  disabled?: boolean
}>()

const emit = defineEmits<{ 'update:modelValue': [value: string | null] }>()

const { t } = useI18n()
const { search } = useCompanies()

const selected = ref<CompanySummary | null>(props.initial ?? null)
const items = ref<CompanySummary[]>(props.initial ? [props.initial] : [])
const searchTerm = ref('')
const isLoading = ref(false)

let debounceHandle: ReturnType<typeof setTimeout> | undefined
// Monotonic token so a slow earlier request can't overwrite a newer one's
// results if it resolves out of order.
let searchSeq = 0

async function runSearch(q: string) {
  const seq = ++searchSeq
  isLoading.value = true
  try {
    const results = await search(q)
    if (seq !== searchSeq) return
    items.value = results
  }
  catch {
    if (seq !== searchSeq) return
    items.value = []
  }
  finally {
    if (seq === searchSeq) isLoading.value = false
  }
}

function onSearchTerm(q: string) {
  searchTerm.value = q
  if (debounceHandle) clearTimeout(debounceHandle)
  debounceHandle = setTimeout(() => runSearch(q), 250)
}

function onSelect(value: unknown) {
  const opt = value as CompanySummary | null
  selected.value = opt
  emit('update:modelValue', opt?.id ?? null)
}

watch(() => props.initial, (v) => {
  selected.value = v ?? null
  if (v && !items.value.some(c => c.id === v.id)) {
    items.value = [v, ...items.value]
  }
})

onMounted(() => {
  runSearch('')
})

onUnmounted(() => {
  if (debounceHandle) clearTimeout(debounceHandle)
})
</script>

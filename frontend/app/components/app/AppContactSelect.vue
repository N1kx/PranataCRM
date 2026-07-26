<template>
  <USelectMenu
    :model-value="selected"
    :items="items"
    :loading="isLoading"
    :disabled="disabled"
    :search-term="searchTerm"
    ignore-filter
    label-key="name"
    description-key="email"
    by="id"
    clear
    :placeholder="placeholder ?? t('contact_select.placeholder')"
    :search-input="{ placeholder: t('contact_select.search_placeholder') }"
    class="w-full"
    @update:model-value="onSelect"
    @update:search-term="onSearchTerm"
  >
    <template #empty>
      <span class="text-sm text-gray-400">{{ t('contact_select.no_results') }}</span>
    </template>
  </USelectMenu>
</template>

<script setup lang="ts">
import type { ContactSummary } from '~/types/contacts'

const props = defineProps<{
  modelValue?: string | null
  /** A ContactSummary already resolved by the parent, so the label renders without a lookup call. */
  initial?: ContactSummary | null
  /** Narrows the search to one company's contacts (deal form: the picked company). */
  companyId?: string | null
  placeholder?: string
  disabled?: boolean
}>()

const emit = defineEmits<{ 'update:modelValue': [value: string | null] }>()

const { t } = useI18n()
const { search } = useContacts()

const selected = ref<ContactSummary | null>(props.initial ?? null)
const items = ref<ContactSummary[]>(props.initial ? [props.initial] : [])
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
    const results = await search(q, 20, props.companyId)
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
  const opt = value as ContactSummary | null
  selected.value = opt
  emit('update:modelValue', opt?.id ?? null)
}

watch(() => props.initial, (v) => {
  selected.value = v ?? null
  if (v && !items.value.some(c => c.id === v.id)) {
    items.value = [v, ...items.value]
  }
})

// Re-scope the options when the parent's company changes. A contact already
// picked from a different company is cleared, since it would no longer be a
// valid choice within the newly selected company.
watch(() => props.companyId, (companyId) => {
  if (selected.value && companyId && selected.value.company_id !== companyId) {
    selected.value = null
    emit('update:modelValue', null)
  }
  runSearch(searchTerm.value)
})

onMounted(() => {
  runSearch('')
})

onUnmounted(() => {
  if (debounceHandle) clearTimeout(debounceHandle)
})
</script>

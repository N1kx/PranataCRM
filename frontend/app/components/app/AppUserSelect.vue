<template>
  <USelectMenu
    :model-value="selected"
    :items="items"
    :loading="isLoading"
    :disabled="disabled"
    :search-term="searchTerm"
    ignore-filter
    label-key="full_name"
    description-key="email"
    by="id"
    clear
    :placeholder="placeholder ?? t('user_select.placeholder')"
    :search-input="{ placeholder: t('user_select.search_placeholder') }"
    class="w-full"
    @update:model-value="onSelect"
    @update:search-term="onSearchTerm"
  >
    <template #empty>
      <span class="text-sm text-gray-400">{{ t('user_select.no_results') }}</span>
    </template>
  </USelectMenu>
</template>

<script setup lang="ts">
import type { UserSummary } from '~/types/user'

const props = defineProps<{
  modelValue?: string | null
  /** A UserSummary already resolved by the parent, so the label renders without a lookup call. */
  initial?: UserSummary | null
  placeholder?: string
  disabled?: boolean
}>()

const emit = defineEmits<{ 'update:modelValue': [value: string | null] }>()

const { t } = useI18n()
const { search } = useUsers()

const selected = ref<UserSummary | null>(props.initial ?? null)
const items = ref<UserSummary[]>(props.initial ? [props.initial] : [])
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
  const opt = value as UserSummary | null
  selected.value = opt
  emit('update:modelValue', opt?.id ?? null)
}

watch(() => props.initial, (v) => {
  selected.value = v ?? null
  if (v && !items.value.some(u => u.id === v.id)) {
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

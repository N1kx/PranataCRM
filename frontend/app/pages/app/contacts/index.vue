<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('contacts.title') }}
      </h1>
      <AppButton color="primary" icon="i-lucide-user-plus" @click="navigateTo('/app/contacts/new')">
        {{ t('contacts.add') }}
      </AppButton>
    </div>

    <!-- Error state -->
    <UAlert
      v-if="loadError"
      color="error"
      variant="soft"
      icon="i-lucide-circle-alert"
      :title="t('common.error_state')"
    >
      <template #description>
        <AppButton color="error" variant="outline" size="xs" class="mt-2" @click="loadContacts">
          {{ t('common.retry') }}
        </AppButton>
      </template>
    </UAlert>

    <!-- Toolbar -->
    <UCard v-else>
      <div class="flex flex-wrap items-center gap-3 pb-4">
        <AppInput
          v-model="searchInput"
          icon="i-lucide-search"
          class="w-full sm:w-64"
          :placeholder="t('contacts.search_placeholder')"
        />
        <USelect
          v-model="statusModel"
          :items="statusFilterOptions"
          class="w-full sm:w-40"
        />
        <USelect
          v-model="lifecycleModel"
          :items="lifecycleFilterOptions"
          class="w-full sm:w-48"
        />
        <AppButton
          v-if="hasActiveFilters"
          color="neutral"
          variant="ghost"
          size="xs"
          @click="clearFilters"
        >
          {{ t('contacts.clear_filters') }}
        </AppButton>
      </div>

      <!-- Loading state -->
      <div v-if="isLoading && !items.length" class="text-center py-12 text-gray-400">
        <UIcon name="i-lucide-loader-circle" class="w-8 h-8 mx-auto mb-3 animate-spin" />
        <p class="text-sm">
          {{ t('common.loading') }}
        </p>
      </div>

      <!-- Empty state -->
      <div v-else-if="!items.length" class="text-center py-12 text-gray-400">
        <UIcon name="i-lucide-users" class="w-10 h-10 mx-auto mb-3" />
        <p class="text-sm">
          {{ hasActiveFilters ? t('contacts.no_results') : t('common.empty') }}
        </p>
        <AppButton v-if="hasActiveFilters" color="neutral" variant="outline" size="xs" class="mt-3" @click="clearFilters">
          {{ t('contacts.clear_filters') }}
        </AppButton>
      </div>

      <template v-else>
        <UTable :data="items" :columns="columns" :loading="isLoading">
          <template v-for="col in sortableColumns" :key="col" #[`${col}-header`]>
            <button type="button" class="flex items-center gap-1" @click="toggleSort(col)">
              {{ t(`contacts.table.${col}`) }}
              <UIcon v-if="sort === COLUMN_TO_SORT_FIELD[col]" :name="order === 'asc' ? 'i-lucide-arrow-up' : 'i-lucide-arrow-down'" class="w-3.5 h-3.5" />
            </button>
          </template>

          <template #name-cell="{ row }">
            <NuxtLink
              :to="`/app/contacts/${row.original.id}`"
              class="font-medium text-gray-900 dark:text-white hover:text-primary-600 dark:hover:text-primary-400"
            >
              {{ contactFullName(row.original) }}
            </NuxtLink>
          </template>
          <template #email-cell="{ row }">
            {{ row.original.email || '-' }}
          </template>
          <template #phone-cell="{ row }">
            {{ row.original.phone || '-' }}
          </template>
          <template #job_title-cell="{ row }">
            {{ row.original.job_title || '-' }}
          </template>
          <template #status-cell="{ row }">
            <UBadge :color="contactStatusColor(row.original.status)" variant="subtle">
              {{ t(`contacts.status.${row.original.status}`) }}
            </UBadge>
          </template>
          <template #owner-cell="{ row }">
            {{ row.original.owner_id ? (ownerNames[row.original.owner_id] ?? '-') : '-' }}
          </template>
          <template #actions-cell="{ row }">
            <UDropdownMenu :items="rowActions(row.original)">
              <UButton color="neutral" variant="ghost" icon="i-lucide-ellipsis-vertical" />
            </UDropdownMenu>
          </template>
        </UTable>

        <!-- Pagination -->
        <div v-if="total > pageSize" class="flex justify-end pt-4">
          <UPagination v-model:page="page" :items-per-page="pageSize" :total="total" />
        </div>
      </template>
    </UCard>

    <!-- Delete confirmation modal -->
    <UModal v-model:open="deleteModalOpen" :title="t('contacts.confirm_delete_title')">
      <template #body>
        <p class="text-sm text-gray-600 dark:text-gray-300">
          {{ t('contacts.confirm_delete_body', { name: deleteTarget ? contactFullName(deleteTarget) : '' }) }}
        </p>
      </template>

      <template #footer>
        <div class="flex justify-end gap-3">
          <AppButton color="neutral" variant="outline" :disabled="isDeleting" @click="deleteModalOpen = false">
            {{ t('common.cancel') }}
          </AppButton>
          <AppButton color="error" :loading="isDeleting" @click="onDelete">
            {{ t('contacts.delete') }}
          </AppButton>
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import type { Contact, ContactStatus, LifecycleStage } from '~/types/contacts'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t } = useI18n()
const { list, remove } = useContacts()
const { lookup } = useUsers()
const toast = useToast()
const route = useRoute()
const router = useRouter()

// ── URL-synced filter/sort/pagination state ─────────────────────────────────
// Kept in the URL query so the view is shareable/back-button friendly.

const ALL = '__all__'
const SORTABLE_FIELDS = ['created_at', 'first_name', 'last_name', 'email', 'status'] as const
const sortableColumns = ['name', 'email', 'status']
// The Name column sorts server-side by first_name (mirrors how it's displayed);
// this maps each sortable column id to its backend sort field. Used both to
// build the sort param on click and to light up the active column's arrow.
const COLUMN_TO_SORT_FIELD: Record<string, typeof SORTABLE_FIELDS[number]> = {
  name: 'first_name',
  email: 'email',
  status: 'status',
}

function readQuery() {
  const q = route.query
  return {
    page: Number(q.page) > 0 ? Number(q.page) : 1,
    q: typeof q.q === 'string' ? q.q : '',
    status: typeof q.status === 'string' ? q.status : '',
    lifecycleStage: typeof q.lifecycle_stage === 'string' ? q.lifecycle_stage : '',
    sort: typeof q.sort === 'string' && (SORTABLE_FIELDS as readonly string[]).includes(q.sort) ? q.sort : 'created_at',
    order: (q.order === 'asc' ? 'asc' : 'desc') as 'asc' | 'desc',
  }
}

const initial = readQuery()
const page = ref(initial.page)
const searchInput = ref(initial.q)
const status = ref<ContactStatus | ''>(initial.status as ContactStatus | '')
const lifecycleStage = ref<LifecycleStage | ''>(initial.lifecycleStage as LifecycleStage | '')
const sort = ref<typeof SORTABLE_FIELDS[number]>(initial.sort as typeof SORTABLE_FIELDS[number])
const order = ref<'asc' | 'desc'>(initial.order)
const pageSize = 20

const statusModel = computed({
  get: () => status.value || ALL,
  set: (v: string) => { status.value = (v === ALL ? '' : v) as ContactStatus | '' },
})
const lifecycleModel = computed({
  get: () => lifecycleStage.value || ALL,
  set: (v: string) => { lifecycleStage.value = (v === ALL ? '' : v) as LifecycleStage | '' },
})

const CONTACT_STATUSES: ContactStatus[] = ['lead', 'qualified', 'customer', 'churned']
const LIFECYCLE_STAGES: LifecycleStage[] = [
  'subscriber', 'lead', 'mql', 'sql', 'opportunity', 'customer', 'evangelist',
]

const statusFilterOptions = computed(() => [
  { value: ALL, label: t('contacts.filter.status_all') },
  ...CONTACT_STATUSES.map(v => ({ value: v, label: t(`contacts.status.${v}`) })),
])
const lifecycleFilterOptions = computed(() => [
  { value: ALL, label: t('contacts.filter.lifecycle_all') },
  ...LIFECYCLE_STAGES.map(v => ({ value: v, label: t(`contacts.lifecycle.${v}`) })),
])

const hasActiveFilters = computed(() =>
  !!(searchInput.value || status.value || lifecycleStage.value),
)

function clearFilters() {
  searchInput.value = ''
  status.value = ''
  lifecycleStage.value = ''
}

function toggleSort(col: string) {
  const field = COLUMN_TO_SORT_FIELD[col]
  if (!field) return
  if (sort.value === field) {
    order.value = order.value === 'asc' ? 'desc' : 'asc'
  }
  else {
    sort.value = field
    order.value = 'asc'
  }
  page.value = 1
}

// Debounced search input.
let searchDebounce: ReturnType<typeof setTimeout> | undefined
const q = ref(initial.q)
watch(searchInput, (v) => {
  if (searchDebounce) clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => { q.value = v; page.value = 1 }, 300)
})

watch([status, lifecycleStage], () => { page.value = 1 })

// Sync state -> URL query (replace, not push, to avoid polluting history per keystroke).
watch([page, q, status, lifecycleStage, sort, order], () => {
  router.replace({
    query: {
      ...(page.value > 1 ? { page: String(page.value) } : {}),
      ...(q.value ? { q: q.value } : {}),
      ...(status.value ? { status: status.value } : {}),
      ...(lifecycleStage.value ? { lifecycle_stage: lifecycleStage.value } : {}),
      ...(sort.value !== 'created_at' ? { sort: sort.value } : {}),
      ...(order.value !== 'desc' ? { order: order.value } : {}),
    },
  })
})

// ── List state ────────────────────────────────────────────────────────────────

const items = ref<Contact[]>([])
const total = ref(0)
const isLoading = ref(false)
// id -> full_name map, resolved once per page load instead of per row.
const ownerNames = ref<Record<string, string>>({})
const loadError = ref(false)

const columns = computed<TableColumn<Contact>[]>(() => [
  { accessorKey: 'first_name', id: 'name', header: t('contacts.table.name') },
  { accessorKey: 'email', header: t('contacts.table.email') },
  { accessorKey: 'phone', header: t('contacts.table.phone') },
  { accessorKey: 'job_title', header: t('contacts.table.job_title') },
  { accessorKey: 'status', header: t('contacts.table.status') },
  { accessorKey: 'owner_id', id: 'owner', header: t('contacts.table.owner') },
  { id: 'actions', header: '' },
])

// Monotonic token so a slow earlier request (e.g. rapid filter/sort changes on
// a slow network) can't overwrite a newer one's results if it resolves out of
// order — mirrors AppUserSelect's searchSeq.
let loadSeq = 0

async function loadContacts() {
  const seq = ++loadSeq
  isLoading.value = true
  loadError.value = false
  try {
    const res = await list({
      page: page.value,
      pageSize,
      q: q.value || undefined,
      status: status.value || undefined,
      lifecycleStage: lifecycleStage.value || undefined,
      sort: sort.value,
      order: order.value,
    })
    if (seq !== loadSeq) return
    items.value = res.items
    total.value = res.total
  }
  catch {
    if (seq !== loadSeq) return
    loadError.value = true
    return
  }
  finally {
    if (seq === loadSeq) isLoading.value = false
  }
  // Owner names are a secondary enrichment: resolve them separately so a lookup
  // failure degrades to "-" instead of blanking the whole (already loaded) list.
  await loadOwnerNames(items.value)
}

async function loadOwnerNames(contacts: Contact[]) {
  const ids = [...new Set(contacts.map(c => c.owner_id).filter((id): id is string => !!id))]
  if (!ids.length) {
    ownerNames.value = {}
    return
  }
  try {
    const owners = await lookup(ids)
    ownerNames.value = owners.reduce<Record<string, string>>((acc, o) => {
      acc[o.id] = o.full_name
      return acc
    }, {})
  }
  catch {
    ownerNames.value = {}
  }
}

onMounted(loadContacts)
watch([page, q, status, lifecycleStage, sort, order], loadContacts)

function rowActions(row: Contact) {
  return [[
    {
      label: t('contacts.actions.view'),
      icon: 'i-lucide-eye',
      onSelect: () => navigateTo(`/app/contacts/${row.id}`),
    },
    {
      label: t('contacts.actions.edit'),
      icon: 'i-lucide-pencil',
      onSelect: () => navigateTo(`/app/contacts/${row.id}/edit`),
    },
    {
      label: t('contacts.actions.delete'),
      icon: 'i-lucide-trash-2',
      onSelect: () => confirmDelete(row),
    },
  ]]
}

// ── Delete ────────────────────────────────────────────────────────────────────

const deleteModalOpen = ref(false)
const deleteTarget = ref<Contact | null>(null)
const isDeleting = ref(false)

function confirmDelete(row: Contact) {
  deleteTarget.value = row
  deleteModalOpen.value = true
}

async function onDelete() {
  if (!deleteTarget.value) return
  isDeleting.value = true
  try {
    await remove(deleteTarget.value.id)
    toast.add({ title: t('contacts.deleted'), color: 'success', icon: 'i-lucide-check-circle' })
    deleteModalOpen.value = false
    deleteTarget.value = null
    // If we deleted the last row of a page > 1, step back one page
    // (the page watcher triggers the reload).
    if (items.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    else {
      await loadContacts()
    }
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    toast.add({
      title: t(`error.${e.code ?? 'unknown'}`, t('error.unknown')),
      color: 'error',
      icon: 'i-lucide-circle-alert',
    })
  }
  finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('companies.title') }}
      </h1>
      <AppButton color="primary" icon="i-lucide-building-2" @click="navigateTo('/app/companies/new')">
        {{ t('companies.add') }}
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
        <AppButton color="error" variant="outline" size="xs" class="mt-2" @click="loadCompanies">
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
          :placeholder="t('companies.search_placeholder')"
        />
        <USelect
          v-model="statusModel"
          :items="statusFilterOptions"
          class="w-full sm:w-40"
        />
        <USelect
          v-model="companyTypeModel"
          :items="companyTypeFilterOptions"
          class="w-full sm:w-40"
        />
        <USelect
          v-model="sizeModel"
          :items="sizeFilterOptions"
          class="w-full sm:w-40"
        />
        <AppInput
          v-model="industryInput"
          class="w-full sm:w-48"
          :placeholder="t('companies.filter_industry')"
        />
        <AppButton
          v-if="hasActiveFilters"
          color="neutral"
          variant="ghost"
          size="xs"
          @click="clearFilters"
        >
          {{ t('companies.clear_filters') }}
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
        <UIcon name="i-lucide-building-2" class="w-10 h-10 mx-auto mb-3" />
        <p class="text-sm">
          {{ hasActiveFilters ? t('companies.no_results') : t('common.empty') }}
        </p>
        <AppButton v-if="hasActiveFilters" color="neutral" variant="outline" size="xs" class="mt-3" @click="clearFilters">
          {{ t('companies.clear_filters') }}
        </AppButton>
      </div>

      <template v-else>
        <UTable :data="items" :columns="columns" :loading="isLoading">
          <template v-for="col in sortableColumns" :key="col" #[`${col}-header`]>
            <button type="button" class="flex items-center gap-1" @click="toggleSort(col)">
              {{ t(`companies.table.${col}`) }}
              <UIcon v-if="sort === col" :name="order === 'asc' ? 'i-lucide-arrow-up' : 'i-lucide-arrow-down'" class="w-3.5 h-3.5" />
            </button>
          </template>

          <template #name-cell="{ row }">
            <NuxtLink
              :to="`/app/companies/${row.original.id}`"
              class="font-medium text-gray-900 dark:text-white hover:text-primary-600 dark:hover:text-primary-400"
            >
              {{ companyDisplayName(row.original) }}
            </NuxtLink>
          </template>
          <template #domain-cell="{ row }">
            {{ row.original.domain || '-' }}
          </template>
          <template #company_type-cell="{ row }">
            <UBadge :color="companyTypeColor(row.original.company_type)" variant="subtle">
              {{ t(`companies.type.${row.original.company_type}`) }}
            </UBadge>
          </template>
          <template #status-cell="{ row }">
            <UBadge :color="companyStatusColor(row.original.status)" variant="subtle">
              {{ t(`companies.status.${row.original.status}`) }}
            </UBadge>
          </template>
          <template #employee_count-cell="{ row }">
            {{ row.original.employee_count != null ? row.original.employee_count : '-' }}
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
    <UModal v-model:open="deleteModalOpen" :title="t('companies.confirm_delete_title')">
      <template #body>
        <p class="text-sm text-gray-600 dark:text-gray-300">
          {{ t('companies.confirm_delete_body', { name: deleteTarget ? companyDisplayName(deleteTarget) : '' }) }}
        </p>
      </template>

      <template #footer>
        <div class="flex justify-end gap-3">
          <AppButton color="neutral" variant="outline" :disabled="isDeleting" @click="deleteModalOpen = false">
            {{ t('common.cancel') }}
          </AppButton>
          <AppButton color="error" :loading="isDeleting" @click="onDelete">
            {{ t('companies.delete') }}
          </AppButton>
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import type { Company, CompanySize, CompanyStatus, CompanyType } from '~/types/companies'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t } = useI18n()
const { list, remove } = useCompanies()
const { lookup } = useUsers()
const toast = useToast()
const route = useRoute()
const router = useRouter()

// ── URL-synced filter/sort/pagination state ─────────────────────────────────
// Kept in the URL query so the view is shareable/back-button friendly
// (same approach as contacts, see #23).

const ALL = '__all__'
const SORTABLE_FIELDS = ['name', 'company_type', 'status', 'employee_count', 'created_at'] as const
const sortableColumns = ['name', 'company_type', 'status', 'employee_count']

function readQuery() {
  const q = route.query
  return {
    page: Number(q.page) > 0 ? Number(q.page) : 1,
    q: typeof q.q === 'string' ? q.q : '',
    status: typeof q.status === 'string' ? q.status : '',
    companyType: typeof q.company_type === 'string' ? q.company_type : '',
    size: typeof q.size === 'string' ? q.size : '',
    industry: typeof q.industry === 'string' ? q.industry : '',
    sort: typeof q.sort === 'string' && (SORTABLE_FIELDS as readonly string[]).includes(q.sort) ? q.sort : 'created_at',
    order: (q.order === 'asc' ? 'asc' : 'desc') as 'asc' | 'desc',
  }
}

const initial = readQuery()
const page = ref(initial.page)
const searchInput = ref(initial.q)
const industryInput = ref(initial.industry)
const status = ref<CompanyStatus | ''>(initial.status as CompanyStatus | '')
const companyType = ref<CompanyType | ''>(initial.companyType as CompanyType | '')
const size = ref<CompanySize | ''>(initial.size as CompanySize | '')
const sort = ref<typeof SORTABLE_FIELDS[number]>(initial.sort as typeof SORTABLE_FIELDS[number])
const order = ref<'asc' | 'desc'>(initial.order)
const pageSize = 20

const statusModel = computed({
  get: () => status.value || ALL,
  set: (v: string) => { status.value = (v === ALL ? '' : v) as CompanyStatus | '' },
})
const companyTypeModel = computed({
  get: () => companyType.value || ALL,
  set: (v: string) => { companyType.value = (v === ALL ? '' : v) as CompanyType | '' },
})
const sizeModel = computed({
  get: () => size.value || ALL,
  set: (v: string) => { size.value = (v === ALL ? '' : v) as CompanySize | '' },
})

const statusFilterOptions = computed(() => [
  { value: ALL, label: t('companies.filter_status') },
  { value: 'active', label: t('companies.status.active') },
  { value: 'inactive', label: t('companies.status.inactive') },
])
const companyTypeFilterOptions = computed(() => [
  { value: ALL, label: t('companies.filter_type') },
  ...(['prospect', 'customer', 'partner', 'vendor', 'competitor', 'other'] as CompanyType[])
    .map(v => ({ value: v, label: t(`companies.type.${v}`) })),
])
const sizeFilterOptions = computed(() => [
  { value: ALL, label: t('companies.filter_size') },
  ...(['1-10', '11-50', '51-200', '201-500', '500+'] as CompanySize[]).map(v => ({ value: v, label: v })),
])

const hasActiveFilters = computed(() =>
  !!(searchInput.value || status.value || companyType.value || size.value || industryInput.value),
)

function clearFilters() {
  searchInput.value = ''
  industryInput.value = ''
  status.value = ''
  companyType.value = ''
  size.value = ''
}

function toggleSort(col: string) {
  if (sort.value === col) {
    order.value = order.value === 'asc' ? 'desc' : 'asc'
  }
  else {
    sort.value = col as typeof SORTABLE_FIELDS[number]
    order.value = 'asc'
  }
  page.value = 1
}

// Debounced search/industry text input.
let searchDebounce: ReturnType<typeof setTimeout> | undefined
const q = ref(initial.q)
watch(searchInput, (v) => {
  if (searchDebounce) clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => { q.value = v; page.value = 1 }, 300)
})
let industryDebounce: ReturnType<typeof setTimeout> | undefined
const industry = ref(initial.industry)
watch(industryInput, (v) => {
  if (industryDebounce) clearTimeout(industryDebounce)
  industryDebounce = setTimeout(() => { industry.value = v; page.value = 1 }, 300)
})

watch([status, companyType, size], () => { page.value = 1 })

// Sync state -> URL query (replace, not push, to avoid polluting history per keystroke).
watch([page, q, status, companyType, size, industry, sort, order], () => {
  router.replace({
    query: {
      ...(page.value > 1 ? { page: String(page.value) } : {}),
      ...(q.value ? { q: q.value } : {}),
      ...(status.value ? { status: status.value } : {}),
      ...(companyType.value ? { company_type: companyType.value } : {}),
      ...(size.value ? { size: size.value } : {}),
      ...(industry.value ? { industry: industry.value } : {}),
      ...(sort.value !== 'created_at' ? { sort: sort.value } : {}),
      ...(order.value !== 'desc' ? { order: order.value } : {}),
    },
  })
})

// ── List state ────────────────────────────────────────────────────────────────

const items = ref<Company[]>([])
const total = ref(0)
const isLoading = ref(false)
// id -> full_name map, resolved once per page load instead of per row.
const ownerNames = ref<Record<string, string>>({})
const loadError = ref(false)

const columns = computed<TableColumn<Company>[]>(() => [
  { accessorKey: 'name', id: 'name', header: t('companies.table.name') },
  { accessorKey: 'domain', header: t('companies.table.domain') },
  { accessorKey: 'company_type', header: t('companies.table.company_type') },
  { accessorKey: 'status', header: t('companies.table.status') },
  { accessorKey: 'employee_count', header: t('companies.table.employee_count') },
  { accessorKey: 'owner_id', id: 'owner', header: t('companies.table.owner') },
  { id: 'actions', header: '' },
])

// Monotonic token so a slow earlier request (e.g. rapid filter/sort changes on
// a slow network) can't overwrite a newer one's results if it resolves out of
// order — mirrors AppUserSelect's searchSeq.
let loadSeq = 0

async function loadCompanies() {
  const seq = ++loadSeq
  isLoading.value = true
  loadError.value = false
  try {
    const res = await list({
      page: page.value,
      pageSize,
      q: q.value || undefined,
      status: status.value || undefined,
      companyType: companyType.value || undefined,
      size: size.value || undefined,
      industry: industry.value || undefined,
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

async function loadOwnerNames(companies: Company[]) {
  const ids = [...new Set(companies.map(c => c.owner_id).filter((id): id is string => !!id))]
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

onMounted(loadCompanies)
watch([page, q, status, companyType, size, industry, sort, order], loadCompanies)

function rowActions(row: Company) {
  return [[
    {
      label: t('companies.actions.view'),
      icon: 'i-lucide-eye',
      onSelect: () => navigateTo(`/app/companies/${row.id}`),
    },
    {
      label: t('companies.actions.edit'),
      icon: 'i-lucide-pencil',
      onSelect: () => navigateTo(`/app/companies/${row.id}/edit`),
    },
    {
      label: t('companies.actions.delete'),
      icon: 'i-lucide-trash-2',
      onSelect: () => confirmDelete(row),
    },
  ]]
}

// ── Delete ────────────────────────────────────────────────────────────────────

const deleteModalOpen = ref(false)
const deleteTarget = ref<Company | null>(null)
const isDeleting = ref(false)

function confirmDelete(row: Company) {
  deleteTarget.value = row
  deleteModalOpen.value = true
}

async function onDelete() {
  if (!deleteTarget.value) return
  isDeleting.value = true
  try {
    await remove(deleteTarget.value.id)
    toast.add({ title: t('companies.deleted'), color: 'success', icon: 'i-lucide-check-circle' })
    deleteModalOpen.value = false
    deleteTarget.value = null
    // If we deleted the last row of a page > 1, step back one page
    // (the page watcher triggers the reload).
    if (items.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    else {
      await loadCompanies()
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

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between gap-3">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('deals.title') }}
      </h1>
      <div class="flex items-center gap-2">
        <!-- Pipeline (default) / list toggle -->
        <!-- v4 renamed ButtonGroup to FieldGroup. -->
        <UFieldGroup>
          <UButton
            :color="view === 'pipeline' ? 'primary' : 'neutral'"
            :variant="view === 'pipeline' ? 'solid' : 'outline'"
            icon="i-lucide-columns-3"
            :aria-label="t('deals.pipeline.title')"
            @click="view = 'pipeline'"
          />
          <UButton
            :color="view === 'list' ? 'primary' : 'neutral'"
            :variant="view === 'list' ? 'solid' : 'outline'"
            icon="i-lucide-list"
            :aria-label="t('deals.list_view')"
            @click="view = 'list'"
          />
        </UFieldGroup>
        <AppButton color="primary" icon="i-lucide-circle-dollar-sign" @click="navigateTo('/app/deals/new')">
          {{ t('deals.add') }}
        </AppButton>
      </div>
    </div>

    <!-- Pipeline view -->
    <template v-if="view === 'pipeline'">
      <!-- Owner scope, shown here too so the board's default ("my deals") is
           visible and changeable rather than an invisible filter. -->
      <div class="flex flex-wrap items-center gap-3">
        <div class="w-full sm:w-64">
          <AppUserSelect
            :model-value="ownerId"
            :initial="ownerInitial"
            :placeholder="t('deals.filter_owner')"
            @update:model-value="setOwner"
          />
        </div>
        <AppButton
          v-if="hasActiveFilters"
          color="neutral"
          variant="ghost"
          size="xs"
          @click="clearFilters"
        >
          {{ t('deals.clear_filters') }}
        </AppButton>
      </div>
      <DealsPipeline ref="pipelineRef" :owner-id="ownerId" />
    </template>

    <template v-else>
      <!-- Error state -->
      <UAlert
        v-if="loadError"
        color="error"
        variant="soft"
        icon="i-lucide-circle-alert"
        :title="t('common.error_state')"
      >
        <template #description>
          <AppButton color="error" variant="outline" size="xs" class="mt-2" @click="loadDeals">
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
            :placeholder="t('deals.search_placeholder')"
          />
          <USelect v-model="stageModel" :items="stageFilterOptions" class="w-full sm:w-40" />
          <USelect v-model="statusModel" :items="statusFilterOptions" class="w-full sm:w-40" />
          <USelect v-model="dealTypeModel" :items="dealTypeFilterOptions" class="w-full sm:w-44" />
          <USelect v-model="priorityModel" :items="priorityFilterOptions" class="w-full sm:w-40" />
          <div class="w-full sm:w-56">
            <AppUserSelect
              :model-value="ownerId"
              :initial="ownerInitial"
              :placeholder="t('deals.filter_owner')"
              @update:model-value="setOwner"
            />
          </div>
          <div class="w-full sm:w-56">
            <AppCompanySelect
              v-model="companyId"
              :initial="companyInitial"
              :placeholder="t('deals.filter_company')"
            />
          </div>
          <AppButton
            v-if="hasActiveFilters"
            color="neutral"
            variant="ghost"
            size="xs"
            @click="clearFilters"
          >
            {{ t('deals.clear_filters') }}
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
          <UIcon name="i-lucide-circle-dollar-sign" class="w-10 h-10 mx-auto mb-3" />
          <p class="text-sm">
            {{ hasActiveFilters ? t('deals.no_results') : t('common.empty') }}
          </p>
          <AppButton v-if="hasActiveFilters" color="neutral" variant="outline" size="xs" class="mt-3" @click="clearFilters">
            {{ t('deals.clear_filters') }}
          </AppButton>
        </div>

        <template v-else>
          <UTable :data="items" :columns="columns" :loading="isLoading">
            <template v-for="col in sortableColumns" :key="col" #[`${col}-header`]>
              <button type="button" class="flex items-center gap-1" @click="toggleSort(col)">
                {{ t(`deals.table.${col}`) }}
                <UIcon
                  v-if="sort === col"
                  :name="order === 'asc' ? 'i-lucide-arrow-up' : 'i-lucide-arrow-down'"
                  class="w-3.5 h-3.5"
                />
              </button>
            </template>

            <template #title-cell="{ row }">
              <NuxtLink
                :to="`/app/deals/${row.original.id}`"
                class="font-medium text-gray-900 dark:text-white hover:text-primary-600 dark:hover:text-primary-400"
              >
                {{ row.original.title }}
              </NuxtLink>
            </template>
            <template #stage-cell="{ row }">
              <DealsStageBadge :stage="row.original.stage" />
            </template>
            <template #status-cell="{ row }">
              <UBadge :color="dealStatusColor(row.original.status)" variant="subtle">
                {{ t(`deals.status.${row.original.status}`) }}
              </UBadge>
            </template>
            <template #value-cell="{ row }">
              {{ formatMoney(row.original.value, row.original.currency, locale) }}
            </template>
            <template #probability-cell="{ row }">
              {{ row.original.probability }}%
            </template>
            <template #expected_close_date-cell="{ row }">
              {{ formatDate(row.original.expected_close_date) }}
            </template>
            <template #owner-cell="{ row }">
              {{ row.original.owner_id ? (ownerNames[row.original.owner_id] ?? '-') : '-' }}
            </template>
            <template #company-cell="{ row }">
              {{ row.original.company_id ? (companyNames[row.original.company_id] ?? '-') : '-' }}
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
    </template>

    <!-- Delete confirmation modal -->
    <UModal v-model:open="deleteModalOpen" :title="t('deals.confirm_delete_title')">
      <template #body>
        <p class="text-sm text-gray-600 dark:text-gray-300">
          {{ t('deals.confirm_delete_body', { title: deleteTarget?.title ?? '' }) }}
        </p>
      </template>

      <template #footer>
        <div class="flex justify-end gap-3">
          <AppButton color="neutral" variant="outline" :disabled="isDeleting" @click="deleteModalOpen = false">
            {{ t('common.cancel') }}
          </AppButton>
          <AppButton color="error" :loading="isDeleting" @click="onDelete">
            {{ t('deals.delete') }}
          </AppButton>
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import type { Ref } from 'vue'
import type { CompanySummary } from '~/types/companies'
import type {
  Deal,
  DealPriority,
  DealSortField,
  DealStage,
  DealStatus,
  DealType,
} from '~/types/deals'
import { DEAL_PRIORITIES, DEAL_STAGES, DEAL_STATUSES, DEAL_TYPES } from '~/types/deals'
import type { UserSummary } from '~/types/user'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t, locale } = useI18n()
const { user: currentUser } = useAuth()
const { list, remove } = useDeals()
const { lookup: lookupUsers } = useUsers()
const { lookup: lookupCompanies } = useCompanies()
const toast = useToast()
const route = useRoute()
const router = useRouter()

const pipelineRef = ref<{ refresh: () => void } | null>(null)

// ── URL-synced view/filter/sort/pagination state ────────────────────────────
// Kept in the URL query so the view is shareable/back-button friendly
// (same approach as companies/contacts).

const ALL = '__all__'
const SORTABLE_FIELDS: DealSortField[] = [
  'created_at', 'title', 'value', 'expected_close_date', 'probability', 'stage', 'status',
]
const sortableColumns = ['title', 'value', 'probability', 'expected_close_date', 'stage', 'status']

function inList<T extends string>(allowed: readonly T[], v: unknown): T | '' {
  return typeof v === 'string' && (allowed as readonly string[]).includes(v) ? v as T : ''
}

const q0 = route.query
const view = ref<'pipeline' | 'list'>(q0.view === 'list' ? 'list' : 'pipeline')
const page = ref(Number(q0.page) > 0 ? Number(q0.page) : 1)
const searchInput = ref(typeof q0.q === 'string' ? q0.q : '')
const q = ref(searchInput.value)
const stage = ref<DealStage | ''>(inList(DEAL_STAGES, q0.stage))
const status = ref<DealStatus | ''>(inList(DEAL_STATUSES, q0.status))
const dealType = ref<DealType | ''>(inList(DEAL_TYPES, q0.deal_type))
const priority = ref<DealPriority | ''>(inList(DEAL_PRIORITIES, q0.priority))
// Owner defaults to the signed-in user: a salesperson opening the board cares
// about their own pipeline first. `owner_id=all` in the URL is the explicit
// opt-out (managers, shared links) — distinguishing it from an absent param is
// what stops a cleared filter from silently snapping back to "mine" on reload.
// null here means "every owner".
const ALL_OWNERS = 'all'
const ownerId = ref<string | null>(
  typeof q0.owner_id === 'string'
    ? (q0.owner_id === ALL_OWNERS ? null : q0.owner_id)
    : (currentUser.value?.id ?? null),
)
const companyId = ref<string | null>(typeof q0.company_id === 'string' ? q0.company_id : null)
const contactId = ref<string | null>(typeof q0.contact_id === 'string' ? q0.contact_id : null)
const sort = ref<DealSortField>(
  (inList(SORTABLE_FIELDS, q0.sort) || 'created_at') as DealSortField,
)
const order = ref<'asc' | 'desc'>(q0.order === 'asc' ? 'asc' : 'desc')
const pageSize = 20

// Labels for the two picker-based filters, so they render a name on first load
// when arriving via a shared URL.
const ownerInitial = ref<UserSummary | null>(null)
const companyInitial = ref<CompanySummary | null>(null)

function selectModel<T extends string>(r: Ref<T | ''>) {
  return computed({
    get: () => r.value || ALL,
    set: (v: string) => { r.value = (v === ALL ? '' : v) as T | '' },
  })
}
const stageModel = selectModel(stage)
const statusModel = selectModel(status)
const dealTypeModel = selectModel(dealType)
const priorityModel = selectModel(priority)

const stageFilterOptions = computed(() => [
  { value: ALL, label: t('deals.filter_stage') },
  ...DEAL_STAGES.map(v => ({ value: v, label: t(`deals.stage.${v}`) })),
])
const statusFilterOptions = computed(() => [
  { value: ALL, label: t('deals.filter_status') },
  ...DEAL_STATUSES.map(v => ({ value: v, label: t(`deals.status.${v}`) })),
])
const dealTypeFilterOptions = computed(() => [
  { value: ALL, label: t('deals.filter_type') },
  ...DEAL_TYPES.map(v => ({ value: v, label: t(`deals.type.${v}`) })),
])
const priorityFilterOptions = computed(() => [
  { value: ALL, label: t('deals.filter_priority') },
  ...DEAL_PRIORITIES.map(v => ({ value: v, label: t(`deals.priority.${v}`) })),
])

// Owner counts as "active" only when it deviates from the default (me), so the
// clear-filters affordance does not appear on a freshly opened board.
const hasActiveFilters = computed(() =>
  !!(searchInput.value || stage.value || status.value || dealType.value
    || priority.value || companyId.value || contactId.value)
  || ownerId.value !== (currentUser.value?.id ?? null),
)

function clearFilters() {
  searchInput.value = ''
  stage.value = ''
  status.value = ''
  dealType.value = ''
  priority.value = ''
  companyId.value = null
  contactId.value = null
  companyInitial.value = null
  // Back to the default owner, not to "everyone" — clearing restores the
  // initial view rather than widening it.
  setOwner(currentUser.value?.id ?? null)
}

// Monotonic token so a slow lookup for a previously-picked owner can't land
// after a newer one and relabel the picker with the wrong person.
let ownerLabelSeq = 0

/**
 * Keep `ownerInitial` in step with `ownerId`.
 *
 * Picking someone other than yourself has to go through a lookup — without it
 * the label kept whatever it held before, and the picker only looked right
 * because it tracks its own selection internally. Anything that re-read
 * `ownerInitial` (a re-render, a shared link) would show the stale name.
 */
async function resolveOwnerLabel(id: string | null) {
  const seq = ++ownerLabelSeq
  if (!id) {
    ownerInitial.value = null
    return
  }
  const me = currentUser.value
  if (me && id === me.id) {
    // Already in memory — no round-trip for the common (default) case.
    ownerInitial.value = { id: me.id, full_name: me.full_name, email: me.email }
    return
  }
  try {
    const [owner] = await lookupUsers([id])
    if (seq === ownerLabelSeq) ownerInitial.value = owner ?? null
  }
  catch { /* picker keeps showing its own selection; label just stays as-is */ }
}

function setOwner(id: string | null) {
  ownerId.value = id
  void resolveOwnerLabel(id)
}

function toggleSort(col: string) {
  if (sort.value === col) {
    order.value = order.value === 'asc' ? 'desc' : 'asc'
  }
  else {
    sort.value = col as DealSortField
    order.value = 'asc'
  }
  page.value = 1
}

// Debounced search text input.
let searchDebounce: ReturnType<typeof setTimeout> | undefined
watch(searchInput, (v) => {
  if (searchDebounce) clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => { q.value = v; page.value = 1 }, 300)
})
onUnmounted(() => {
  if (searchDebounce) clearTimeout(searchDebounce)
})

// Any filter change resets to the first page.
watch([stage, status, dealType, priority, ownerId, companyId, contactId], () => { page.value = 1 })

// Sync state -> URL query (replace, not push, to avoid polluting history per keystroke).
watch([view, page, q, stage, status, dealType, priority, ownerId, companyId, contactId, sort, order], () => {
  router.replace({
    query: {
      ...(view.value === 'list' ? { view: 'list' } : {}),
      ...(page.value > 1 ? { page: String(page.value) } : {}),
      ...(q.value ? { q: q.value } : {}),
      ...(stage.value ? { stage: stage.value } : {}),
      ...(status.value ? { status: status.value } : {}),
      ...(dealType.value ? { deal_type: dealType.value } : {}),
      ...(priority.value ? { priority: priority.value } : {}),
      // Omitted when it equals the default (the signed-in user) to keep the
      // URL clean; 'all' is written explicitly so it survives a reload.
      ...(ownerId.value === null
        ? { owner_id: ALL_OWNERS }
        : ownerId.value !== currentUser.value?.id
          ? { owner_id: ownerId.value }
          : {}),
      ...(companyId.value ? { company_id: companyId.value } : {}),
      ...(contactId.value ? { contact_id: contactId.value } : {}),
      ...(sort.value !== 'created_at' ? { sort: sort.value } : {}),
      ...(order.value !== 'desc' ? { order: order.value } : {}),
    },
  })
})

// ── List state ───────────────────────────────────────────────────────────────

const items = ref<Deal[]>([])
const total = ref(0)
const isLoading = ref(false)
// id -> label maps, resolved once per page load instead of per row.
const ownerNames = ref<Record<string, string>>({})
const companyNames = ref<Record<string, string>>({})
const loadError = ref(false)

const columns = computed<TableColumn<Deal>[]>(() => [
  { accessorKey: 'title', id: 'title', header: t('deals.table.title') },
  { accessorKey: 'stage', id: 'stage', header: t('deals.table.stage') },
  { accessorKey: 'status', id: 'status', header: t('deals.table.status') },
  { accessorKey: 'value', id: 'value', header: t('deals.table.value') },
  { accessorKey: 'probability', id: 'probability', header: t('deals.table.probability') },
  { accessorKey: 'expected_close_date', id: 'expected_close_date', header: t('deals.table.expected_close_date') },
  { accessorKey: 'owner_id', id: 'owner', header: t('deals.table.owner') },
  { accessorKey: 'company_id', id: 'company', header: t('deals.table.company') },
  { id: 'actions', header: '' },
])

// expected_close_date is a calendar date, so it must render the same in every
// timezone — see formatCalendarDate in utils/date.ts.
function formatDate(value: string | null | undefined): string {
  return formatCalendarDate(value, locale.value)
}

// Monotonic token so a slow earlier request (e.g. rapid filter/sort changes on
// a slow network) can't overwrite a newer one's results.
let loadSeq = 0

async function loadDeals() {
  const seq = ++loadSeq
  isLoading.value = true
  loadError.value = false
  try {
    const res = await list({
      page: page.value,
      pageSize,
      q: q.value || undefined,
      stage: stage.value || undefined,
      status: status.value || undefined,
      dealType: dealType.value || undefined,
      priority: priority.value || undefined,
      ownerId: ownerId.value || undefined,
      companyId: companyId.value || undefined,
      contactId: contactId.value || undefined,
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
  // Labels are a secondary enrichment: resolved in one batched call each so a
  // failure degrades to "-" instead of blanking the already-loaded list.
  await loadLabels(items.value)
}

async function loadLabels(deals: Deal[]) {
  const ownerIds = [...new Set(deals.map(d => d.owner_id).filter((id): id is string => !!id))]
  const companyIds = [...new Set(deals.map(d => d.company_id).filter((id): id is string => !!id))]
  await Promise.all([
    (async () => {
      if (!ownerIds.length) { ownerNames.value = {}; return }
      try {
        const owners = await lookupUsers(ownerIds)
        ownerNames.value = Object.fromEntries(owners.map(o => [o.id, o.full_name]))
      }
      catch { ownerNames.value = {} }
    })(),
    (async () => {
      if (!companyIds.length) { companyNames.value = {}; return }
      try {
        const cs = await lookupCompanies(companyIds)
        companyNames.value = Object.fromEntries(cs.map(c => [c.id, c.name]))
      }
      catch { companyNames.value = {} }
    })(),
  ])
}

// Resolve labels for filters that arrived via the URL, so the pickers aren't
// blank on a shared link.
async function resolveFilterLabels() {
  await resolveOwnerLabel(ownerId.value)
  if (companyId.value) {
    try {
      const [company] = await lookupCompanies([companyId.value])
      companyInitial.value = company ?? null
    }
    catch { /* picker stays unlabelled */ }
  }
}

onMounted(async () => {
  await resolveFilterLabels()
  if (view.value === 'list') await loadDeals()
})

// Only the list view hits /deals with filters; the pipeline loads itself.
watch([view, page, q, stage, status, dealType, priority, ownerId, companyId, contactId, sort, order], () => {
  if (view.value === 'list') loadDeals()
})

function rowActions(row: Deal) {
  return [[
    {
      label: t('deals.actions.view'),
      icon: 'i-lucide-eye',
      onSelect: () => navigateTo(`/app/deals/${row.id}`),
    },
    {
      label: t('deals.actions.edit'),
      icon: 'i-lucide-pencil',
      onSelect: () => navigateTo(`/app/deals/${row.id}/edit`),
    },
    {
      label: t('deals.actions.delete'),
      icon: 'i-lucide-trash-2',
      onSelect: () => confirmDelete(row),
    },
  ]]
}

// ── Delete ───────────────────────────────────────────────────────────────────

const deleteModalOpen = ref(false)
const deleteTarget = ref<Deal | null>(null)
const isDeleting = ref(false)

function confirmDelete(row: Deal) {
  deleteTarget.value = row
  deleteModalOpen.value = true
}

async function onDelete() {
  if (!deleteTarget.value) return
  isDeleting.value = true
  try {
    await remove(deleteTarget.value.id)
    toast.add({ title: t('deals.deleted'), color: 'success', icon: 'i-lucide-check-circle' })
    deleteModalOpen.value = false
    deleteTarget.value = null
    // If we deleted the last row of a page > 1, step back one page
    // (the page watcher triggers the reload).
    if (items.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    else {
      await loadDeals()
    }
    pipelineRef.value?.refresh()
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

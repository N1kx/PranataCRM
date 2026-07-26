<template>
  <div>
    <!-- Error state -->
    <UAlert
      v-if="loadError"
      color="error"
      variant="soft"
      icon="i-lucide-circle-alert"
      :title="t('common.error_state')"
    >
      <template #description>
        <AppButton color="error" variant="outline" size="xs" class="mt-2" @click="load">
          {{ t('common.retry') }}
        </AppButton>
      </template>
    </UAlert>

    <!-- Loading state -->
    <div v-else-if="isLoading" class="text-center py-12 text-gray-400">
      <UIcon name="i-lucide-loader-circle" class="w-8 h-8 mx-auto mb-3 animate-spin" />
      <p class="text-sm">
        {{ t('common.loading') }}
      </p>
    </div>

    <!-- Board: horizontally scrollable, one column per stage -->
    <div v-else class="overflow-x-auto pb-2">
      <div class="flex gap-4 min-w-max">
        <div
          v-for="stage in DEAL_STAGES"
          :key="stage"
          class="w-72 shrink-0 rounded-lg border transition-colors"
          :class="dragOverStage === stage
            ? 'border-primary-400 bg-primary-50/50 dark:bg-primary-950/20'
            : 'border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/30'"
          @dragover.prevent
          @dragenter.prevent="dragOverStage = stage"
          @dragleave="onDragLeave(stage)"
          @drop="onDrop(stage)"
        >
          <!-- Column header: count + summed value of the loaded cards -->
          <div class="px-3 py-2 border-b border-gray-200 dark:border-gray-800">
            <div class="flex items-center justify-between">
              <DealsStageBadge :stage="stage" />
              <span class="text-xs text-gray-500">{{ totals[stage] ?? 0 }}</span>
            </div>
            <!-- One line per currency: totals are never summed across kurs. -->
            <p
              v-for="sum in columnSums(stage)"
              :key="sum"
              class="mt-1 text-xs text-gray-500 dark:text-gray-400"
            >
              {{ sum }}
            </p>
          </div>

          <div class="p-2 space-y-2 min-h-24">
            <p v-if="!columns[stage].length" class="text-center text-xs text-gray-400 py-6">
              {{ t('deals.pipeline.empty_column') }}
            </p>

            <div
              v-for="deal in columns[stage]"
              :key="deal.id"
              :draggable="!isAbandoned(deal)"
              class="rounded-md border bg-white dark:bg-gray-900 p-3 text-sm shadow-sm transition"
              :class="[
                isAbandoned(deal)
                  ? 'opacity-50 cursor-not-allowed border-gray-200 dark:border-gray-800'
                  : 'cursor-grab hover:shadow-md border-gray-200 dark:border-gray-800',
                movingId === deal.id ? 'animate-pulse' : '',
              ]"
              @dragstart="onDragStart(deal, stage, $event)"
              @dragend="onDragEnd"
            >
              <NuxtLink
                :to="`/app/deals/${deal.id}`"
                class="font-medium text-gray-900 dark:text-white hover:text-primary-600 dark:hover:text-primary-400 line-clamp-2"
              >
                {{ deal.title }}
              </NuxtLink>

              <p class="mt-1 font-semibold text-gray-900 dark:text-white">
                {{ formatMoney(deal.value, deal.currency, locale) }}
              </p>

              <div class="mt-1 space-y-0.5 text-xs text-gray-500 dark:text-gray-400">
                <p v-if="deal.company_id && companyNames[deal.company_id]" class="truncate">
                  <UIcon name="i-lucide-building-2" class="w-3 h-3 inline" />
                  {{ companyNames[deal.company_id] }}
                </p>
                <p v-if="deal.owner_id && ownerNames[deal.owner_id]" class="truncate">
                  <UIcon name="i-lucide-user" class="w-3 h-3 inline" />
                  {{ ownerNames[deal.owner_id] }}
                </p>
                <!-- table.* label, not fields.*: the latter already carries a
                     "(%)" suffix, which would double up with the value's. -->
                <p>{{ t('deals.table.probability') }}: {{ deal.probability }}%</p>
              </div>

              <div v-if="isAbandoned(deal)" class="mt-2">
                <UBadge color="neutral" variant="subtle" size="sm">
                  {{ t('deals.status.abandoned') }}
                </UBadge>
                <AppButton
                  color="neutral"
                  variant="outline"
                  size="xs"
                  class="mt-2 w-full"
                  :loading="reopeningId === deal.id"
                  @click="onReopen(deal)"
                >
                  {{ t('deals.actions.reopen') }}
                </AppButton>
              </div>
            </div>

            <!-- The board is capped per column; the long tail lives in the list view. -->
            <NuxtLink
              v-if="(totals[stage] ?? 0) > columns[stage].length"
              :to="`/app/deals?view=list&stage=${stage}`"
              class="block text-center text-xs text-primary-600 dark:text-primary-400 hover:underline py-2"
            >
              {{ t('deals.pipeline.more_in_list', { count: (totals[stage] ?? 0) - columns[stage].length }) }}
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>

    <!-- Reason modal for won/lost drops -->
    <DealsStageModal
      v-model:open="reasonModalOpen"
      :stage="pendingStage"
      :loading="isSubmittingReason"
      @confirm="onReasonConfirm"
      @cancel="onReasonCancel"
    />
  </div>
</template>

<script setup lang="ts">
import type { Deal, DealStage, StageChangePayload } from '~/types/deals'
import { DEAL_STAGES } from '~/types/deals'

/**
 * Pipeline kanban with drag-to-change-stage.
 *
 * Drag-and-drop uses the native HTML5 DnD API rather than pulling in a
 * dependency (vuedraggable et al). All of it is contained in the handlers
 * below (onDragStart/onDrop/onDragEnd) so swapping in a library later means
 * touching only this component.
 */

const props = defineProps<{
  /** Scope the board to one owner; null/undefined loads every owner's deals. */
  ownerId?: string | null
}>()

const emit = defineEmits<{
  /** Bubbled up so the page can refresh a sibling list view. */
  changed: []
}>()

const { t, locale } = useI18n()
const { list, moveStage, setStatus } = useDeals()
const { lookup: lookupUsers } = useUsers()
const { lookup: lookupCompanies } = useCompanies()
const toast = useToast()

/** Per-column cap — the board must never try to render thousands of cards. */
const COLUMN_CAP = 50

function emptyColumns(): Record<DealStage, Deal[]> {
  return { lead: [], qualified: [], proposal: [], won: [], lost: [] }
}

const columns = ref<Record<DealStage, Deal[]>>(emptyColumns())
const totals = ref<Partial<Record<DealStage, number>>>({})
const isLoading = ref(false)
const loadError = ref(false)
const ownerNames = ref<Record<string, string>>({})
const companyNames = ref<Record<string, string>>({})

const isAbandoned = (deal: Deal) => deal.status === 'abandoned'

/**
 * Column total(s), one formatted figure per currency present in the column.
 *
 * Deals in a column can carry different currencies, and there is no exchange
 * rate available client-side — so amounts are grouped by currency and summed
 * within each group. Adding them together and labelling the result with a
 * single currency would render a number that is simply wrong (a USD 48,000
 * deal would silently inflate an IDR column by 48,000 rupiah).
 *
 * Ordered by card count descending so the dominant currency leads, with the
 * currency code as a tiebreak to keep the order stable across reloads.
 */
function columnSums(stage: DealStage): string[] {
  const cards = columns.value[stage]
  if (!cards.length) return [formatMoney('0', 'IDR', locale.value)]

  const byCurrency = new Map<string, string[]>()
  for (const deal of cards) {
    const currency = deal.currency || 'IDR'
    const values = byCurrency.get(currency) ?? []
    values.push(deal.value)
    byCurrency.set(currency, values)
  }

  return [...byCurrency.entries()]
    .sort(([currA, a], [currB, b]) => b.length - a.length || currA.localeCompare(currB))
    .map(([currency, values]) => formatMoney(sumMoney(values), currency, locale.value))
}

// Monotonic token so a slow earlier load can't overwrite a newer one.
let loadSeq = 0

async function load() {
  const seq = ++loadSeq
  isLoading.value = true
  loadError.value = false
  try {
    const results = await Promise.all(
      DEAL_STAGES.map(stage => list({
        stage,
        ownerId: props.ownerId ?? undefined,
        pageSize: COLUMN_CAP,
        sort: 'created_at',
        order: 'desc',
      })),
    )
    if (seq !== loadSeq) return
    const next = emptyColumns()
    const nextTotals: Partial<Record<DealStage, number>> = {}
    DEAL_STAGES.forEach((stage, i) => {
      next[stage] = results[i]?.items ?? []
      nextTotals[stage] = results[i]?.total ?? 0
    })
    columns.value = next
    totals.value = nextTotals
  }
  catch {
    if (seq !== loadSeq) return
    loadError.value = true
    return
  }
  finally {
    if (seq === loadSeq) isLoading.value = false
  }
  // Labels are a secondary enrichment: resolved in one batched call each, and
  // a failure only leaves them blank rather than breaking the loaded board.
  await resolveLabels()
}

async function resolveLabels() {
  const all = DEAL_STAGES.flatMap(s => columns.value[s])
  const ownerIds = [...new Set(all.map(d => d.owner_id).filter((id): id is string => !!id))]
  const companyIds = [...new Set(all.map(d => d.company_id).filter((id): id is string => !!id))]

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

// ── Drag & drop ──────────────────────────────────────────────────────────────

const dragOverStage = ref<DealStage | null>(null)
const movingId = ref<string | null>(null)
const reopeningId = ref<string | null>(null)

/** The card currently being dragged, plus where it came from (for rollback). */
let dragged: { deal: Deal, from: DealStage, index: number } | null = null

function onDragStart(deal: Deal, from: DealStage, event: DragEvent) {
  if (isAbandoned(deal)) {
    // Abandoned deals can't change stage (backend 422s) — refuse the drag.
    event.preventDefault()
    return
  }
  dragged = { deal, from, index: columns.value[from].findIndex(d => d.id === deal.id) }
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    // Firefox only initiates a drag when some data is set.
    event.dataTransfer.setData('text/plain', deal.id)
  }
}

function onDragEnd() {
  dragOverStage.value = null
}

function onDragLeave(stage: DealStage) {
  if (dragOverStage.value === stage) dragOverStage.value = null
}

/** Move a card between columns in the local state only. */
function moveCard(deal: Deal, from: DealStage, to: DealStage, index?: number) {
  columns.value[from] = columns.value[from].filter(d => d.id !== deal.id)
  const target = [...columns.value[to]]
  target.splice(index ?? 0, 0, deal)
  columns.value[to] = target
  totals.value[from] = Math.max((totals.value[from] ?? 1) - 1, 0)
  totals.value[to] = (totals.value[to] ?? 0) + 1
}

const reasonModalOpen = ref(false)
const pendingStage = ref<DealStage>('won')
const isSubmittingReason = ref(false)
/** Set while a won/lost drop waits on the reason modal, so cancel can roll back. */
let pendingMove: { deal: Deal, from: DealStage, index: number, to: DealStage } | null = null

function onDrop(to: DealStage) {
  dragOverStage.value = null
  const d = dragged
  dragged = null
  if (!d || d.from === to) return

  // Optimistic: the card moves immediately, and is rolled back if the API call
  // (or the reason modal) does not go through.
  moveCard(d.deal, d.from, to)

  if (to === 'won' || to === 'lost') {
    // These carry side effects and (for lost) a required reason — collect it
    // before committing.
    pendingMove = { deal: d.deal, from: d.from, index: d.index, to }
    pendingStage.value = to
    reasonModalOpen.value = true
    return
  }

  void commitMove(d.deal, d.from, d.index, { stage: to })
}

function onReasonConfirm(payload: StageChangePayload) {
  const p = pendingMove
  if (!p) return
  isSubmittingReason.value = true
  void commitMove(p.deal, p.from, p.index, payload).finally(() => {
    isSubmittingReason.value = false
    reasonModalOpen.value = false
    pendingMove = null
  })
}

function onReasonCancel() {
  const p = pendingMove
  pendingMove = null
  if (!p) return
  // Roll the optimistic move back — nothing was sent.
  moveCard(p.deal, p.to, p.from, p.index)
}

/**
 * Commit an already-optimistically-applied move. On failure the card is
 * returned to its original column and index and the error is surfaced.
 */
async function commitMove(
  deal: Deal,
  from: DealStage,
  index: number,
  payload: StageChangePayload,
) {
  movingId.value = deal.id
  try {
    const updated = await moveStage(deal.id, payload)
    // Replace the optimistic card with the server's version, which carries the
    // derived status / probability / actual_close_date.
    const col = columns.value[payload.stage]
    const at = col.findIndex(d => d.id === deal.id)
    if (at !== -1) col[at] = updated
    emit('changed')
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    moveCard(deal, payload.stage, from, index)
    toast.add({
      title: t(`error.${e.code ?? 'unknown'}`, t('error.unknown')),
      color: 'error',
      icon: 'i-lucide-circle-alert',
    })
  }
  finally {
    movingId.value = null
  }
}

async function onReopen(deal: Deal) {
  reopeningId.value = deal.id
  try {
    const updated = await setStatus(deal.id, { status: 'open' })
    const col = columns.value[deal.stage]
    const at = col.findIndex(d => d.id === deal.id)
    if (at !== -1) col[at] = updated
    toast.add({ title: t('deals.reopened'), color: 'success', icon: 'i-lucide-check-circle' })
    emit('changed')
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
    reopeningId.value = null
  }
}

onMounted(load)

// Re-fetch when the page changes the owner scope. The load() sequence token
// already guards against an older request landing after a newer one.
watch(() => props.ownerId, load)

defineExpose({ refresh: load })
</script>

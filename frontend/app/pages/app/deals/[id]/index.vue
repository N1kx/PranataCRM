<template>
  <div class="space-y-6 max-w-3xl">
    <!-- Header -->
    <div class="flex items-start justify-between gap-3">
      <div class="flex items-center gap-3 flex-wrap">
        <UButton
          icon="i-lucide-arrow-left"
          color="neutral"
          variant="ghost"
          to="/app/deals"
          :aria-label="t('deals.back_to_list')"
        />
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ deal ? deal.title : t('deals.view') }}
        </h1>
        <DealsStageBadge v-if="deal" :stage="deal.stage" />
        <UBadge v-if="deal" :color="dealStatusColor(deal.status)" variant="subtle">
          {{ t(`deals.status.${deal.status}`) }}
        </UBadge>
      </div>

      <div v-if="deal" class="flex items-center gap-2 shrink-0">
        <!-- Stage is deliberately NOT part of the edit form: it only moves
             through PATCH /deals/{id}/stage, which applies side effects. -->
        <UDropdownMenu :items="stageMenuItems">
          <AppButton color="neutral" variant="outline" icon="i-lucide-git-branch" :loading="isMovingStage">
            {{ t('deals.actions.change_stage') }}
          </AppButton>
        </UDropdownMenu>
        <AppButton color="primary" icon="i-lucide-pencil" @click="navigateTo(`/app/deals/${dealId}/edit`)">
          {{ t('deals.actions.edit') }}
        </AppButton>
        <UDropdownMenu :items="moreMenuItems">
          <UButton color="neutral" variant="ghost" icon="i-lucide-ellipsis-vertical" />
        </UDropdownMenu>
      </div>
    </div>

    <!-- Error state -->
    <UAlert
      v-if="loadErrorCode"
      color="error"
      variant="soft"
      icon="i-lucide-circle-alert"
      :title="t(`error.${loadErrorCode}`, t('common.error_state'))"
    >
      <template #description>
        <AppButton color="error" variant="outline" size="xs" class="mt-2" @click="loadDeal">
          {{ t('common.retry') }}
        </AppButton>
      </template>
    </UAlert>

    <!-- Loading state -->
    <UCard v-else-if="isLoading">
      <div class="text-center py-12 text-gray-400">
        <UIcon name="i-lucide-loader-circle" class="w-8 h-8 mx-auto mb-3 animate-spin" />
        <p class="text-sm">
          {{ t('common.loading') }}
        </p>
      </div>
    </UCard>

    <!-- Detail -->
    <UCard v-else-if="deal">
      <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
        <!-- Company / contact link out to their own detail pages. -->
        <div>
          <dt class="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            {{ t('deals.fields.company_id') }}
          </dt>
          <dd class="mt-1 text-sm text-gray-900 dark:text-white">
            <NuxtLink
              v-if="deal.company_id && companyName"
              :to="`/app/companies/${deal.company_id}`"
              class="text-primary-600 dark:text-primary-400 hover:underline"
            >
              {{ companyName }}
            </NuxtLink>
            <span v-else>-</span>
          </dd>
        </div>
        <div>
          <dt class="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            {{ t('deals.fields.contact_id') }}
          </dt>
          <dd class="mt-1 text-sm text-gray-900 dark:text-white">
            <NuxtLink
              v-if="deal.contact_id && contactName"
              :to="`/app/contacts/${deal.contact_id}`"
              class="text-primary-600 dark:text-primary-400 hover:underline"
            >
              {{ contactName }}
            </NuxtLink>
            <span v-else>-</span>
          </dd>
        </div>

        <div v-for="field in detailFields" :key="field.label">
          <dt class="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            {{ field.label }}
          </dt>
          <dd class="mt-1 text-sm text-gray-900 dark:text-white">
            {{ field.value || '-' }}
          </dd>
        </div>
      </dl>

      <div v-if="deal.description" class="mt-6 pt-4 border-t border-gray-200 dark:border-gray-800">
        <dt class="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          {{ t('deals.fields.description') }}
        </dt>
        <dd class="mt-1 text-sm text-gray-900 dark:text-white whitespace-pre-line">
          {{ deal.description }}
        </dd>
      </div>
    </UCard>

    <!-- Reason modal for won/lost stage moves -->
    <DealsStageModal
      v-model:open="reasonModalOpen"
      :stage="pendingStage"
      :loading="isMovingStage"
      @confirm="onStageConfirm"
    />

    <!-- Delete confirmation modal -->
    <UModal v-model:open="deleteModalOpen" :title="t('deals.confirm_delete_title')">
      <template #body>
        <p class="text-sm text-gray-600 dark:text-gray-300">
          {{ t('deals.confirm_delete_body', { title: deal?.title ?? '' }) }}
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
import type { Deal, DealStage, StageChangePayload } from '~/types/deals'
import { DEAL_STAGES } from '~/types/deals'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t, locale } = useI18n()
const { get, moveStage, setStatus, remove } = useDeals()
const { lookup: lookupUsers } = useUsers()
const { lookup: lookupCompanies } = useCompanies()
const { lookup: lookupContacts } = useContacts()
const toast = useToast()
const route = useRoute()

const dealId = route.params.id as string
const deal = ref<Deal | null>(null)
const isLoading = ref(false)
const loadErrorCode = ref('')
const ownerName = ref('')
const companyName = ref('')
const contactName = ref('')

async function loadDeal() {
  isLoading.value = true
  loadErrorCode.value = ''
  ownerName.value = ''
  companyName.value = ''
  contactName.value = ''
  try {
    deal.value = await get(dealId)
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    loadErrorCode.value = e.code ?? 'unknown'
    return
  }
  finally {
    isLoading.value = false
  }
  if (deal.value) await resolveLabels(deal.value)
}

/**
 * Resolve owner/company/contact ids to names. Each is independently guarded so
 * a failed lookup only blanks that one label — the deal itself still renders.
 */
async function resolveLabels(d: Deal) {
  await Promise.all([
    (async () => {
      if (!d.owner_id) return
      try {
        const [owner] = await lookupUsers([d.owner_id])
        ownerName.value = owner?.full_name ?? ''
      }
      catch { ownerName.value = '' }
    })(),
    (async () => {
      if (!d.company_id) return
      try {
        const [company] = await lookupCompanies([d.company_id])
        companyName.value = company?.name ?? ''
      }
      catch { companyName.value = '' }
    })(),
    (async () => {
      if (!d.contact_id) return
      try {
        const [contact] = await lookupContacts([d.contact_id])
        contactName.value = contact?.name ?? ''
      }
      catch { contactName.value = '' }
    })(),
  ])
}

onMounted(loadDeal)

// Calendar dates (close/next-step dates) must not shift with the viewer's
// timezone; created_at below is an instant and deliberately does convert.
function formatDate(value: string | null | undefined): string {
  return formatCalendarDate(value, locale.value, '')
}

const detailFields = computed(() => {
  const d = deal.value
  if (!d) return []
  return [
    { label: t('deals.fields.owner_id'), value: ownerName.value },
    { label: t('deals.fields.value'), value: formatMoney(d.value, d.currency, locale.value) },
    // Server-computed — displayed, never editable.
    { label: t('deals.fields.weighted_value'), value: formatMoney(d.weighted_value, d.currency, locale.value) },
    { label: t('deals.fields.probability'), value: `${d.probability}%` },
    { label: t('deals.fields.deal_type'), value: d.deal_type ? t(`deals.type.${d.deal_type}`) : '' },
    { label: t('deals.fields.priority'), value: d.priority ? t(`deals.priority.${d.priority}`) : '' },
    { label: t('deals.fields.expected_close_date'), value: formatDate(d.expected_close_date) },
    { label: t('deals.fields.actual_close_date'), value: formatDate(d.actual_close_date) },
    { label: t('deals.fields.source'), value: d.source },
    { label: t('deals.fields.competitor'), value: d.competitor },
    { label: t('deals.fields.next_step'), value: d.next_step },
    { label: t('deals.fields.next_step_date'), value: formatDate(d.next_step_date) },
    { label: t('deals.fields.close_reason'), value: d.close_reason },
    { label: t('deals.fields.lost_reason'), value: d.lost_reason },
    // An instant, not a calendar date — showing it in the reader's own
    // timezone is the correct behaviour here.
    { label: t('deals.fields.created_at'), value: formatInstant(d.created_at, locale.value) },
  ]
})

// ── Stage change ─────────────────────────────────────────────────────────────

const isMovingStage = ref(false)
const reasonModalOpen = ref(false)
const pendingStage = ref<DealStage>('won')

const stageMenuItems = computed(() => [
  DEAL_STAGES.map(stage => ({
    label: t(`deals.stage.${stage}`),
    // An abandoned deal must be reopened before its stage can change (the
    // backend 422s), and the current stage is a no-op.
    disabled: !deal.value || deal.value.stage === stage || deal.value.status === 'abandoned',
    onSelect: () => requestStage(stage),
  })),
])

function requestStage(stage: DealStage) {
  if (stage === 'won' || stage === 'lost') {
    // These need a reason (required for lost) — collect it first.
    pendingStage.value = stage
    reasonModalOpen.value = true
    return
  }
  void applyStage({ stage })
}

function onStageConfirm(payload: StageChangePayload) {
  void applyStage(payload).then(() => { reasonModalOpen.value = false })
}

async function applyStage(payload: StageChangePayload) {
  isMovingStage.value = true
  try {
    deal.value = await moveStage(dealId, payload)
    toast.add({ title: t('deals.stage_changed'), color: 'success', icon: 'i-lucide-check-circle' })
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
    isMovingStage.value = false
  }
}

// ── Abandon / reopen / delete ────────────────────────────────────────────────

const moreMenuItems = computed(() => {
  const d = deal.value
  const abandoned = d?.status === 'abandoned'
  return [[
    {
      label: abandoned ? t('deals.actions.reopen') : t('deals.actions.abandon'),
      icon: abandoned ? 'i-lucide-rotate-ccw' : 'i-lucide-ban',
      // won/lost are terminal here: they only change via the stage endpoint.
      disabled: !d || (d.status !== 'open' && d.status !== 'abandoned'),
      onSelect: () => toggleAbandoned(),
    },
    {
      label: t('deals.actions.delete'),
      icon: 'i-lucide-trash-2',
      onSelect: () => { deleteModalOpen.value = true },
    },
  ]]
})

async function toggleAbandoned() {
  const d = deal.value
  if (!d) return
  const next = d.status === 'abandoned' ? 'open' : 'abandoned'
  try {
    deal.value = await setStatus(dealId, { status: next })
    toast.add({
      title: next === 'open' ? t('deals.reopened') : t('deals.abandoned'),
      color: 'success',
      icon: 'i-lucide-check-circle',
    })
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    toast.add({
      title: t(`error.${e.code ?? 'unknown'}`, t('error.unknown')),
      color: 'error',
      icon: 'i-lucide-circle-alert',
    })
  }
}

const deleteModalOpen = ref(false)
const isDeleting = ref(false)

async function onDelete() {
  isDeleting.value = true
  try {
    await remove(dealId)
    toast.add({ title: t('deals.deleted'), color: 'success', icon: 'i-lucide-check-circle' })
    await navigateTo('/app/deals')
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

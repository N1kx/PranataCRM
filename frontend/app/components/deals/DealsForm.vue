<template>
  <UForm :schema="schema" :state="form" class="space-y-4" @submit="onSubmit">
    <UAlert
      v-if="formError"
      color="error"
      variant="soft"
      :description="formError"
      icon="i-lucide-circle-alert"
    />

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <AppField :label="t('deals.fields.title')" name="title" required>
        <AppInput v-model="form.title" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('deals.fields.expected_close_date')" name="expected_close_date" required>
        <AppInput v-model="form.expected_close_date" type="date" :disabled="isSaving" />
      </AppField>

      <AppField :label="t('deals.fields.company_id')" name="company_id" :error="fieldErrors.company_id">
        <AppCompanySelect
          v-model="form.company_id"
          :initial="companyInitial"
          :disabled="isSaving"
        />
      </AppField>
      <AppField :label="t('deals.fields.contact_id')" name="contact_id" :error="fieldErrors.contact_id">
        <AppContactSelect
          v-model="form.contact_id"
          :initial="contactInitial"
          :company-id="form.company_id"
          :disabled="isSaving"
        />
      </AppField>
      <AppField :label="t('deals.fields.owner_id')" name="owner_id" :error="fieldErrors.owner_id">
        <AppUserSelect v-model="form.owner_id" :initial="ownerInitial" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('deals.fields.deal_type')" name="deal_type">
        <USelect v-model="dealTypeModel" :items="dealTypeOptions" :disabled="isSaving" class="w-full" />
      </AppField>

      <AppField :label="t('deals.fields.value')" name="value">
        <AppInput v-model="form.value" type="number" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('deals.fields.currency')" name="currency" required>
        <AppInput v-model="form.currency" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('deals.fields.probability')" name="probability">
        <AppInput v-model="form.probability" type="number" :disabled="isSaving" />
      </AppField>
      <!-- Server-computed: shown so the user can see the effect of value x
           probability, but never part of the payload. -->
      <AppField :label="t('deals.fields.weighted_value')" name="weighted_value">
        <div class="h-8 flex items-center text-sm text-gray-500 dark:text-gray-400">
          {{ weightedPreview }}
        </div>
      </AppField>

      <AppField :label="t('deals.fields.priority')" name="priority">
        <USelect v-model="priorityModel" :items="priorityOptions" :disabled="isSaving" class="w-full" />
      </AppField>
      <AppField :label="t('deals.fields.source')" name="source">
        <AppInput v-model="form.source" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('deals.fields.competitor')" name="competitor">
        <AppInput v-model="form.competitor" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('deals.fields.next_step')" name="next_step">
        <AppInput v-model="form.next_step" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('deals.fields.next_step_date')" name="next_step_date">
        <AppInput v-model="form.next_step_date" type="date" :disabled="isSaving" />
      </AppField>
    </div>

    <AppField :label="t('deals.fields.description')" name="description">
      <UTextarea v-model="form.description" :rows="3" :disabled="isSaving" class="w-full" />
    </AppField>

    <div class="flex justify-end gap-3">
      <AppButton color="neutral" variant="outline" :disabled="isSaving" @click="emit('cancel')">
        {{ t('common.cancel') }}
      </AppButton>
      <AppButton type="submit" color="primary" :loading="isSaving">
        {{ isSaving ? t('deals.submitting') : t('common.save') }}
      </AppButton>
    </div>
  </UForm>
</template>

<script setup lang="ts">
import { z } from 'zod'
import type { CompanySummary } from '~/types/companies'
import type { ContactSummary } from '~/types/contacts'
import type { Deal, DealPriority, DealType, DealUpdatePayload } from '~/types/deals'
import { DEAL_PRIORITIES, DEAL_TYPES } from '~/types/deals'
import type { UserSummary } from '~/types/user'

const props = defineProps<{
  /** Deal to edit; omit for create mode. */
  deal?: Deal | null
  /** Create-mode prefill from ?company_id= (already resolved to a label). */
  prefillCompany?: CompanySummary | null
  /** Create-mode prefill from ?contact_id= (already resolved to a label). */
  prefillContact?: ContactSummary | null
}>()

const emit = defineEmits<{
  saved: [deal: Deal]
  cancel: []
}>()

const { t, locale } = useI18n()
const { create, update } = useDeals()
const { user: currentUser } = useAuth()
const { lookup: lookupUsers } = useUsers()
const { lookup: lookupCompanies } = useCompanies()
const { lookup: lookupContacts } = useContacts()

const isSaving = ref(false)
const formError = ref('')
// Per-reference 422s from the backend are surfaced on the matching picker
// rather than as a generic banner.
const fieldErrors = reactive<Record<string, string>>({
  owner_id: '',
  company_id: '',
  contact_id: '',
})

// Resolved labels so each picker renders a name immediately instead of a blank
// box while it searches.
const ownerInitial = ref<UserSummary | null>(null)
const companyInitial = ref<CompanySummary | null>(null)
const contactInitial = ref<ContactSummary | null>(null)

const emptyForm = {
  title: '',
  expected_close_date: '',
  contact_id: null as string | null,
  company_id: null as string | null,
  owner_id: null as string | null,
  deal_type: '' as DealType | '',
  // Money stays a string end-to-end — never parsed into a JS number.
  value: '0',
  currency: 'IDR',
  probability: '0',
  priority: '' as DealPriority | '',
  source: '',
  next_step: '',
  next_step_date: '',
  competitor: '',
  description: '',
}

const form = reactive({ ...emptyForm })
let original = { ...emptyForm }

watch(() => props.deal, async (deal) => {
  if (!deal) {
    // Create mode: default the owner to the logged-in user (still changeable),
    // and honour any ?company_id=/?contact_id= prefill from the caller.
    Object.assign(form, emptyForm, {
      owner_id: currentUser.value?.id ?? null,
      company_id: props.prefillCompany?.id ?? null,
      contact_id: props.prefillContact?.id ?? null,
    })
    original = { ...form }
    ownerInitial.value = currentUser.value
      ? { id: currentUser.value.id, full_name: currentUser.value.full_name, email: currentUser.value.email }
      : null
    companyInitial.value = props.prefillCompany ?? null
    contactInitial.value = props.prefillContact ?? null
    return
  }

  Object.assign(form, {
    title: deal.title,
    expected_close_date: deal.expected_close_date ?? '',
    contact_id: deal.contact_id ?? null,
    company_id: deal.company_id ?? null,
    owner_id: deal.owner_id ?? null,
    deal_type: deal.deal_type ?? '',
    value: deal.value ?? '0',
    currency: deal.currency,
    probability: String(deal.probability ?? 0),
    priority: deal.priority ?? '',
    source: deal.source ?? '',
    next_step: deal.next_step ?? '',
    next_step_date: deal.next_step_date ?? '',
    competitor: deal.competitor ?? '',
    description: deal.description ?? '',
  })
  original = { ...form }

  // Resolve the three picker labels in parallel; each failure only leaves that
  // picker unlabelled, it must not block the form from rendering.
  ownerInitial.value = null
  companyInitial.value = null
  contactInitial.value = null
  await Promise.all([
    (async () => {
      if (!deal.owner_id) return
      try {
        const [owner] = await lookupUsers([deal.owner_id])
        ownerInitial.value = owner ?? null
      }
      catch { /* label stays blank */ }
    })(),
    (async () => {
      if (!deal.company_id) return
      try {
        const [company] = await lookupCompanies([deal.company_id])
        companyInitial.value = company ?? null
      }
      catch { /* label stays blank */ }
    })(),
    (async () => {
      if (!deal.contact_id) return
      try {
        const [contact] = await lookupContacts([deal.contact_id])
        contactInitial.value = contact ?? null
      }
      catch { /* label stays blank */ }
    })(),
  ])
}, { immediate: true })

const weightedPreview = computed(() =>
  formatMoney(
    computeWeightedValue(form.value || '0', Number(form.probability) || 0),
    form.currency || 'IDR',
    // Pass the active locale so this matches the formatting used on the list,
    // board and detail views rather than falling back to the id-ID default.
    locale.value,
  ),
)

// Mirrors the implemented backend (backend/app/modules/deals/schemas.py) so the
// user never hits an avoidable 422.
const maxMsg = (max: number) => t('deals.validation.max_length', { max })
const schema = computed(() => z.object({
  title: z.string()
    .trim()
    .min(1, t('deals.validation.title_required'))
    .max(255, maxMsg(255)),
  expected_close_date: z.string()
    .trim()
    .min(1, t('deals.validation.expected_close_date_required'))
    // Both past and future dates are legitimate (overdue/backdated deals).
    .regex(/^\d{4}-\d{2}-\d{2}$/, t('deals.validation.date_invalid')),
  // Money is validated as a decimal string; it is never parsed to a number.
  value: z.literal('').or(
    z.string().trim().regex(/^\d+(\.\d{1,2})?$/, t('deals.validation.value_invalid')),
  ),
  currency: z.string()
    .trim()
    .toUpperCase()
    .regex(/^[A-Z]{3}$/, t('deals.validation.currency_invalid')),
  probability: z.literal('').or(
    z.string().trim().regex(/^\d{1,3}$/, t('deals.validation.probability_invalid'))
      .refine(v => Number(v) >= 0 && Number(v) <= 100, t('deals.validation.probability_invalid')),
  ),
  deal_type: z.literal('').or(z.enum(DEAL_TYPES as [DealType, ...DealType[]])),
  priority: z.literal('').or(z.enum(DEAL_PRIORITIES as [DealPriority, ...DealPriority[]])),
  source: z.string().max(50, maxMsg(50)),
  competitor: z.string().max(255, maxMsg(255)),
  next_step: z.string(),
  next_step_date: z.literal('').or(
    z.string().trim().regex(/^\d{4}-\d{2}-\d{2}$/, t('deals.validation.date_invalid')),
  ),
  description: z.string(),
}))

// Reka UI's <SelectItem/> rejects an empty-string value (it's reserved to mean
// "cleared"), so the "none" option needs a non-empty sentinel. The form state
// itself stays '' internally (matching the API/Zod schema); these computeds
// only translate at the UI boundary.
const NONE_SENTINEL = '__none__'

const dealTypeOptions = computed(() => [
  { value: NONE_SENTINEL, label: t('deals.type.none') },
  ...DEAL_TYPES.map(value => ({ value, label: t(`deals.type.${value}`) })),
])
const dealTypeModel = computed({
  get: () => form.deal_type || NONE_SENTINEL,
  set: (v: string) => { form.deal_type = (v === NONE_SENTINEL ? '' : v) as DealType | '' },
})

const priorityOptions = computed(() => [
  { value: NONE_SENTINEL, label: t('deals.priority.none') },
  ...DEAL_PRIORITIES.map(value => ({ value, label: t(`deals.priority.${value}`) })),
])
const priorityModel = computed({
  get: () => form.priority || NONE_SENTINEL,
  set: (v: string) => { form.priority = (v === NONE_SENTINEL ? '' : v) as DealPriority | '' },
})

// Columns that are NOT NULL on the backend: they may never be sent as an
// explicit null, so a blank falls back to its default instead of clearing.
const NON_NULLABLE = new Set(['title', 'expected_close_date', 'value', 'currency', 'probability'])
const DEFAULTS: Record<string, string> = { value: '0', probability: '0', currency: 'IDR' }

/**
 * Build the payload: trim strings, keep money as strings, drop empty optional
 * fields, and in edit mode only include fields whose value changed (partial
 * PATCH). `stage`, `status` and `weighted_value` are structurally absent from
 * the form, so they can never be sent.
 */
function buildPayload(): DealUpdatePayload {
  const payload: Record<string, unknown> = {}
  for (const [key, raw] of Object.entries(form)) {
    let value: unknown = typeof raw === 'string' ? raw.trim() : raw
    if (key === 'currency' && typeof value === 'string') value = value.toUpperCase()
    // probability is an integer on the wire; value/weighted_value stay strings.
    if (key === 'probability') value = Number(value === '' ? DEFAULTS.probability : value)
    if (NON_NULLABLE.has(key) && value === '') value = DEFAULTS[key] ?? ''

    if (props.deal) {
      const originalRaw = original[key as keyof typeof original]
      const originalValue = key === 'probability' ? Number(originalRaw || 0) : originalRaw
      if (value === originalValue) continue
      if (value === '' && !NON_NULLABLE.has(key)) {
        // Was populated, now cleared — send an explicit null so the backend
        // actually unsets it. Omitting it would silently keep the stale value.
        payload[key] = null
        continue
      }
      payload[key] = value
      continue
    }

    // Create mode: omit blank optional fields so required-field validation
    // surfaces its own clear error rather than a generic "may not be null".
    if (value === '' && !NON_NULLABLE.has(key)) continue
    payload[key] = value
  }
  return payload as DealUpdatePayload
}

const REFERENCE_ERRORS: Record<string, string> = {
  INVALID_OWNER_REFERENCE: 'owner_id',
  INVALID_COMPANY_REFERENCE: 'company_id',
  INVALID_CONTACT_REFERENCE: 'contact_id',
}

async function onSubmit() {
  formError.value = ''
  fieldErrors.owner_id = ''
  fieldErrors.company_id = ''
  fieldErrors.contact_id = ''
  isSaving.value = true
  try {
    let saved: Deal
    if (props.deal) {
      const payload = buildPayload()
      saved = Object.keys(payload).length > 0
        ? await update(props.deal.id, payload)
        : props.deal
    }
    else {
      saved = await create({
        ...buildPayload(),
        title: form.title.trim(),
        expected_close_date: form.expected_close_date.trim(),
      })
    }
    emit('saved', saved)
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    const field = e.code ? REFERENCE_ERRORS[e.code] : undefined
    if (field) {
      fieldErrors[field] = t(`error.${e.code}`)
    }
    else {
      formError.value = t(`error.${e.code ?? 'unknown'}`, t('error.unknown'))
    }
  }
  finally {
    isSaving.value = false
  }
}
</script>

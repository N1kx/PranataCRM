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
      <AppField :label="t('companies.fields.name')" name="name" required>
        <AppInput v-model="form.name" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('companies.fields.legal_name')" name="legal_name">
        <AppInput v-model="form.legal_name" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('companies.owner')" name="owner_id">
        <AppUserSelect v-model="form.owner_id" :initial="ownerInitial" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('companies.fields.domain')" name="domain">
        <AppInput v-model="form.domain" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('companies.fields.website')" name="website">
        <AppInput v-model="form.website" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('companies.fields.email')" name="email">
        <AppInput v-model="form.email" type="email" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('companies.fields.phone')" name="phone" required>
        <AppInput v-model="form.phone" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('companies.fields.industry')" name="industry">
        <AppInput v-model="form.industry" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('companies.fields.size')" name="size">
        <USelect v-model="sizeModel" :items="sizeOptions" :disabled="isSaving" class="w-full" />
      </AppField>
      <AppField :label="t('companies.fields.employee_count')" name="employee_count">
        <AppInput v-model="form.employee_count" type="number" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('companies.fields.company_type')" name="company_type">
        <USelect v-model="form.company_type" :items="companyTypeOptions" :disabled="isSaving" class="w-full" />
      </AppField>
      <AppField :label="t('companies.fields.status')" name="status">
        <USelect v-model="form.status" :items="statusOptions" :disabled="isSaving" class="w-full" />
      </AppField>
      <AppField :label="t('companies.fields.source')" name="source">
        <AppInput v-model="form.source" :disabled="isSaving" />
      </AppField>
      <!-- Renders as 3 separate fields (Country / State / City), each with
           its own label; State disabled until Country is picked, City
           disabled until State is picked — see AppLocationSelect.vue. -->
      <AppLocationSelect
        :country="form.country"
        :state="form.state"
        :city="form.city"
        :disabled="isSaving"
        @update:country="form.country = $event ?? ''"
        @update:state="form.state = $event ?? ''"
        @update:city="form.city = $event ?? ''"
      />
      <AppField :label="t('companies.fields.linkedin_url')" name="linkedin_url">
        <AppInput v-model="form.linkedin_url" :disabled="isSaving" />
      </AppField>
    </div>
    <AppField :label="t('companies.fields.description')" name="description">
      <UTextarea v-model="form.description" :rows="3" :disabled="isSaving" class="w-full" />
    </AppField>

    <div class="flex justify-end gap-3">
      <AppButton color="neutral" variant="outline" :disabled="isSaving" @click="emit('cancel')">
        {{ t('common.cancel') }}
      </AppButton>
      <AppButton type="submit" color="primary" :loading="isSaving">
        {{ isSaving ? t('companies.submitting') : t('common.save') }}
      </AppButton>
    </div>
  </UForm>
</template>

<script setup lang="ts">
import { z } from 'zod'
import type { Company, CompanySize, CompanyStatus, CompanyType, CompanyUpdatePayload } from '~/types/companies'
import type { UserSummary } from '~/types/user'

const props = defineProps<{
  /** Company to edit; omit for create mode. */
  company?: Company | null
}>()

const emit = defineEmits<{
  saved: []
  cancel: []
}>()

const { t } = useI18n()
const { create, update } = useCompanies()
const { user: currentUser } = useAuth()
const { lookup } = useUsers()

const COMPANY_TYPES: CompanyType[] = ['prospect', 'customer', 'partner', 'vendor', 'competitor', 'other']
const COMPANY_SIZES: CompanySize[] = ['1-10', '11-50', '51-200', '201-500', '500+']
const COMPANY_STATUSES: CompanyStatus[] = ['active', 'inactive']

const isSaving = ref(false)
const formError = ref('')
// Resolved label for the currently selected owner, so AppUserSelect can render
// a name immediately instead of a blank box while it searches.
const ownerInitial = ref<UserSummary | null>(null)

const emptyForm = {
  owner_id: null as string | null,
  name: '',
  legal_name: '',
  domain: '',
  website: '',
  email: '',
  phone: '',
  industry: '',
  size: '' as CompanySize | '',
  employee_count: '',
  company_type: 'prospect' as CompanyType,
  status: 'active' as CompanyStatus,
  source: '',
  city: '',
  state: '',
  country: '',
  linkedin_url: '',
  description: '',
}

const form = reactive({ ...emptyForm })
let original = { ...emptyForm }

watch(() => props.company, async (company) => {
  if (!company) {
    // Create mode: default the owner to the logged-in user (still changeable).
    Object.assign(form, emptyForm, { owner_id: currentUser.value?.id ?? null })
    original = { ...form }
    ownerInitial.value = currentUser.value
      ? { id: currentUser.value.id, full_name: currentUser.value.full_name, email: currentUser.value.email }
      : null
    return
  }
  Object.assign(form, {
    owner_id: company.owner_id ?? null,
    name: company.name,
    legal_name: company.legal_name ?? '',
    domain: company.domain ?? '',
    website: company.website ?? '',
    email: company.email ?? '',
    phone: company.phone ?? '',
    industry: company.industry ?? '',
    size: company.size ?? '',
    employee_count: company.employee_count != null ? String(company.employee_count) : '',
    company_type: company.company_type,
    status: company.status,
    source: company.source ?? '',
    city: company.city ?? '',
    state: company.state ?? '',
    country: company.country ?? '',
    linkedin_url: company.linkedin_url ?? '',
    description: company.description ?? '',
  })
  original = { ...form }

  ownerInitial.value = null
  if (company.owner_id) {
    const [owner] = await lookup([company.owner_id])
    ownerInitial.value = owner ?? null
  }
}, { immediate: true })

// Mirrors the implemented backend (backend/app/modules/companies/schemas.py)
// so the user never hits an avoidable 422.
const maxMsg = (max: number) => t('companies.validation.max_length', { max })
const urlMsg = t('companies.validation.url_invalid')
const optionalUrl = z.literal('').or(z.string().trim().url(urlMsg))
const schema = computed(() => z.object({
  name: z.string()
    .trim()
    .min(1, t('companies.validation.name_required'))
    .max(255, maxMsg(255)),
  legal_name: z.string().max(255, maxMsg(255)),
  domain: z.literal('').or(
    z.string().trim().max(255, maxMsg(255))
      .refine(v => !v.includes('://') && !v.includes(' '), t('companies.validation.domain_invalid')),
  ),
  website: optionalUrl,
  email: z.literal('').or(
    z.string().trim().email(t('companies.validation.email_invalid')).max(254, maxMsg(254)),
  ),
  phone: z.string()
    .trim()
    .min(1, t('companies.validation.phone_required'))
    .max(50, maxMsg(50))
    .regex(/^[0-9+\-() ]+$/, t('companies.validation.phone_invalid')),
  industry: z.string().max(100, maxMsg(100)),
  size: z.literal('').or(z.enum(COMPANY_SIZES as [CompanySize, ...CompanySize[]])),
  employee_count: z.literal('').or(
    z.string().regex(/^\d+$/, t('companies.validation.employee_count_invalid')),
  ),
  company_type: z.enum(COMPANY_TYPES as [CompanyType, ...CompanyType[]]),
  status: z.enum(COMPANY_STATUSES as [CompanyStatus, ...CompanyStatus[]]),
  source: z.string().max(50, maxMsg(50)),
  // country/state/city come from AppLocationSelect (issue #26), not free
  // text — always '' or a valid code/id picked from the backend's list, so
  // no length/format check is needed here (the backend still validates
  // existence + cascade consistency on submit).
  city: z.string(),
  state: z.string(),
  country: z.string().min(1, t('companies.validation.country_required')),
  linkedin_url: optionalUrl,
  description: z.string(),
}))

const statusOptions = computed(() =>
  COMPANY_STATUSES.map(value => ({ value, label: t(`companies.status.${value}`) })),
)
const companyTypeOptions = computed(() =>
  COMPANY_TYPES.map(value => ({ value, label: t(`companies.type.${value}`) })),
)

// Reka UI's <SelectItem/> rejects an empty-string value (it's reserved to mean
// "cleared"), so the "no size" option needs a non-empty sentinel.
// form.size itself stays '' internally (matches the API/Zod schema); this
// computed just translates at the UI boundary.
const NONE_SENTINEL = '__none__'
const sizeOptions = computed(() => [
  { value: NONE_SENTINEL, label: t('companies.size.none') },
  ...COMPANY_SIZES.map(value => ({ value, label: value })),
])
const sizeModel = computed({
  get: () => form.size || NONE_SENTINEL,
  set: (v: string) => {
    form.size = (v === NONE_SENTINEL ? '' : v) as CompanySize | ''
  },
})

/**
 * Build the payload: trim strings, drop empty optional fields, and in edit
 * mode only include fields whose value changed (partial PATCH).
 */
function buildPayload(): CompanyUpdatePayload {
  const payload: Record<string, unknown> = {}
  for (const [key, raw] of Object.entries(form)) {
    let value: unknown = typeof raw === 'string' ? raw.trim() : raw
    if (key === 'employee_count' && value !== '') value = Number(value)

    if (props.company) {
      const originalValue = original[key as keyof typeof original]
      if (value === originalValue) continue
      if (value === '' && key !== 'name' && key !== 'phone' && key !== 'country') {
        // Was populated, now cleared - send an explicit null so the backend
        // actually unsets it. Omitting it here would silently keep the
        // stale DB value (see ContactsForm.vue's buildPayload / PR #39 review).
        payload[key] = null
        continue
      }
      payload[key] = value
      continue
    }

    // Create mode: omit blank optional fields so required-field validation
    // surfaces its own clear error rather than a generic "may not be null".
    if (value === '' && key !== 'name' && key !== 'phone' && key !== 'country') continue
    payload[key] = value
  }
  return payload as CompanyUpdatePayload
}

async function onSubmit() {
  formError.value = ''
  isSaving.value = true
  try {
    if (props.company) {
      const payload = buildPayload()
      if (Object.keys(payload).length > 0) {
        await update(props.company.id, payload)
      }
    }
    else {
      await create({
        ...buildPayload(),
        name: form.name.trim(),
        phone: form.phone.trim(),
        country: form.country.trim(),
      })
    }
    emit('saved')
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    if (e.code === 'INVALID_OWNER_REFERENCE') {
      formError.value = t('error.INVALID_OWNER_REFERENCE')
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

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
      <AppField :label="t('contacts.fields.first_name')" name="first_name" required>
        <AppInput v-model="form.first_name" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('contacts.fields.last_name')" name="last_name">
        <AppInput v-model="form.last_name" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('contacts.owner')" name="owner_id">
        <AppUserSelect v-model="form.owner_id" :initial="ownerInitial" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('contacts.fields.email')" name="email">
        <AppInput v-model="form.email" type="email" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('contacts.fields.phone')" name="phone">
        <AppInput v-model="form.phone" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('contacts.fields.mobile_phone')" name="mobile_phone">
        <AppInput v-model="form.mobile_phone" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('contacts.fields.job_title')" name="job_title">
        <AppInput v-model="form.job_title" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('contacts.fields.department')" name="department">
        <AppInput v-model="form.department" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('contacts.fields.lead_source')" name="lead_source">
        <AppInput v-model="form.lead_source" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('contacts.fields.status')" name="status">
        <USelect v-model="form.status" :items="statusOptions" :disabled="isSaving" class="w-full" />
      </AppField>
      <AppField :label="t('contacts.fields.lifecycle_stage')" name="lifecycle_stage">
        <USelect v-model="lifecycleStageModel" :items="lifecycleOptions" :disabled="isSaving" class="w-full" />
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
    </div>
    <AppField :label="t('contacts.fields.description')" name="description">
      <UTextarea v-model="form.description" :rows="3" :disabled="isSaving" class="w-full" />
    </AppField>

    <div class="flex justify-end gap-3">
      <AppButton color="neutral" variant="outline" :disabled="isSaving" @click="emit('cancel')">
        {{ t('common.cancel') }}
      </AppButton>
      <AppButton type="submit" color="primary" :loading="isSaving">
        {{ isSaving ? t('contacts.submitting') : t('common.save') }}
      </AppButton>
    </div>
  </UForm>
</template>

<script setup lang="ts">
import { z } from 'zod'
import type { Contact, ContactStatus, ContactUpdatePayload, LifecycleStage } from '~/types/contacts'
import type { UserSummary } from '~/types/user'

const props = defineProps<{
  /** Contact to edit; omit for create mode. */
  contact?: Contact | null
}>()

const emit = defineEmits<{
  saved: []
  cancel: []
}>()

const { t } = useI18n()
const { create, update } = useContacts()
const { user: currentUser } = useAuth()
const { lookup } = useUsers()

const CONTACT_STATUSES: ContactStatus[] = ['lead', 'qualified', 'customer', 'churned']
const LIFECYCLE_STAGES: LifecycleStage[] = [
  'subscriber', 'lead', 'mql', 'sql', 'opportunity', 'customer', 'evangelist',
]

const isSaving = ref(false)
const formError = ref('')
// Resolved label for the currently selected owner, so AppUserSelect can render
// a name immediately instead of a blank box while it searches.
const ownerInitial = ref<UserSummary | null>(null)

const emptyForm = {
  owner_id: null as string | null,
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  mobile_phone: '',
  job_title: '',
  department: '',
  status: 'lead' as ContactStatus,
  lifecycle_stage: '' as LifecycleStage | '',
  lead_source: '',
  city: '',
  state: '',
  country: '',
  description: '',
}

const form = reactive({ ...emptyForm })
let original = { ...emptyForm }

watch(() => props.contact, async (contact) => {
  if (!contact) {
    // Create mode: default the owner to the logged-in user (still changeable).
    Object.assign(form, emptyForm, { owner_id: currentUser.value?.id ?? null })
    original = { ...form }
    ownerInitial.value = currentUser.value
      ? { id: currentUser.value.id, full_name: currentUser.value.full_name, email: currentUser.value.email }
      : null
    return
  }
  Object.assign(form, {
    owner_id: contact.owner_id ?? null,
    first_name: contact.first_name,
    last_name: contact.last_name ?? '',
    email: contact.email ?? '',
    phone: contact.phone ?? '',
    mobile_phone: contact.mobile_phone ?? '',
    job_title: contact.job_title ?? '',
    department: contact.department ?? '',
    status: contact.status,
    lifecycle_stage: contact.lifecycle_stage ?? '',
    lead_source: contact.lead_source ?? '',
    city: contact.city ?? '',
    state: contact.state ?? '',
    country: contact.country ?? '',
    description: contact.description ?? '',
  })
  original = { ...form }

  ownerInitial.value = null
  if (contact.owner_id) {
    const [owner] = await lookup([contact.owner_id])
    ownerInitial.value = owner ?? null
  }
}, { immediate: true })

// Mirrors backend #14 so the user never hits an avoidable 422.
const maxMsg = (max: number) => t('contacts.validation.max_length', { max })
const schema = computed(() => z.object({
  first_name: z.string()
    .trim()
    .min(1, t('contacts.validation.first_name_required'))
    .max(100, maxMsg(100)),
  last_name: z.string().max(100, maxMsg(100)),
  email: z.literal('').or(
    z.string().trim().email(t('contacts.validation.email_invalid')).max(255, maxMsg(255)),
  ),
  phone: z.string().max(50, maxMsg(50)),
  mobile_phone: z.string().max(50, maxMsg(50)),
  job_title: z.string().max(255, maxMsg(255)),
  department: z.string().max(100, maxMsg(100)),
  status: z.enum(CONTACT_STATUSES as [ContactStatus, ...ContactStatus[]]),
  lifecycle_stage: z.literal('').or(
    z.enum(LIFECYCLE_STAGES as [LifecycleStage, ...LifecycleStage[]]),
  ),
  lead_source: z.string().max(50, maxMsg(50)),
  // country/state/city come from AppLocationSelect (issue #26), not free
  // text — always '' or a valid code/id picked from the backend's list, so
  // no length/format check is needed here (the backend still validates
  // existence + cascade consistency on submit).
  city: z.string(),
  state: z.string(),
  country: z.string(),
  description: z.string(),
}))

const statusOptions = computed(() =>
  CONTACT_STATUSES.map(value => ({ value, label: t(`contacts.status.${value}`) })),
)

// Reka UI's <SelectItem/> rejects an empty-string value (it's reserved to mean
// "cleared"), so the "no lifecycle stage" option needs a non-empty sentinel.
// form.lifecycle_stage itself stays '' internally (matches the API/Zod schema);
// this computed just translates at the UI boundary.
const NONE_SENTINEL = '__none__'
const lifecycleOptions = computed(() => [
  { value: NONE_SENTINEL, label: t('contacts.lifecycle.none') },
  ...LIFECYCLE_STAGES.map(value => ({ value, label: t(`contacts.lifecycle.${value}`) })),
])
const lifecycleStageModel = computed({
  get: () => form.lifecycle_stage || NONE_SENTINEL,
  set: (v: string) => {
    form.lifecycle_stage = (v === NONE_SENTINEL ? '' : v) as LifecycleStage | ''
  },
})

/**
 * Build the payload: trim strings, drop empty optional fields, and in edit
 * mode only include fields whose value changed (partial PATCH).
 */
function buildPayload(): ContactUpdatePayload {
  const payload: Record<string, unknown> = {}
  for (const [key, raw] of Object.entries(form)) {
    const value = typeof raw === 'string' ? raw.trim() : raw

    if (props.contact) {
      const originalValue = original[key as keyof typeof original]
      if (value === originalValue) continue
      if (value === '' && key !== 'first_name') {
        // Was populated, now cleared - send an explicit null so the backend
        // actually unsets it. Omitting it here would silently keep the
        // stale DB value: AppLocationSelect resets state/city to '' when
        // the user picks a new country, and if that clear never reaches
        // the backend, the old state/city gets re-validated against the
        // new country and 422s (see PR #39 review).
        payload[key] = null
        continue
      }
      payload[key] = value
      continue
    }

    // Create mode: omit blank optional fields so required-field validation
    // (e.g. companies' required `country`) surfaces its own clear error
    // rather than a generic "may not be null".
    if (value === '' && key !== 'first_name') continue
    payload[key] = value
  }
  return payload as ContactUpdatePayload
}

async function onSubmit() {
  formError.value = ''
  isSaving.value = true
  try {
    if (props.contact) {
      const payload = buildPayload()
      if (Object.keys(payload).length > 0) {
        await update(props.contact.id, payload)
      }
    }
    else {
      await create({ ...buildPayload(), first_name: form.first_name.trim() })
    }
    emit('saved')
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    formError.value = t(`error.${e.code ?? 'unknown'}`, t('error.unknown'))
  }
  finally {
    isSaving.value = false
  }
}
</script>

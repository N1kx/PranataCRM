<template>
  <UForm :schema="schema" :state="form" class="space-y-4" @submit="onSubmit">
    <UAlert
      v-if="formError"
      color="red"
      variant="soft"
      :description="formError"
      icon="i-lucide-circle-alert"
    />

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <AppField :label="t('contacts.fields.first_name')" name="first_name">
        <AppInput v-model="form.first_name" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('contacts.fields.last_name')" name="last_name">
        <AppInput v-model="form.last_name" :disabled="isSaving" />
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
        <USelect v-model="form.status" :options="statusOptions" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('contacts.fields.lifecycle_stage')" name="lifecycle_stage">
        <USelect v-model="form.lifecycle_stage" :options="lifecycleOptions" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('contacts.fields.city')" name="city">
        <AppInput v-model="form.city" :disabled="isSaving" />
      </AppField>
      <AppField :label="t('contacts.fields.country')" name="country">
        <AppInput v-model="form.country" :disabled="isSaving" />
      </AppField>
    </div>
    <AppField :label="t('contacts.fields.description')" name="description">
      <UTextarea v-model="form.description" :rows="3" :disabled="isSaving" />
    </AppField>

    <div class="flex justify-end gap-3">
      <AppButton color="gray" variant="outline" :disabled="isSaving" @click="emit('cancel')">
        {{ t('common.cancel') }}
      </AppButton>
      <AppButton type="submit" color="violet" :loading="isSaving">
        {{ isSaving ? t('contacts.submitting') : t('common.save') }}
      </AppButton>
    </div>
  </UForm>
</template>

<script setup lang="ts">
import { z } from 'zod'
import type { Contact, ContactStatus, ContactUpdatePayload, LifecycleStage } from '~/types/contacts'

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

const CONTACT_STATUSES: ContactStatus[] = ['lead', 'qualified', 'customer', 'churned']
const LIFECYCLE_STAGES: LifecycleStage[] = [
  'subscriber', 'lead', 'mql', 'sql', 'opportunity', 'customer', 'evangelist',
]

const isSaving = ref(false)
const formError = ref('')

const emptyForm = {
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
  country: '',
  description: '',
}

const form = reactive({ ...emptyForm })
let original = { ...emptyForm }

watch(() => props.contact, (contact) => {
  if (!contact) {
    Object.assign(form, emptyForm)
    original = { ...emptyForm }
    return
  }
  Object.assign(form, {
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
    country: contact.country ?? '',
    description: contact.description ?? '',
  })
  original = { ...form }
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
  city: z.string().max(100, maxMsg(100)),
  country: z.string().max(100, maxMsg(100)),
  description: z.string(),
}))

const statusOptions = computed(() =>
  CONTACT_STATUSES.map(value => ({ value, label: t(`contacts.status.${value}`) })),
)
const lifecycleOptions = computed(() => [
  { value: '', label: t('contacts.lifecycle.none') },
  ...LIFECYCLE_STAGES.map(value => ({ value, label: t(`contacts.lifecycle.${value}`) })),
])

/**
 * Build the payload: trim strings, drop empty optional fields, and in edit
 * mode only include fields whose value changed (partial PATCH).
 */
function buildPayload(): ContactUpdatePayload {
  const payload: Record<string, string> = {}
  for (const [key, raw] of Object.entries(form)) {
    const value = typeof raw === 'string' ? raw.trim() : raw
    if (props.contact && value === original[key as keyof typeof original]) {
      continue
    }
    if (value === '' && key !== 'first_name') {
      continue
    }
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

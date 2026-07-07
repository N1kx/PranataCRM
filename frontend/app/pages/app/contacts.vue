<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('contacts.title') }}
      </h1>
      <AppButton color="violet" icon="i-lucide-user-plus" @click="openCreate">
        {{ t('contacts.add') }}
      </AppButton>
    </div>

    <!-- Error state -->
    <UAlert
      v-if="loadError"
      color="red"
      variant="soft"
      icon="i-lucide-circle-alert"
      :title="t('common.error_state')"
    >
      <template #description>
        <AppButton color="red" variant="outline" size="xs" class="mt-2" @click="loadContacts">
          {{ t('common.retry') }}
        </AppButton>
      </template>
    </UAlert>

    <!-- List -->
    <UCard v-else>
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
          {{ t('common.empty') }}
        </p>
      </div>

      <template v-else>
        <UTable :rows="items" :columns="columns" :loading="isLoading">
          <template #name-data="{ row }">
            <span class="font-medium text-gray-900 dark:text-white">
              {{ fullName(row) }}
            </span>
          </template>
          <template #email-data="{ row }">
            {{ row.email || '-' }}
          </template>
          <template #phone-data="{ row }">
            {{ row.phone || '-' }}
          </template>
          <template #job_title-data="{ row }">
            {{ row.job_title || '-' }}
          </template>
          <template #status-data="{ row }">
            <UBadge :color="statusColor(row.status)" variant="subtle">
              {{ t(`contacts.status.${row.status}`) }}
            </UBadge>
          </template>
          <template #actions-data="{ row }">
            <UDropdown :items="rowActions(row)">
              <UButton color="gray" variant="ghost" icon="i-lucide-ellipsis-vertical" />
            </UDropdown>
          </template>
        </UTable>

        <!-- Pagination -->
        <div v-if="total > pageSize" class="flex justify-end pt-4">
          <UPagination v-model="page" :page-count="pageSize" :total="total" />
        </div>
      </template>
    </UCard>

    <!-- Create / Edit modal -->
    <UModal v-model="modalOpen">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold">
              {{ editingId ? t('contacts.edit') : t('contacts.add') }}
            </h2>
            <UButton icon="i-lucide-x" color="gray" variant="ghost" @click="modalOpen = false" />
          </div>
        </template>

        <UAlert
          v-if="formError"
          color="red"
          variant="soft"
          :description="formError"
          class="mb-4"
          icon="i-lucide-circle-alert"
        />

        <UForm :schema="schema" :state="form" class="space-y-4" @submit="onSubmit">
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

          <AppButton type="submit" block color="violet" :loading="isSaving">
            {{ isSaving ? t('contacts.submitting') : t('common.save') }}
          </AppButton>
        </UForm>
      </UCard>
    </UModal>

    <!-- Delete confirmation modal -->
    <UModal v-model="deleteModalOpen">
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold">
            {{ t('contacts.confirm_delete_title') }}
          </h2>
        </template>

        <p class="text-sm text-gray-600 dark:text-gray-300">
          {{ t('contacts.confirm_delete_body', { name: deleteTarget ? fullName(deleteTarget) : '' }) }}
        </p>

        <template #footer>
          <div class="flex justify-end gap-3">
            <AppButton color="gray" variant="outline" :disabled="isDeleting" @click="deleteModalOpen = false">
              {{ t('common.cancel') }}
            </AppButton>
            <AppButton color="red" :loading="isDeleting" @click="onDelete">
              {{ t('contacts.delete') }}
            </AppButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { z } from 'zod'
import type { Contact, ContactStatus, ContactUpdatePayload, LifecycleStage } from '~/types/contacts'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t } = useI18n()
const { list, create, update, remove } = useContacts()
const toast = useToast()

const CONTACT_STATUSES: ContactStatus[] = ['lead', 'qualified', 'customer', 'churned']
const LIFECYCLE_STAGES: LifecycleStage[] = [
  'subscriber', 'lead', 'mql', 'sql', 'opportunity', 'customer', 'evangelist',
]

// ── List state ────────────────────────────────────────────────────────────────

const items = ref<Contact[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const isLoading = ref(false)
const loadError = ref(false)

const columns = computed(() => [
  { key: 'name', label: t('contacts.table.name') },
  { key: 'email', label: t('contacts.table.email') },
  { key: 'phone', label: t('contacts.table.phone') },
  { key: 'job_title', label: t('contacts.table.job_title') },
  { key: 'status', label: t('contacts.table.status') },
  { key: 'actions', label: '' },
])

function statusColor(status: ContactStatus) {
  return ({
    lead: 'gray',
    qualified: 'blue',
    customer: 'green',
    churned: 'red',
  } as const)[status] ?? 'gray'
}

function fullName(contact: Contact): string {
  return [contact.first_name, contact.last_name].filter(Boolean).join(' ')
}

async function loadContacts() {
  isLoading.value = true
  loadError.value = false
  try {
    const res = await list(page.value, pageSize)
    items.value = res.items
    total.value = res.total
  }
  catch {
    loadError.value = true
  }
  finally {
    isLoading.value = false
  }
}

onMounted(loadContacts)
watch(page, loadContacts)

function rowActions(row: Contact) {
  return [[
    {
      label: t('contacts.actions.edit'),
      icon: 'i-lucide-pencil',
      click: () => openEdit(row),
    },
    {
      label: t('contacts.actions.delete'),
      icon: 'i-lucide-trash-2',
      click: () => confirmDelete(row),
    },
  ]]
}

// ── Create / Edit form ────────────────────────────────────────────────────────

const modalOpen = ref(false)
const editingId = ref<string | null>(null)
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

function resetForm() {
  Object.assign(form, emptyForm)
  original = { ...emptyForm }
  formError.value = ''
}

function openCreate() {
  editingId.value = null
  resetForm()
  modalOpen.value = true
}

function openEdit(row: Contact) {
  editingId.value = row.id
  resetForm()
  Object.assign(form, {
    first_name: row.first_name,
    last_name: row.last_name ?? '',
    email: row.email ?? '',
    phone: row.phone ?? '',
    mobile_phone: row.mobile_phone ?? '',
    job_title: row.job_title ?? '',
    department: row.department ?? '',
    status: row.status,
    lifecycle_stage: row.lifecycle_stage ?? '',
    lead_source: row.lead_source ?? '',
    city: row.city ?? '',
    country: row.country ?? '',
    description: row.description ?? '',
  })
  original = { ...form }
  modalOpen.value = true
}

/**
 * Build the payload: trim strings, drop empty optional fields, and in edit
 * mode only include fields whose value changed (partial PATCH).
 */
function buildPayload(): ContactUpdatePayload {
  const payload: Record<string, string> = {}
  for (const [key, raw] of Object.entries(form)) {
    const value = typeof raw === 'string' ? raw.trim() : raw
    if (editingId.value && value === original[key as keyof typeof original]) {
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
    if (editingId.value) {
      const payload = buildPayload()
      if (Object.keys(payload).length > 0) {
        await update(editingId.value, payload)
      }
      toast.add({ title: t('contacts.saved'), color: 'green', icon: 'i-lucide-check-circle' })
    }
    else {
      await create({ ...buildPayload(), first_name: form.first_name.trim() })
      toast.add({ title: t('contacts.created'), color: 'green', icon: 'i-lucide-check-circle' })
    }
    modalOpen.value = false
    resetForm()
    await loadContacts()
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    formError.value = t(`error.${e.code ?? 'unknown'}`, t('error.unknown'))
  }
  finally {
    isSaving.value = false
  }
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
    toast.add({ title: t('contacts.deleted'), color: 'green', icon: 'i-lucide-check-circle' })
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
      color: 'red',
      icon: 'i-lucide-circle-alert',
    })
  }
  finally {
    isDeleting.value = false
  }
}
</script>

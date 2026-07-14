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
        <UTable :data="items" :columns="columns" :loading="isLoading">
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
import type { Contact } from '~/types/contacts'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t } = useI18n()
const { list, remove } = useContacts()
const { lookup } = useUsers()
const toast = useToast()

// ── List state ────────────────────────────────────────────────────────────────

const items = ref<Contact[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
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
    return
  }
  finally {
    isLoading.value = false
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
watch(page, loadContacts)

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

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('contacts.title') }}
      </h1>
      <AppButton color="violet" icon="i-lucide-user-plus" @click="navigateTo('/app/contacts/new')">
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
            <NuxtLink
              :to="`/app/contacts/${row.id}`"
              class="font-medium text-gray-900 dark:text-white hover:text-violet-600 dark:hover:text-violet-400"
            >
              {{ contactFullName(row) }}
            </NuxtLink>
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
            <UBadge :color="contactStatusColor(row.status)" variant="subtle">
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

    <!-- Delete confirmation modal -->
    <UModal v-model="deleteModalOpen">
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold">
            {{ t('contacts.confirm_delete_title') }}
          </h2>
        </template>

        <p class="text-sm text-gray-600 dark:text-gray-300">
          {{ t('contacts.confirm_delete_body', { name: deleteTarget ? contactFullName(deleteTarget) : '' }) }}
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
import type { Contact } from '~/types/contacts'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t } = useI18n()
const { list, remove } = useContacts()
const toast = useToast()

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
      label: t('contacts.actions.view'),
      icon: 'i-lucide-eye',
      click: () => navigateTo(`/app/contacts/${row.id}`),
    },
    {
      label: t('contacts.actions.edit'),
      icon: 'i-lucide-pencil',
      click: () => navigateTo(`/app/contacts/${row.id}/edit`),
    },
    {
      label: t('contacts.actions.delete'),
      icon: 'i-lucide-trash-2',
      click: () => confirmDelete(row),
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

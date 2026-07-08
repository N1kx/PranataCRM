<template>
  <div class="space-y-6 max-w-3xl">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <UButton
          icon="i-lucide-arrow-left"
          color="gray"
          variant="ghost"
          to="/app/contacts"
          :aria-label="t('contacts.back_to_list')"
        />
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ contact ? contactFullName(contact) : t('contacts.view') }}
        </h1>
        <UBadge v-if="contact" :color="contactStatusColor(contact.status)" variant="subtle">
          {{ t(`contacts.status.${contact.status}`) }}
        </UBadge>
      </div>
      <!-- Later gated by write permission once RBAC lands -->
      <AppButton
        v-if="contact"
        color="violet"
        icon="i-lucide-pencil"
        @click="navigateTo(`/app/contacts/${contact.id}/edit`)"
      >
        {{ t('contacts.actions.edit') }}
      </AppButton>
    </div>

    <!-- Error state -->
    <UAlert
      v-if="loadErrorCode"
      color="red"
      variant="soft"
      icon="i-lucide-circle-alert"
      :title="t(`error.${loadErrorCode}`, t('common.error_state'))"
    >
      <template #description>
        <AppButton color="red" variant="outline" size="xs" class="mt-2" @click="loadContact">
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
    <UCard v-else-if="contact">
      <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
        <div v-for="field in detailFields" :key="field.label">
          <dt class="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            {{ field.label }}
          </dt>
          <dd class="mt-1 text-sm text-gray-900 dark:text-white">
            {{ field.value || '-' }}
          </dd>
        </div>
      </dl>

      <div v-if="contact.description" class="mt-6 pt-4 border-t border-gray-200 dark:border-gray-800">
        <dt class="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          {{ t('contacts.fields.description') }}
        </dt>
        <dd class="mt-1 text-sm text-gray-900 dark:text-white whitespace-pre-line">
          {{ contact.description }}
        </dd>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import type { Contact } from '~/types/contacts'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t, locale } = useI18n()
const { get } = useContacts()
const route = useRoute()

const contactId = route.params.id as string
const contact = ref<Contact | null>(null)
const isLoading = ref(false)
const loadErrorCode = ref('')

async function loadContact() {
  isLoading.value = true
  loadErrorCode.value = ''
  try {
    contact.value = await get(contactId)
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    loadErrorCode.value = e.code ?? 'unknown'
  }
  finally {
    isLoading.value = false
  }
}

onMounted(loadContact)

const detailFields = computed(() => {
  const c = contact.value
  if (!c) return []
  return [
    { label: t('contacts.fields.email'), value: c.email },
    { label: t('contacts.fields.phone'), value: c.phone },
    { label: t('contacts.fields.mobile_phone'), value: c.mobile_phone },
    { label: t('contacts.fields.job_title'), value: c.job_title },
    { label: t('contacts.fields.department'), value: c.department },
    {
      label: t('contacts.fields.lifecycle_stage'),
      value: c.lifecycle_stage ? t(`contacts.lifecycle.${c.lifecycle_stage}`) : '',
    },
    { label: t('contacts.fields.lead_source'), value: c.lead_source },
    { label: t('contacts.fields.city'), value: c.city },
    { label: t('contacts.fields.country'), value: c.country },
    {
      label: t('contacts.fields.created_at'),
      value: new Date(c.created_at).toLocaleString(locale.value),
    },
  ]
})
</script>

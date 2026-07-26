<template>
  <div class="space-y-6 max-w-3xl">
    <!-- Header -->
    <div class="flex items-center gap-3">
      <UButton
        icon="i-lucide-arrow-left"
        color="neutral"
        variant="ghost"
        to="/app/deals"
        :aria-label="t('deals.back_to_list')"
      />
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('deals.add') }}
      </h1>
    </div>

    <UCard>
      <!-- Held back until any ?company_id=/?contact_id= prefill has resolved, so
           the form's create-mode initialisation sees it on first run. -->
      <div v-if="isResolvingPrefill" class="text-center py-12 text-gray-400">
        <UIcon name="i-lucide-loader-circle" class="w-8 h-8 mx-auto mb-3 animate-spin" />
        <p class="text-sm">
          {{ t('common.loading') }}
        </p>
      </div>
      <DealsForm
        v-else
        :prefill-company="prefillCompany"
        :prefill-contact="prefillContact"
        @saved="onSaved"
        @cancel="navigateTo('/app/deals')"
      />
    </UCard>
  </div>
</template>

<script setup lang="ts">
import type { CompanySummary } from '~/types/companies'
import type { ContactSummary } from '~/types/contacts'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t } = useI18n()
const { lookup: lookupCompanies } = useCompanies()
const { lookup: lookupContacts } = useContacts()
const toast = useToast()
const route = useRoute()

// ?company_id= / ?contact_id= are what the company-detail "Add deal" and
// contact-detail "Add deal" buttons pass in (issues #37 / #38).
const companyId = typeof route.query.company_id === 'string' ? route.query.company_id : ''
const contactId = typeof route.query.contact_id === 'string' ? route.query.contact_id : ''

const prefillCompany = ref<CompanySummary | null>(null)
const prefillContact = ref<ContactSummary | null>(null)
const isResolvingPrefill = ref(!!(companyId || contactId))

onMounted(async () => {
  if (!isResolvingPrefill.value) return
  // Resolve labels for the prefilled ids. A failure here must not block
  // creating a deal — the picker just starts empty.
  await Promise.all([
    (async () => {
      if (!companyId) return
      try {
        const [company] = await lookupCompanies([companyId])
        prefillCompany.value = company ?? null
      }
      catch { /* picker starts empty */ }
    })(),
    (async () => {
      if (!contactId) return
      try {
        const [contact] = await lookupContacts([contactId])
        prefillContact.value = contact ?? null
      }
      catch { /* picker starts empty */ }
    })(),
  ])
  isResolvingPrefill.value = false
})

async function onSaved() {
  toast.add({ title: t('deals.created'), color: 'success', icon: 'i-lucide-check-circle' })
  await navigateTo('/app/deals')
}
</script>

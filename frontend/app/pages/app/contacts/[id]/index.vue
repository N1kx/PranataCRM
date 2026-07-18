<template>
  <div class="space-y-6 max-w-3xl">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <UButton
          icon="i-lucide-arrow-left"
          color="neutral"
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
        color="primary"
        icon="i-lucide-pencil"
        @click="navigateTo(`/app/contacts/${contact.id}/edit`)"
      >
        {{ t('contacts.actions.edit') }}
      </AppButton>
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
        <AppButton color="error" variant="outline" size="xs" class="mt-2" @click="loadContact">
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
        <div>
          <dt class="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            {{ t('contacts.company') }}
          </dt>
          <dd class="mt-1 text-sm text-gray-900 dark:text-white">
            <NuxtLink
              v-if="contact.company_id"
              :to="`/app/companies/${contact.company_id}`"
              class="text-primary-600 dark:text-primary-400 hover:underline"
            >
              {{ companyName || '-' }}
            </NuxtLink>
            <template v-else>
              -
            </template>
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
import { SOURCE_VALUES } from '~/types/source'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t, locale } = useI18n()
const { get } = useContacts()
const { listCountries, listStates, listCities } = useGeo()
const { lookup: lookupCompanies } = useCompanies()
const route = useRoute()

const contactId = route.params.id as string
const contact = ref<Contact | null>(null)
const isLoading = ref(false)
const loadErrorCode = ref('')
// country/state/city are stored as an ISO code / geo ids (issue #26);
// resolve their display names separately since the contact response itself
// only carries the raw code/id.
const countryName = ref('')
const stateName = ref('')
const cityName = ref('')
const companyName = ref('')

async function resolveCompanyName(c: Contact) {
  if (!c.company_id) return
  try {
    const [company] = await lookupCompanies([c.company_id])
    companyName.value = company?.name ?? ''
  }
  catch {
    companyName.value = ''
  }
}

// Best-effort: resolves country/state/city ids to display labels. Wrapped
// in its own try/catch so a lookup failure (e.g. a legacy free-text
// country like "Indonesia" that isn't a valid ISO code, which 422s
// listStates) only leaves the location labels blank — it must never fail
// the whole page when the contact itself loaded fine.
async function resolveLocationLabels(c: Contact) {
  try {
    if (c.country) {
      const countries = await listCountries()
      countryName.value = countries.find(x => x.value === c.country)?.label ?? ''
    }
    if (c.state) {
      // The states-by-country / cities-by-state lists are each the full
      // active set for that scope (small, backend-cached) — it's also how
      // we resolve the selected state/city's label, no separate /lookup
      // endpoint needed.
      const states = await listStates(c.country ?? '')
      stateName.value = states.find(x => x.value === c.state)?.label ?? ''
    }
    if (c.city && c.state) {
      const cities = await listCities(c.state)
      cityName.value = cities.find(x => x.value === c.city)?.label ?? ''
    }
  }
  catch {
    // Swallow — labels simply stay blank, the contact detail itself is
    // still valid and must keep rendering.
  }
}

async function loadContact() {
  isLoading.value = true
  loadErrorCode.value = ''
  countryName.value = ''
  stateName.value = ''
  cityName.value = ''
  companyName.value = ''
  try {
    contact.value = await get(contactId)
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    loadErrorCode.value = e.code ?? 'unknown'
    return
  }
  finally {
    isLoading.value = false
  }
  if (contact.value) {
    await Promise.all([resolveLocationLabels(contact.value), resolveCompanyName(contact.value)])
  }
}

onMounted(loadContact)

// lead_source is a bounded picklist (issue #40) — show the translated label,
// and append the free-text detail when the 'other' option was picked. A
// stored value outside the picklist (pre-#40 free text, or written by
// something other than this form) has no translation key — show it as-is
// rather than leaking the raw i18n key path.
function leadSourceDisplay(c: Contact): string {
  if (!c.lead_source) return ''
  if (!(SOURCE_VALUES as readonly string[]).includes(c.lead_source)) return c.lead_source
  const label = t(`contacts.lead_source.${c.lead_source}`)
  return c.lead_source === 'other' && c.lead_source_other
    ? `${label} - ${c.lead_source_other}`
    : label
}

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
    { label: t('contacts.fields.lead_source'), value: leadSourceDisplay(c) },
    { label: t('contacts.fields.country'), value: countryName.value },
    { label: t('contacts.fields.state'), value: stateName.value },
    { label: t('contacts.fields.city'), value: cityName.value },
    {
      label: t('contacts.fields.created_at'),
      value: new Date(c.created_at).toLocaleString(locale.value),
    },
  ]
})
</script>

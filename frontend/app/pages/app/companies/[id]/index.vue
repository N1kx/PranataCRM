<template>
  <div class="space-y-6 max-w-3xl">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <UButton
          icon="i-lucide-arrow-left"
          color="neutral"
          variant="ghost"
          to="/app/companies"
          :aria-label="t('companies.back_to_list')"
        />
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ company ? companyDisplayName(company) : t('companies.view') }}
        </h1>
        <UBadge v-if="company" :color="companyStatusColor(company.status)" variant="subtle">
          {{ t(`companies.status.${company.status}`) }}
        </UBadge>
        <UBadge v-if="company" :color="companyTypeColor(company.company_type)" variant="subtle">
          {{ t(`companies.type.${company.company_type}`) }}
        </UBadge>
      </div>
      <!-- Later gated by write permission once RBAC lands -->
      <AppButton
        v-if="company"
        color="primary"
        icon="i-lucide-pencil"
        @click="navigateTo(`/app/companies/${company.id}/edit`)"
      >
        {{ t('companies.actions.edit') }}
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
        <AppButton color="error" variant="outline" size="xs" class="mt-2" @click="loadCompany">
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
    <UCard v-else-if="company">
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

      <div v-if="company.description" class="mt-6 pt-4 border-t border-gray-200 dark:border-gray-800">
        <dt class="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          {{ t('companies.fields.description') }}
        </dt>
        <dd class="mt-1 text-sm text-gray-900 dark:text-white whitespace-pre-line">
          {{ company.description }}
        </dd>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import type { Company } from '~/types/companies'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t, locale } = useI18n()
const { get } = useCompanies()
const { listCountries, listStates, listCities } = useGeo()
const { lookup } = useUsers()
const route = useRoute()

const companyId = route.params.id as string
const company = ref<Company | null>(null)
const isLoading = ref(false)
const loadErrorCode = ref('')
// country/state/city are stored as an ISO code / geo ids (issue #26);
// resolve their display names separately since the company response itself
// only carries the raw code/id.
const countryName = ref('')
const stateName = ref('')
const cityName = ref('')
const ownerName = ref('')

// Best-effort: resolves country/state/city ids to display labels. Wrapped
// in its own try/catch so a lookup failure only leaves the location labels
// blank — it must never fail the whole page when the company itself loaded
// fine (mirrors contacts/[id]/index.vue).
async function resolveLocationLabels(c: Company) {
  try {
    if (c.country) {
      const countries = await listCountries()
      countryName.value = countries.find(x => x.value === c.country)?.label ?? ''
    }
    if (c.state) {
      const states = await listStates(c.country ?? '')
      stateName.value = states.find(x => x.value === c.state)?.label ?? ''
    }
    if (c.city && c.state) {
      const cities = await listCities(c.state)
      cityName.value = cities.find(x => x.value === c.city)?.label ?? ''
    }
  }
  catch {
    // Swallow — labels simply stay blank, the company detail itself is
    // still valid and must keep rendering.
  }
}

async function resolveOwnerName(c: Company) {
  if (!c.owner_id) return
  try {
    const [owner] = await lookup([c.owner_id])
    ownerName.value = owner?.full_name ?? ''
  }
  catch {
    ownerName.value = ''
  }
}

async function loadCompany() {
  isLoading.value = true
  loadErrorCode.value = ''
  countryName.value = ''
  stateName.value = ''
  cityName.value = ''
  ownerName.value = ''
  try {
    company.value = await get(companyId)
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    loadErrorCode.value = e.code ?? 'unknown'
    return
  }
  finally {
    isLoading.value = false
  }
  if (company.value) {
    await Promise.all([resolveLocationLabels(company.value), resolveOwnerName(company.value)])
  }
}

onMounted(loadCompany)

const detailFields = computed(() => {
  const c = company.value
  if (!c) return []
  return [
    { label: t('companies.owner'), value: ownerName.value },
    { label: t('companies.fields.legal_name'), value: c.legal_name },
    { label: t('companies.fields.website'), value: c.website },
    { label: t('companies.fields.email'), value: c.email },
    { label: t('companies.fields.phone'), value: c.phone },
    { label: t('companies.fields.industry'), value: c.industry },
    { label: t('companies.fields.size'), value: c.size },
    { label: t('companies.fields.employee_count'), value: c.employee_count != null ? String(c.employee_count) : '' },
    { label: t('companies.fields.source'), value: c.source },
    { label: t('companies.fields.country'), value: countryName.value },
    { label: t('companies.fields.state'), value: stateName.value },
    { label: t('companies.fields.city'), value: cityName.value },
    { label: t('companies.fields.linkedin_url'), value: c.linkedin_url },
    {
      label: t('companies.fields.created_at'),
      value: new Date(c.created_at).toLocaleString(locale.value),
    },
  ]
})
</script>

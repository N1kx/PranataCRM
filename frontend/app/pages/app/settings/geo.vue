<!--
  Minimal admin page for geo reference data (issue #26): pick a country ->
  manage its states/provinces -> pick a state -> manage its cities. States
  and cities are admin-editable (unlike countries, which are ISO-fixed) —
  see backend/app/modules/geo/admin_router.py for the rationale and the
  TENANT_OWNER gate (interim proxy for a real platform-admin role, see the
  TODO there).
-->
<template>
  <div class="space-y-6 max-w-4xl">
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('geo_admin.title') }}
      </h1>
      <p class="text-sm text-gray-500 mt-1">
        {{ t('geo_admin.description') }}
      </p>
    </div>

    <UAlert
      v-if="!isTenantOwner"
      color="warning"
      variant="soft"
      icon="i-lucide-lock"
      :description="t('geo_admin.owner_only')"
    />

    <template v-else>
      <UCard>
        <AppField :label="t('geo_admin.country')" name="country">
          <USelectMenu
            :model-value="selectedCountry ?? undefined"
            :items="countries"
            :loading="loadingCountries"
            label-key="label"
            by="value"
            class="w-full sm:w-80"
            :placeholder="t('location_select.country_placeholder')"
            @update:model-value="selectedCountry = $event ?? null"
          />
        </AppField>
      </UCard>

      <!-- States/provinces for the selected country -->
      <UCard v-if="selectedCountry">
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="font-semibold">
              {{ t('geo_admin.states_title', { country: selectedCountry.label }) }}
            </h2>
          </div>
        </template>

        <UAlert
          v-if="stateError"
          color="error"
          variant="soft"
          :description="stateError"
          class="mb-4"
        />

        <form class="flex flex-wrap gap-2 mb-4" @submit.prevent="onAddState">
          <AppInput
            v-model="newStateName"
            :placeholder="t('geo_admin.new_state_placeholder')"
            :disabled="savingState"
            class="flex-1 min-w-48"
          />
          <AppButton type="submit" color="primary" :loading="savingState">
            {{ t('geo_admin.add') }}
          </AppButton>
        </form>

        <div v-if="loadingStates" class="text-sm text-gray-400 py-4 text-center">
          {{ t('common.loading') }}
        </div>
        <ul v-else class="divide-y divide-gray-200 dark:divide-gray-800">
          <li
            v-for="s in states"
            :key="s.value"
            class="flex items-center justify-between py-2 gap-2"
          >
            <button
              class="text-left flex-1 hover:underline"
              :class="selectedState?.value === s.value && 'font-semibold'"
              @click="selectedState = s"
            >
              {{ s.label }}
            </button>
            <AppButton
              size="xs"
              color="error"
              variant="ghost"
              icon="i-lucide-trash-2"
              :aria-label="t('geo_admin.delete')"
              @click="onDeleteState(s)"
            />
          </li>
          <li v-if="!states.length" class="py-4 text-sm text-gray-400 text-center">
            {{ t('common.empty') }}
          </li>
        </ul>
      </UCard>

      <!-- Cities for the selected state -->
      <UCard v-if="selectedState">
        <template #header>
          <h2 class="font-semibold">
            {{ t('geo_admin.cities_title', { state: selectedState.label }) }}
          </h2>
        </template>

        <UAlert
          v-if="cityError"
          color="error"
          variant="soft"
          :description="cityError"
          class="mb-4"
        />

        <form class="flex flex-wrap gap-2 mb-4" @submit.prevent="onAddCity">
          <AppInput
            v-model="newCityName"
            :placeholder="t('geo_admin.new_city_placeholder')"
            :disabled="savingCity"
            class="flex-1 min-w-48"
          />
          <AppButton type="submit" color="primary" :loading="savingCity">
            {{ t('geo_admin.add') }}
          </AppButton>
        </form>

        <div v-if="loadingCities" class="text-sm text-gray-400 py-4 text-center">
          {{ t('common.loading') }}
        </div>
        <ul v-else class="divide-y divide-gray-200 dark:divide-gray-800">
          <li v-for="c in cities" :key="c.value" class="flex items-center justify-between py-2 gap-2">
            <span>{{ c.label }}</span>
            <AppButton
              size="xs"
              color="error"
              variant="ghost"
              icon="i-lucide-trash-2"
              :aria-label="t('geo_admin.delete')"
              @click="onDeleteCity(c)"
            />
          </li>
          <li v-if="!cities.length" class="py-4 text-sm text-gray-400 text-center">
            {{ t('common.empty') }}
          </li>
        </ul>
      </UCard>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { GeoOption } from '~/types/geo'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t } = useI18n()
const { user } = useAuth()
const {
  listCountries, listStates, listCities,
  adminCreateState, adminDeleteState,
  adminCreateCity, adminDeleteCity,
} = useGeo()

// Mirrors the backend's interim gate (admin_router.py's _require_admin):
// TENANT_OWNER only, pending a real platform-admin role (see that file's
// TODO — geo data is global, not per-tenant, so this is a stopgap).
const isTenantOwner = computed(() => user.value?.suite_role === 'tenant_owner')

const countries = ref<GeoOption[]>([])
const loadingCountries = ref(false)
const selectedCountry = ref<GeoOption | null>(null)

const states = ref<GeoOption[]>([])
const loadingStates = ref(false)
const selectedState = ref<GeoOption | null>(null)
const newStateName = ref('')
const savingState = ref(false)
const stateError = ref('')

const cities = ref<GeoOption[]>([])
const loadingCities = ref(false)
const newCityName = ref('')
const savingCity = ref(false)
const cityError = ref('')

async function loadCountries() {
  loadingCountries.value = true
  try {
    countries.value = await listCountries()
  }
  finally {
    loadingCountries.value = false
  }
}

async function loadStates() {
  if (!selectedCountry.value) {
    states.value = []
    return
  }
  loadingStates.value = true
  try {
    states.value = await listStates(selectedCountry.value.value)
  }
  finally {
    loadingStates.value = false
  }
}

async function loadCities() {
  if (!selectedState.value) {
    cities.value = []
    return
  }
  loadingCities.value = true
  try {
    cities.value = await listCities(selectedState.value.value)
  }
  finally {
    loadingCities.value = false
  }
}

watch(selectedCountry, () => {
  selectedState.value = null
  cities.value = []
  loadStates()
})
watch(selectedState, loadCities)

async function onAddState() {
  const name = newStateName.value.trim()
  if (!name || !selectedCountry.value) return
  stateError.value = ''
  savingState.value = true
  try {
    await adminCreateState({ country_code: selectedCountry.value.value, name })
    newStateName.value = ''
    await loadStates()
  }
  catch (err: unknown) {
    const e = err as { code?: string, message?: string }
    stateError.value = t(`error.${e.code ?? 'unknown'}`, e.message ?? t('error.unknown'))
  }
  finally {
    savingState.value = false
  }
}

async function onDeleteState(s: GeoOption) {
  stateError.value = ''
  try {
    await adminDeleteState(s.value)
    if (selectedState.value?.value === s.value) selectedState.value = null
    await loadStates()
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    stateError.value = t(`error.${e.code ?? 'unknown'}`, t('error.unknown'))
  }
}

async function onAddCity() {
  const name = newCityName.value.trim()
  if (!name || !selectedState.value) return
  cityError.value = ''
  savingCity.value = true
  try {
    await adminCreateCity({ state_id: selectedState.value.value, name })
    newCityName.value = ''
    await loadCities()
  }
  catch (err: unknown) {
    const e = err as { code?: string, message?: string }
    cityError.value = t(`error.${e.code ?? 'unknown'}`, e.message ?? t('error.unknown'))
  }
  finally {
    savingCity.value = false
  }
}

async function onDeleteCity(c: GeoOption) {
  cityError.value = ''
  try {
    await adminDeleteCity(c.value)
    await loadCities()
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    cityError.value = t(`error.${e.code ?? 'unknown'}`, t('error.unknown'))
  }
}

onMounted(loadCountries)
</script>

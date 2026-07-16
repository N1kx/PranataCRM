<!--
  Cascading country -> state/province -> city autocomplete (issue #26).
  v-model:country / v-model:state / v-model:city — country is an ISO
  alpha-2 code, state/city are geo_states.id / geo_cities.id (UUID strings),
  matching what the backend stores on contacts/companies.

  Renders as THREE separate labeled fields rather than one combined block, so
  callers can drop it directly into their own field grid alongside other
  AppField items and the three location fields still read as distinct fields
  (own label, own error slot). The wrapping <div class="contents"> is a
  single DOM root (this project's lint forbids multi-root templates) but
  `display: contents` removes it from layout entirely, so its three AppField
  children become direct grid items of whatever grid the caller places this
  component in — visually identical to three separate fields.

  State is disabled until a country is chosen; city is disabled until a
  state is chosen. Picking a new country clears state+city; picking a new
  state clears city. Each level's full scoped list is fetched once (backend
  serves it from a per-scope Redis cache) and filtered client-side by
  USelectMenu's own search — no debounced backend calls per keystroke.
-->
<template>
  <div class="contents">
    <AppField :label="t('location_select.country_label')" name="country">
      <USelectMenu
        :model-value="selectedCountry"
        :items="countries"
        :loading="loadingCountries"
        :disabled="disabled"
        label-key="label"
        by="value"
        clear
        :placeholder="t('location_select.country_placeholder')"
        :search-input="{ placeholder: t('location_select.search_placeholder') }"
        class="w-full"
        @update:model-value="onCountrySelect"
      >
        <template #empty>
          <span class="text-sm text-gray-400">{{ t('location_select.no_results') }}</span>
        </template>
      </USelectMenu>
    </AppField>

    <AppField :label="t('location_select.state_label')" name="state">
      <USelectMenu
        :model-value="selectedState"
        :items="states"
        :loading="loadingStates"
        :disabled="disabled || !country"
        label-key="label"
        by="value"
        clear
        :placeholder="t('location_select.state_placeholder')"
        :search-input="{ placeholder: t('location_select.search_placeholder') }"
        class="w-full"
        @update:model-value="onStateSelect"
      >
        <template #empty>
          <span class="text-sm text-gray-400">{{ t('location_select.no_results') }}</span>
        </template>
      </USelectMenu>
    </AppField>

    <AppField :label="t('location_select.city_label')" name="city">
      <USelectMenu
        :model-value="selectedCity"
        :items="cities"
        :loading="loadingCities"
        :disabled="disabled || !state"
        label-key="label"
        by="value"
        clear
        :placeholder="t('location_select.city_placeholder')"
        :search-input="{ placeholder: t('location_select.search_placeholder') }"
        class="w-full"
        @update:model-value="onCitySelect"
      >
        <template #empty>
          <span class="text-sm text-gray-400">{{ t('location_select.no_results') }}</span>
        </template>
      </USelectMenu>
    </AppField>
  </div>
</template>

<script setup lang="ts">
import type { GeoOption } from '~/types/geo'

const props = defineProps<{
  country?: string | null
  state?: string | null
  city?: string | null
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:country': [value: string | null]
  'update:state': [value: string | null]
  'update:city': [value: string | null]
}>()

const { t } = useI18n()
const { listCountries, listStates, listCities } = useGeo()

const countries = ref<GeoOption[]>([])
const states = ref<GeoOption[]>([])
const cities = ref<GeoOption[]>([])

const loadingCountries = ref(false)
const loadingStates = ref(false)
const loadingCities = ref(false)

const selectedCountry = computed(
  () => countries.value.find(c => c.value === props.country) ?? null,
)
const selectedState = computed(
  () => states.value.find(s => s.value === props.state) ?? null,
)
const selectedCity = computed(
  () => cities.value.find(c => c.value === props.city) ?? null,
)

function onCountrySelect(value: unknown) {
  const opt = value as GeoOption | null
  emit('update:country', opt?.value ?? null)
  // Changing the country invalidates whatever state/city were selected.
  emit('update:state', null)
  emit('update:city', null)
}

function onStateSelect(value: unknown) {
  const opt = value as GeoOption | null
  emit('update:state', opt?.value ?? null)
  emit('update:city', null)
}

function onCitySelect(value: unknown) {
  const opt = value as GeoOption | null
  emit('update:city', opt?.value ?? null)
}

// Monotonic sequence tokens so a slow, older request can't overwrite a
// newer one's results if it resolves out of order (mirrors AppUserSelect's
// searchSeq) — otherwise rapid country/state changes + a slow network could
// leave `states`/`cities` populated with another scope's options.
let statesSeq = 0
let citiesSeq = 0

// Refreshes the *available options* for the child level whenever the parent
// value changes — covers both a user's cascading pick (handled above) and
// an externally-set initial value (edit mode loading an existing record),
// so the selected item's label is always resolvable from the loaded list.
watch(
  () => props.country,
  async (code) => {
    const seq = ++statesSeq
    states.value = []
    cities.value = []
    if (!code) return
    loadingStates.value = true
    try {
      const result = await listStates(code)
      if (seq !== statesSeq) return
      states.value = result
    }
    catch {
      if (seq !== statesSeq) return
      states.value = []
    }
    finally {
      if (seq === statesSeq) loadingStates.value = false
    }
  },
  { immediate: true },
)

watch(
  () => props.state,
  async (stateId) => {
    const seq = ++citiesSeq
    cities.value = []
    if (!stateId) return
    loadingCities.value = true
    try {
      const result = await listCities(stateId)
      if (seq !== citiesSeq) return
      cities.value = result
    }
    catch {
      if (seq !== citiesSeq) return
      cities.value = []
    }
    finally {
      if (seq === citiesSeq) loadingCities.value = false
    }
  },
  { immediate: true },
)

onMounted(async () => {
  loadingCountries.value = true
  try {
    countries.value = await listCountries()
  }
  catch {
    countries.value = []
  }
  finally {
    loadingCountries.value = false
  }
})
</script>

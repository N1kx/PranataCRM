<template>
  <div class="space-y-6 max-w-3xl">
    <!-- Header -->
    <div class="flex items-center gap-3">
      <UButton
        icon="i-lucide-arrow-left"
        color="neutral"
        variant="ghost"
        to="/app/companies"
        :aria-label="t('companies.back_to_list')"
      />
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('companies.edit') }}
      </h1>
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

    <UCard v-else-if="company">
      <CompaniesForm :company="company" @saved="onSaved" @cancel="navigateTo('/app/companies')" />
    </UCard>
  </div>
</template>

<script setup lang="ts">
import type { Company } from '~/types/companies'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t } = useI18n()
const { get } = useCompanies()
const toast = useToast()
const route = useRoute()

const companyId = route.params.id as string
const company = ref<Company | null>(null)
const isLoading = ref(false)
const loadErrorCode = ref('')

async function loadCompany() {
  isLoading.value = true
  loadErrorCode.value = ''
  try {
    company.value = await get(companyId)
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    loadErrorCode.value = e.code ?? 'unknown'
  }
  finally {
    isLoading.value = false
  }
}

onMounted(loadCompany)

async function onSaved() {
  toast.add({ title: t('companies.saved'), color: 'success', icon: 'i-lucide-check-circle' })
  await navigateTo('/app/companies')
}
</script>

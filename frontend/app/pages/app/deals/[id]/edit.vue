<template>
  <div class="space-y-6 max-w-3xl">
    <!-- Header -->
    <div class="flex items-center gap-3">
      <UButton
        icon="i-lucide-arrow-left"
        color="neutral"
        variant="ghost"
        :to="`/app/deals/${dealId}`"
        :aria-label="t('deals.back_to_list')"
      />
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('deals.edit') }}
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
        <AppButton color="error" variant="outline" size="xs" class="mt-2" @click="loadDeal">
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

    <UCard v-else-if="deal">
      <!-- No stage field here by design: PATCH /deals/{id} rejects `stage`.
           Stage changes go through the pipeline drag or the detail page's
           "change stage" action. -->
      <DealsForm :deal="deal" @saved="onSaved" @cancel="navigateTo(`/app/deals/${dealId}`)" />
    </UCard>
  </div>
</template>

<script setup lang="ts">
import type { Deal } from '~/types/deals'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t } = useI18n()
const { get } = useDeals()
const toast = useToast()
const route = useRoute()

const dealId = route.params.id as string
const deal = ref<Deal | null>(null)
const isLoading = ref(false)
const loadErrorCode = ref('')

async function loadDeal() {
  isLoading.value = true
  loadErrorCode.value = ''
  try {
    deal.value = await get(dealId)
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    loadErrorCode.value = e.code ?? 'unknown'
  }
  finally {
    isLoading.value = false
  }
}

onMounted(loadDeal)

async function onSaved() {
  toast.add({ title: t('deals.saved'), color: 'success', icon: 'i-lucide-check-circle' })
  await navigateTo(`/app/deals/${dealId}`)
}
</script>

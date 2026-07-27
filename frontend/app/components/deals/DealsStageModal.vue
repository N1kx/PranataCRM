<template>
  <UModal v-model:open="isOpen" :title="title" :dismissible="!loading">
    <template #body>
      <div class="space-y-4">
        <p class="text-sm text-gray-600 dark:text-gray-300">
          {{ t('deals.pipeline.move_to', { stage: t(`deals.stage.${stage}`) }) }}
        </p>

        <!-- Required only for 'lost': the backend 422s without it. -->
        <AppField
          v-if="stage === 'lost'"
          :label="t('deals.fields.lost_reason')"
          name="lost_reason"
          :error="lostReasonError"
          required
        >
          <UTextarea
            v-model="lostReason"
            :rows="3"
            :disabled="loading"
            class="w-full"
            :placeholder="t('deals.pipeline.lost_reason_placeholder')"
          />
        </AppField>

        <AppField :label="t('deals.fields.close_reason')" name="close_reason" :error="closeReasonError">
          <AppInput v-model="closeReason" :disabled="loading" />
        </AppField>
      </div>
    </template>

    <template #footer>
      <div class="flex justify-end gap-3">
        <AppButton color="neutral" variant="outline" :disabled="loading" @click="onCancel">
          {{ t('common.cancel') }}
        </AppButton>
        <AppButton color="primary" :loading="loading" @click="onConfirm">
          {{ t('deals.pipeline.confirm_move') }}
        </AppButton>
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import type { DealStage, StageChangePayload } from '~/types/deals'

const props = defineProps<{
  open: boolean
  /** The stage being moved to — drives which reason fields are required. */
  stage: DealStage
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  /** Emitted only once local validation passes; parent performs the API call. */
  'confirm': [payload: StageChangePayload]
  'cancel': []
}>()

const { t } = useI18n()

const lostReason = ref('')
const closeReason = ref('')
const lostReasonError = ref('')
const closeReasonError = ref('')

const isOpen = computed({
  get: () => props.open,
  set: (v: boolean) => {
    emit('update:open', v)
    // Dismissing via the overlay/escape must roll the card back too, otherwise
    // an optimistically-moved card would stay in the new column unsaved.
    if (!v) emit('cancel')
  },
})

const title = computed(() =>
  props.stage === 'lost' ? t('deals.pipeline.lost_title') : t('deals.pipeline.won_title'),
)

// Reset per opening so a previous attempt's text never leaks into the next move.
watch(() => props.open, (open) => {
  if (open) {
    lostReason.value = ''
    closeReason.value = ''
    lostReasonError.value = ''
    closeReasonError.value = ''
  }
})

function onConfirm() {
  lostReasonError.value = ''
  closeReasonError.value = ''

  const lost = lostReason.value.trim()
  const close = closeReason.value.trim()

  if (props.stage === 'lost' && !lost) {
    lostReasonError.value = t('deals.validation.lost_reason_required')
    return
  }
  if (close.length > 100) {
    closeReasonError.value = t('deals.validation.max_length', { max: 100 })
    return
  }

  emit('confirm', {
    stage: props.stage,
    ...(close ? { close_reason: close } : {}),
    ...(lost ? { lost_reason: lost } : {}),
  })
}

function onCancel() {
  // Routed through the computed setter so the explicit Cancel button and an
  // overlay/escape dismissal follow exactly one path.
  isOpen.value = false
}
</script>

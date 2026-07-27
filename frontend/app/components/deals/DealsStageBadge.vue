<template>
  <UBadge :color="dealStageColor(stage)" variant="subtle" :size="size">
    {{ t(`deals.stage.${stage}`) }}
  </UBadge>
</template>

<script setup lang="ts">
import type { DealStage } from '~/types/deals'

defineProps<{
  stage: DealStage
  size?: 'sm' | 'md' | 'lg'
}>()

const { t } = useI18n()
</script>

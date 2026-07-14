<template>
  <div class="space-y-6">
    <!-- Greeting + period control -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ t('dashboard.greeting') }}, {{ user?.full_name?.split(' ')[0] }} 👋
        </h1>
        <p class="text-sm text-gray-500 mt-0.5">
          Berikut ringkasan aktivitas Anda.
        </p>
      </div>
      <UButtonGroup>
        <UButton
          v-for="p in periods"
          :key="p.value"
          size="sm"
          :color="period === p.value ? 'primary' : 'neutral'"
          :variant="period === p.value ? 'solid' : 'outline'"
          @click="period = p.value"
        >
          {{ p.label }}
        </UButton>
      </UButtonGroup>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      <UCard v-for="kpi in kpiCards" :key="kpi.key" class="relative overflow-hidden">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-sm text-gray-500">
              {{ kpi.label }}
            </p>
            <p class="text-3xl font-bold text-gray-900 dark:text-white mt-1 font-[Bricolage_Grotesque,sans-serif]">
              {{ kpi.value }}
            </p>
            <div class="flex items-center gap-1 mt-1">
              <UIcon
                :name="kpi.trend >= 0 ? 'i-lucide-trending-up' : 'i-lucide-trending-down'"
                :class="kpi.trend >= 0 ? 'text-green-500' : 'text-red-500'"
                class="w-4 h-4"
              />
              <span
                class="text-sm font-medium"
                :class="kpi.trend >= 0 ? 'text-green-600' : 'text-red-600'"
              >
                {{ Math.abs(kpi.trend) }}%
              </span>
            </div>
          </div>
          <div
            class="w-10 h-10 rounded-xl flex items-center justify-center"
            :class="kpi.color"
          >
            <UIcon :name="kpi.icon" class="w-5 h-5 text-white" />
          </div>
        </div>
      </UCard>
    </div>

    <!-- Pipeline + Activity -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <!-- Pipeline -->
      <UCard>
        <template #header>
          <h2 class="font-semibold text-gray-900 dark:text-white">
            {{ t('dashboard.pipeline') }}
          </h2>
        </template>
        <!-- TODO: wire dashboard API for real pipeline data -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div
            v-for="col in pipelineColumns"
            :key="col.name"
            class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3"
          >
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              {{ col.name }}
            </p>
            <div class="space-y-2">
              <div
                v-for="card in col.cards"
                :key="card.title"
                class="bg-white dark:bg-gray-900 rounded-md p-2.5 shadow-sm"
              >
                <p class="text-sm font-medium truncate text-gray-800 dark:text-gray-200">
                  {{ card.title }}
                </p>
                <div class="flex items-center justify-between mt-1.5">
                  <span class="text-xs text-gray-400">{{ card.value }}</span>
                  <UBadge
                    :label="card.score + '%'"
                    size="xs"
                    :color="card.score >= 70 ? 'success' : card.score >= 40 ? 'warning' : 'error'"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="mt-3 text-center">
          <p class="text-xs text-gray-400 italic">
            Data placeholder — koneksikan API dashboard untuk data nyata.
          </p>
        </div>
      </UCard>

      <!-- Recent Activity -->
      <UCard>
        <template #header>
          <h2 class="font-semibold text-gray-900 dark:text-white">
            {{ t('dashboard.activity') }}
          </h2>
        </template>
        <ul class="space-y-3">
          <li v-for="item in activityFeed" :key="item.id" class="flex items-start gap-3">
            <div class="w-7 h-7 rounded-full bg-violet-100 dark:bg-violet-900 flex items-center justify-center shrink-0 mt-0.5">
              <UIcon :name="item.icon" class="w-3.5 h-3.5 text-violet-600 dark:text-violet-400" />
            </div>
            <div class="min-w-0">
              <p class="text-sm text-gray-800 dark:text-gray-200">
                {{ item.text }}
              </p>
              <p class="text-xs text-gray-400 mt-0.5">
                {{ item.time }}
              </p>
            </div>
          </li>
        </ul>
        <div class="mt-3 text-center">
          <p class="text-xs text-gray-400 italic">
            Data placeholder — koneksikan API aktivitas untuk data nyata.
          </p>
        </div>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'app', middleware: 'auth' })

const { t } = useI18n()
const { user } = useAuth()

const period = ref('today')
const periods = [
  { value: 'today', label: t('dashboard.period.today') },
  { value: 'month', label: t('dashboard.period.month') },
  { value: 'quarter', label: t('dashboard.period.quarter') },
]

// TODO: wire dashboard API
const kpiCards = [
  { key: 'revenue', label: t('dashboard.kpi.revenue'), value: 'Rp 0', trend: 0, icon: 'i-lucide-circle-dollar-sign', color: 'bg-green-500' },
  { key: 'deals', label: t('dashboard.kpi.active_deals'), value: '0', trend: 0, icon: 'i-lucide-handshake', color: 'bg-blue-500' },
  { key: 'winrate', label: t('dashboard.kpi.win_rate'), value: '0%', trend: 0, icon: 'i-lucide-trophy', color: 'bg-violet-500' },
  { key: 'aging', label: t('dashboard.kpi.aging_leads'), value: '0', trend: 0, icon: 'i-lucide-clock-alert', color: 'bg-orange-500' },
]

const pipelineColumns = [
  { name: 'Prospek', cards: [{ title: 'PT Maju Jaya', value: 'Rp 25jt', score: 72 }, { title: 'CV Berkah', value: 'Rp 10jt', score: 45 }] },
  { name: 'Kualifikasi', cards: [{ title: 'PT Sentosa', value: 'Rp 80jt', score: 88 }] },
  { name: 'Proposal', cards: [{ title: 'PT Global', value: 'Rp 120jt', score: 35 }] },
  { name: 'Negosiasi', cards: [] },
]

const activityFeed = [
  { id: 1, icon: 'i-lucide-phone', text: 'Panggilan dengan PT Maju Jaya', time: 'Hari ini, 10:30' },
  { id: 2, icon: 'i-lucide-mail', text: 'Email follow-up dikirim ke CV Berkah', time: 'Hari ini, 09:15' },
  { id: 3, icon: 'i-lucide-file-text', text: 'Proposal dikirim ke PT Global', time: 'Kemarin, 16:00' },
  { id: 4, icon: 'i-lucide-user-plus', text: 'Lead baru: PT Sentosa ditambahkan', time: 'Kemarin, 14:20' },
]
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ t('team.title') }}
        </h1>
      </div>
      <AppButton color="primary" icon="i-lucide-user-plus" @click="modalOpen = true">
        {{ t('team.add_member') }}
      </AppButton>
    </div>

    <!-- Seat limit warning -->
    <UAlert
      v-if="seatLimitError"
      color="warning"
      icon="i-lucide-alert-triangle"
      :title="t('team.seat_full')"
      variant="soft"
    >
      <template #description>
        <NuxtLink to="/app/settings/billing" class="underline text-orange-700">
          Pergi ke Billing
        </NuxtLink>
      </template>
    </UAlert>

    <!-- Members list placeholder -->
    <UCard>
      <div class="text-center py-12 text-gray-400">
        <UIcon name="i-lucide-users" class="w-10 h-10 mx-auto mb-3" />
        <p class="text-sm">
          {{ t('common.empty') }}
        </p>
        <!-- TODO: fetch member list when GET /users endpoint is available -->
      </div>
    </UCard>

    <!-- Add member modal -->
    <UModal v-model:open="modalOpen">
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold">
            {{ t('team.add_member') }}
          </h2>
          <UButton icon="i-lucide-x" color="neutral" variant="ghost" @click="modalOpen = false" />
        </div>
        <!-- Tabs -->
        <UTabs v-model="activeTab" :items="tabs" class="mt-3" />
      </template>

      <template #body>
        <UAlert
          v-if="formError"
          color="error"
          variant="soft"
          :description="formError"
          class="mb-4"
          icon="i-lucide-circle-alert"
        />

        <!-- Create directly -->
        <UForm
          v-if="activeTab === 0"
          :schema="createSchema"
          :state="createForm"
          class="space-y-4"
          @submit="onCreateUser"
        >
          <AppField :label="t('team.full_name')" name="full_name">
            <AppInput v-model="createForm.full_name" :disabled="isLoading" />
          </AppField>
          <AppField :label="t('team.email')" name="email">
            <AppInput v-model="createForm.email" type="email" :disabled="isLoading" />
          </AppField>
          <AppField :label="t('team.password')" name="password">
            <AppInput v-model="createForm.password" type="password" :disabled="isLoading" />
          </AppField>
          <AppField :label="t('team.role')" name="role_id">
            <!-- TODO: fetch roles from GET /roles endpoint when available -->
            <AppInput v-model="createForm.role_id" placeholder="UUID role (TODO: dropdown)" :disabled="isLoading" />
          </AppField>
          <AppButton type="submit" block color="primary" :loading="isLoading">
            {{ isLoading ? t('team.submitting') : t('team.submit_create') }}
          </AppButton>
        </UForm>

        <!-- Invite by email -->
        <UForm
          v-if="activeTab === 1"
          :schema="inviteSchema"
          :state="inviteForm"
          class="space-y-4"
          @submit="onInviteUser"
        >
          <AppField :label="t('team.email')" name="email">
            <AppInput v-model="inviteForm.email" type="email" :disabled="isLoading" />
          </AppField>
          <AppField :label="t('team.full_name')" name="full_name">
            <AppInput
              v-model="inviteForm.full_name"
              :disabled="isLoading"
              placeholder="Opsional"
            />
          </AppField>
          <AppField :label="t('team.role')" name="role_id">
            <!-- TODO: fetch roles from GET /roles endpoint when available -->
            <AppInput v-model="inviteForm.role_id" placeholder="UUID role (TODO: dropdown)" :disabled="isLoading" />
          </AppField>
          <AppButton type="submit" block color="primary" :loading="isLoading">
            {{ isLoading ? t('team.submitting') : t('team.submit_invite') }}
          </AppButton>
        </UForm>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { z } from 'zod'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t } = useI18n()
const { createUser, inviteUser, isOwnerOrAdmin } = useAuth()
const toast = useToast()

// Guard — backend still enforces, this is UX only
if (!isOwnerOrAdmin.value) {
  await navigateTo('/app')
}

const modalOpen = ref(false)
const activeTab = ref(0)
const isLoading = ref(false)
const formError = ref('')
const seatLimitError = ref(false)

const tabs = [
  { label: t('team.create_tab') },
  { label: t('team.invite_tab') },
]

const createSchema = z.object({
  full_name: z.string().min(1, 'Wajib diisi'),
  email: z.string().email('Format email tidak valid'),
  password: z.string().min(8, 'Min 8 karakter').regex(/[a-zA-Z]/).regex(/[0-9]/),
  role_id: z.string().min(1, 'Wajib diisi'),
})

const inviteSchema = z.object({
  email: z.string().email('Format email tidak valid'),
  role_id: z.string().min(1, 'Wajib diisi'),
})

const createForm = reactive({ full_name: '', email: '', password: '', role_id: '' })
const inviteForm = reactive({ email: '', full_name: '', role_id: '' })

async function onCreateUser() {
  formError.value = ''
  seatLimitError.value = false
  isLoading.value = true
  try {
    await createUser({ ...createForm })
    toast.add({ title: t('team.member_added'), color: 'success', icon: 'i-lucide-check-circle' })
    modalOpen.value = false
    Object.assign(createForm, { full_name: '', email: '', password: '', role_id: '' })
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    if (e.code === 'AUTH_SEAT_LIMIT') {
      seatLimitError.value = true
      modalOpen.value = false
    }
    else {
      formError.value = t(`error.${e.code ?? 'unknown'}`, t('error.unknown'))
    }
  }
  finally {
    isLoading.value = false
  }
}

async function onInviteUser() {
  formError.value = ''
  seatLimitError.value = false
  isLoading.value = true
  try {
    await inviteUser({
      email: inviteForm.email,
      full_name: inviteForm.full_name || undefined,
      role_id: inviteForm.role_id,
    })
    toast.add({ title: t('team.invite_sent'), color: 'success', icon: 'i-lucide-send' })
    modalOpen.value = false
    Object.assign(inviteForm, { email: '', full_name: '', role_id: '' })
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    if (e.code === 'AUTH_SEAT_LIMIT') {
      seatLimitError.value = true
      modalOpen.value = false
    }
    else {
      formError.value = t(`error.${e.code ?? 'unknown'}`, t('error.unknown'))
    }
  }
  finally {
    isLoading.value = false
  }
}
</script>

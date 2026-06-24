<template>
  <div>
    <UCard class="shadow-lg">
      <template #header>
        <div class="text-center">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ t('auth.invite.title') }}
          </h1>
          <p class="text-sm text-gray-500 mt-1">
            {{ t('auth.invite.subtitle') }}
          </p>
        </div>
      </template>

      <!-- Error state: invalid token -->
      <div v-if="tokenError" class="text-center py-6">
        <UIcon name="i-lucide-circle-x" class="w-12 h-12 text-red-400 mx-auto mb-3" />
        <p class="text-gray-700 dark:text-gray-300 font-medium">
          {{ t('error.AUTH_INVITE_INVALID') }}
        </p>
        <NuxtLink to="/login" class="text-violet-600 hover:underline text-sm mt-3 block">
          Kembali ke halaman masuk
        </NuxtLink>
      </div>

      <template v-else>
        <UAlert
          v-if="errorMsg"
          color="red"
          variant="soft"
          :description="errorMsg"
          class="mb-4"
          icon="i-lucide-circle-alert"
        />

        <UForm :schema="schema" :state="form" class="space-y-4" @submit="onSubmit">
          <!-- Email locked from token -->
          <AppField :label="t('auth.invite.email_locked')" name="email">
            <AppInput
              :model-value="emailFromToken"
              type="email"
              disabled
            />
          </AppField>

          <AppField :label="t('auth.invite.full_name')" name="full_name">
            <AppInput
              v-model="form.full_name"
              placeholder="Nama lengkap Anda"
              :disabled="isLoading"
            />
          </AppField>

          <AppField :label="t('auth.invite.password')" name="password">
            <AppInput
              v-model="form.password"
              type="password"
              placeholder="Min 8 karakter, 1 huruf + 1 angka"
              :disabled="isLoading"
            />
          </AppField>

          <AppButton type="submit" block color="violet" :loading="isLoading">
            {{ isLoading ? t('auth.invite.submitting') : t('auth.invite.submit') }}
          </AppButton>
        </UForm>
      </template>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { z } from 'zod'

definePageMeta({ layout: 'auth' })

const { t } = useI18n()
const route = useRoute()
const { acceptInvite } = useAuth()

const token = computed(() => route.query.token as string ?? '')
const slugFromQuery = computed(() => route.query.slug as string ?? '')

// Decode email from JWT payload (public claim — not sensitive, no verification here)
const emailFromToken = computed(() => {
  if (!token.value) return ''
  try {
    const payload = JSON.parse(atob(token.value.split('.')[1] ?? ''))
    return payload.email ?? ''
  }
  catch {
    return ''
  }
})

const tokenError = computed(() => !token.value)

const schema = z.object({
  full_name: z.string().min(1, 'Nama wajib diisi'),
  password: z
    .string()
    .min(8, 'Min 8 karakter')
    .regex(/[a-zA-Z]/, 'Harus ada huruf')
    .regex(/[0-9]/, 'Harus ada angka'),
})

const form = reactive({ full_name: '', password: '' })
const isLoading = ref(false)
const errorMsg = ref('')

async function onSubmit() {
  errorMsg.value = ''
  isLoading.value = true
  try {
    await acceptInvite(slugFromQuery.value, {
      token: token.value,
      full_name: form.full_name,
      password: form.password,
    })
    await navigateTo('/app')
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    errorMsg.value = t(`error.${e.code ?? 'unknown'}`, t('error.unknown'))
  }
  finally {
    isLoading.value = false
  }
}
</script>

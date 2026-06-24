<template>
  <NuxtLayout name="auth-split">
    <!-- Aside content -->
    <template #aside>
      <p class="text-[11px] font-bold uppercase tracking-[0.16em] mb-4" style="color:#b9a3e8;">
        {{ t('auth.login.aside_eyebrow') }}
      </p>
      <h2 class="text-[27px] font-semibold leading-tight mb-4" style="font-family:'Bricolage Grotesque',sans-serif; color:#fff;">
        {{ t('auth.login.aside_headline') }}
      </h2>
      <p class="text-sm" style="color:#a79fbd;">{{ t('auth.login.aside_body') }}</p>
      <div class="flex gap-7 mt-8">
        <div>
          <div class="text-[22px] font-bold" style="font-family:'Bricolage Grotesque',sans-serif; color:#fff;">
            {{ t('auth.login.aside_stat1_v') }}
          </div>
          <div class="text-[11.5px] mt-0.5" style="color:#928aa8;">{{ t('auth.login.aside_stat1_l') }}</div>
        </div>
        <div>
          <div class="text-[22px] font-bold" style="font-family:'Bricolage Grotesque',sans-serif; color:#fff;">
            {{ t('auth.login.aside_stat2_v') }}
          </div>
          <div class="text-[11.5px] mt-0.5" style="color:#928aa8;">{{ t('auth.login.aside_stat2_l') }}</div>
        </div>
      </div>
    </template>

    <!-- Main form -->
    <div class="w-full max-w-[420px]">
      <div v-if="errorMsg" class="mb-5 flex items-start gap-3 rounded-xl px-4 py-3 text-sm" style="background:#f8e2dc; color:#d2553f; border:1px solid #f3c4b9;">
        <span class="mt-0.5 shrink-0">⚠</span>
        <span>{{ errorMsg }}</span>
      </div>
      <div v-if="route.query.registered" class="mb-5 flex items-start gap-3 rounded-xl px-4 py-3 text-sm" style="background:#dcf1e8; color:#2f9e6f; border:1px solid #b4e2cd;">
        <span class="mt-0.5 shrink-0">✓</span>
        <span>{{ t('auth.login.registered_success') }} <b>{{ route.query.slug }}</b>.</span>
      </div>

      <p class="text-[11px] font-bold uppercase tracking-[0.14em] mb-2.5" style="color:#7250ba;">
        {{ t('auth.login.eyebrow') }}
      </p>
      <h1 class="text-[26px] font-bold mb-2" style="font-family:'Bricolage Grotesque',sans-serif; color:#1c1726; letter-spacing:-0.02em;">
        {{ t('auth.login.title') }}
      </h1>
      <p class="text-sm mb-7" style="color:#6b6478;">{{ t('auth.login.subtitle') }}</p>

      <form class="space-y-4" @submit.prevent="onSubmit">
        <!-- Workspace -->
        <div>
          <label class="block text-[12.5px] font-semibold mb-1.5" style="color:#34303d;">
            {{ t('auth.login.workspace') }}
          </label>
          <div
            class="flex items-center rounded-[10px] px-3 transition-all"
            style="border:1px solid #e3e0ea; background:#fff;"
            :style="focusField === 'slug' ? 'border-color:#7250ba; box-shadow:0 0 0 3px rgba(114,80,186,.13);' : ''"
          >
            <input
              v-model="form.slug"
              type="text"
              :placeholder="locale === 'id' ? 'nama-workspace' : 'your-workspace'"
              class="flex-1 bg-transparent outline-none text-sm py-[11px]"
              style="color:#27252c;"
              :disabled="isLoading"
              @focus="focusField = 'slug'"
              @blur="focusField = ''"
            />
            <span class="text-xs ml-2 shrink-0 font-mono" style="color:#a39db0;">.pranata.app</span>
          </div>
          <p v-if="errors.slug" class="mt-1 text-xs" style="color:#d2553f;">{{ errors.slug }}</p>
        </div>

        <!-- Email -->
        <div>
          <label class="block text-[12.5px] font-semibold mb-1.5" style="color:#34303d;">
            {{ t('auth.login.email') }}
          </label>
          <input
            v-model="form.email"
            type="email"
            placeholder="you@company.com"
            class="w-full rounded-[10px] px-3 py-[11px] text-sm outline-none transition-all"
            style="border:1px solid #e3e0ea; background:#fff; color:#27252c;"
            :style="focusField === 'email' ? 'border-color:#7250ba; box-shadow:0 0 0 3px rgba(114,80,186,.13);' : ''"
            :disabled="isLoading"
            @focus="focusField = 'email'"
            @blur="focusField = ''"
          />
          <p v-if="errors.email" class="mt-1 text-xs" style="color:#d2553f;">{{ errors.email }}</p>
        </div>

        <!-- Password -->
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <label class="text-[12.5px] font-semibold" style="color:#34303d;">{{ t('auth.login.password') }}</label>
            <a href="#" class="text-xs font-semibold" style="color:#5d3fa0;">{{ t('auth.login.forgot') }}</a>
          </div>
          <div
            class="flex items-center rounded-[10px] px-3 transition-all"
            style="border:1px solid #e3e0ea; background:#fff;"
            :style="focusField === 'password' ? 'border-color:#7250ba; box-shadow:0 0 0 3px rgba(114,80,186,.13);' : ''"
          >
            <input
              v-model="form.password"
              :type="showPass ? 'text' : 'password'"
              :placeholder="locale === 'id' ? 'Masukkan kata sandi' : 'Enter your password'"
              class="flex-1 bg-transparent outline-none text-sm py-[11px]"
              style="color:#27252c;"
              :disabled="isLoading"
              @focus="focusField = 'password'"
              @blur="focusField = ''"
            />
            <button type="button" class="ml-2 text-sm" style="color:#a39db0;" @click="showPass = !showPass">
              {{ showPass ? '🙈' : '👁' }}
            </button>
          </div>
          <p v-if="errors.password" class="mt-1 text-xs" style="color:#d2553f;">{{ errors.password }}</p>
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full mt-1 rounded-[10px] py-3 text-sm font-semibold text-white transition-all"
          style="background:#7250ba;"
          :style="isLoading ? 'opacity:0.75; cursor:not-allowed;' : 'cursor:pointer;'"
        >
          {{ isLoading ? t('auth.login.submitting') : t('auth.login.submit') }}
        </button>
      </form>

      <p class="mt-6 text-center text-[13px]" style="color:#6b6478;">
        {{ t('auth.login.no_account') }}
        <NuxtLink to="/register" class="font-semibold ml-1" style="color:#5d3fa0;">
          {{ t('auth.login.register_link') }}
        </NuxtLink>
      </p>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
import { z } from 'zod'

definePageMeta({ layout: false })

const { t, locale } = useI18n()
const route = useRoute()
const { login } = useAuth()

const form = reactive({ slug: (route.query.slug as string) ?? '', email: '', password: '' })
const errors = reactive({ slug: '', email: '', password: '' })
const isLoading = ref(false)
const errorMsg = ref('')
const focusField = ref('')
const showPass = ref(false)

const schema = z.object({
  slug: z.string().min(1, 'Workspace wajib diisi'),
  email: z.string().email('Format email tidak valid'),
  password: z.string().min(1, 'Kata sandi wajib diisi'),
})

async function onSubmit() {
  errors.slug = ''
  errors.email = ''
  errors.password = ''
  errorMsg.value = ''

  const result = schema.safeParse(form)
  if (!result.success) {
    for (const issue of result.error.issues) {
      const field = issue.path[0] as keyof typeof errors
      if (field in errors) errors[field] = issue.message
    }
    return
  }
  isLoading.value = true
  try {
    await login(form.slug, { email: form.email, password: form.password })
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

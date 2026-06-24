<template>
  <div class="w-full max-w-[470px]">
    <!-- Card -->
    <div class="bg-white rounded-2xl p-10" style="border:1px solid #e3e0ea; box-shadow:0 1px 2px rgba(28,23,38,.06),0 8px 24px rgba(28,23,38,.07);">

      <!-- Logo + Lang -->
      <div class="flex items-center justify-between mb-7">
        <AppLogo :size="32" />
        <AppLangSwitcher />
      </div>

      <!-- Stepper -->
      <div class="flex items-center mb-7">
        <div v-for="(stepLabel, i) in steps" :key="i" class="flex items-center">
          <div class="flex items-center gap-2">
            <!-- Bubble -->
            <div
              class="w-[26px] h-[26px] rounded-full flex items-center justify-center text-xs font-bold border transition-all"
              :style="stepStyle(i + 1)"
            >
              <span v-if="step > i + 1">v</span>
              <span v-else>{{ i + 1 }}</span>
            </div>
            <!-- Label -->
            <span
              class="text-xs font-semibold"
              :style="step === i + 1 ? 'color:#1c1726;' : step > i + 1 ? 'color:#4b4556;' : 'color:#a39db0;'"
            >
              {{ stepLabel }}
            </span>
          </div>
          <!-- Bar between steps -->
          <div v-if="i < steps.length - 1" class="w-8 h-0.5 mx-2.5" style="background:#e3e0ea;" />
        </div>
      </div>

      <!-- Error -->
      <div v-if="errorMsg" class="mb-5 flex items-start gap-3 rounded-xl px-4 py-3 text-sm" style="background:#f8e2dc; color:#d2553f; border:1px solid #f3c4b9;">
        <span class="shrink-0 mt-0.5">!</span>
        <span>{{ errorMsg }}</span>
      </div>

      <!-- Step 1: Admin account -->
      <form v-if="step === 1" @submit.prevent="handleStep1">
        <h2 class="text-[22px] font-bold mb-2" style="font-family:'Bricolage Grotesque',sans-serif; color:#1c1726; letter-spacing:-0.02em;">
          {{ t('auth.register.title_step1') }}
        </h2>
        <p class="text-sm mb-6" style="color:#6b6478;">{{ t('auth.register.subtitle_step2') }}</p>

        <div class="space-y-4">
          <div>
            <label class="block text-[12.5px] font-semibold mb-1.5" style="color:#34303d;">{{ t('auth.register.full_name') }}</label>
            <input
              v-model="s1.full_name"
              type="text"
              placeholder="Nama lengkap Anda"
              class="w-full rounded-[10px] px-3 py-[11px] text-sm outline-none transition-all"
              :style="inputStyle('full_name')"
              @focus="focusField = 'full_name'"
              @blur="focusField = ''"
            />
            <p v-if="s1Errors.full_name" class="mt-1 text-xs" style="color:#d2553f;">{{ s1Errors.full_name }}</p>
          </div>

          <div>
            <label class="block text-[12.5px] font-semibold mb-1.5" style="color:#34303d;">{{ t('auth.register.email') }}</label>
            <input
              v-model="s1.email"
              type="email"
              placeholder="you@company.com"
              class="w-full rounded-[10px] px-3 py-[11px] text-sm outline-none transition-all"
              :style="inputStyle('email')"
              @focus="focusField = 'email'"
              @blur="focusField = ''"
            />
            <p v-if="s1Errors.email" class="mt-1 text-xs" style="color:#d2553f;">{{ s1Errors.email }}</p>
          </div>

          <div>
            <label class="block text-[12.5px] font-semibold mb-1.5" style="color:#34303d;">{{ t('auth.register.password') }}</label>
            <div
              class="flex items-center rounded-[10px] px-3 transition-all"
              :style="wrapStyle('password')"
            >
              <input
                v-model="s1.password"
                :type="showPass ? 'text' : 'password'"
                placeholder="Min 8 karakter, 1 huruf + 1 angka"
                class="flex-1 outline-none text-sm py-[11px]"
                style="color:#27252c; background:transparent;"
                @focus="focusField = 'password'"
                @blur="focusField = ''"
              />
              <button type="button" class="ml-2 text-xs shrink-0" style="color:#a39db0;" @click="showPass = !showPass">
                {{ showPass ? 'sembunyikan' : 'tampilkan' }}
              </button>
            </div>
            <p v-if="s1Errors.password" class="mt-1 text-xs" style="color:#d2553f;">{{ s1Errors.password }}</p>
          </div>

          <div>
            <label class="block text-[12.5px] font-semibold mb-1.5" style="color:#34303d;">Konfirmasi kata sandi</label>
            <div
              class="flex items-center rounded-[10px] px-3 transition-all"
              :style="wrapStyle('confirm_password')"
            >
              <input
                v-model="s1.confirm_password"
                :type="showConfirm ? 'text' : 'password'"
                placeholder="Ulangi kata sandi"
                class="flex-1 outline-none text-sm py-[11px]"
                style="color:#27252c; background:transparent;"
                @focus="focusField = 'confirm_password'"
                @blur="focusField = ''"
              />
              <button type="button" class="ml-2 text-xs shrink-0" style="color:#a39db0;" @click="showConfirm = !showConfirm">
                {{ showConfirm ? 'sembunyikan' : 'tampilkan' }}
              </button>
            </div>
            <p v-if="s1Errors.confirm_password" class="mt-1 text-xs" style="color:#d2553f;">{{ s1Errors.confirm_password }}</p>
          </div>
        </div>

        <button
          type="submit"
          class="w-full mt-6 rounded-[10px] py-3 text-sm font-semibold text-white"
          style="background:#7250ba;"
        >
          {{ t('auth.register.submit') }}
        </button>
      </form>

      <!-- Step 2: Organization -->
      <form v-if="step === 2" @submit.prevent="handleStep2">
        <h2 class="text-[22px] font-bold mb-2" style="font-family:'Bricolage Grotesque',sans-serif; color:#1c1726; letter-spacing:-0.02em;">
          {{ t('auth.register.title_step2') }}
        </h2>
        <p class="text-sm mb-6" style="color:#6b6478;">
          {{ t('auth.register.subtitle_step2') }}
        </p>

        <div class="space-y-4">
          <div>
            <label class="block text-[12.5px] font-semibold mb-1.5" style="color:#34303d;">{{ t('auth.register.organization_name') }}</label>
            <input
              v-model="s2.organization_name"
              type="text"
              placeholder="PT Nama Perusahaan"
              :disabled="isLoading"
              class="w-full rounded-[10px] px-3 py-[11px] text-sm outline-none transition-all"
              :style="focusField === 'org'
                ? 'border:1px solid #7250ba; box-shadow:0 0 0 3px rgba(114,80,186,.13); color:#27252c;'
                : 'border:1px solid #e3e0ea; color:#27252c;'"
              @focus="focusField = 'org'"
              @blur="focusField = ''"
            />
            <p v-if="s2Errors.organization_name" class="mt-1 text-xs" style="color:#d2553f;">{{ s2Errors.organization_name }}</p>
          </div>

          <div>
            <label class="block text-[12.5px] font-semibold mb-1.5" style="color:#34303d;">{{ t('auth.register.slug') }}</label>
            <div
              class="flex items-center rounded-[10px] px-3 transition-all"
              :style="focusField === 'slug'
                ? 'border:1px solid #7250ba; box-shadow:0 0 0 3px rgba(114,80,186,.13);'
                : 'border:1px solid #e3e0ea;'"
            >
              <input
                v-model="s2.slug"
                type="text"
                placeholder="nama-workspace"
                :disabled="isLoading"
                class="flex-1 bg-transparent outline-none text-sm py-[11px]"
                style="color:#27252c;"
                @focus="focusField = 'slug'"
                @blur="focusField = ''"
              />
              <span class="text-xs ml-2 shrink-0 font-mono" style="color:#a39db0;">.pranata.app</span>
            </div>
            <p v-if="s2Errors.slug" class="mt-1 text-xs" style="color:#d2553f;">{{ s2Errors.slug }}</p>
            <p v-else class="mt-1 text-xs" style="color:#a39db0;">{{ t('auth.register.slug_hint') }}</p>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[12.5px] font-semibold mb-1.5" style="color:#34303d;">{{ t('auth.register.industry') }}</label>
              <div
                class="flex items-center rounded-[10px] px-3 transition-all"
                style="border:1px solid #e3e0ea;"
              >
                <select
                  v-model="s2.industry"
                  :disabled="isLoading"
                  class="flex-1 bg-transparent outline-none text-sm py-[11px] appearance-none"
                  style="color:#27252c;"
                >
                  <option value="" disabled>Pilih industri</option>
                  <option v-for="opt in industryOptions" :key="opt" :value="opt">{{ opt }}</option>
                </select>
                <span class="text-xs ml-1 shrink-0" style="color:#a39db0;">v</span>
              </div>
            </div>
            <div>
              <label class="block text-[12.5px] font-semibold mb-1.5" style="color:#34303d;">{{ t('auth.register.team_size') }}</label>
              <div
                class="flex items-center rounded-[10px] px-3 transition-all"
                style="border:1px solid #e3e0ea;"
              >
                <select
                  v-model="s2.team_size"
                  :disabled="isLoading"
                  class="flex-1 bg-transparent outline-none text-sm py-[11px] appearance-none"
                  style="color:#27252c;"
                >
                  <option value="" disabled>Ukuran tim</option>
                  <option v-for="opt in teamSizeOptions" :key="opt" :value="opt">{{ opt }}</option>
                </select>
                <span class="text-xs ml-1 shrink-0" style="color:#a39db0;">v</span>
              </div>
            </div>
          </div>
        </div>

        <div class="flex gap-3 mt-6">
          <button
            type="button"
            :disabled="isLoading"
            class="flex-1 rounded-[10px] py-3 text-sm font-semibold transition-all"
            style="background:#fff; border:1px solid #e3e0ea; color:#34303d;"
            @click="goBack"
          >
            {{ t('auth.register.back') }}
          </button>
          <button
            type="submit"
            :disabled="isLoading"
            class="flex-1 rounded-[10px] py-3 text-sm font-semibold text-white transition-all"
            style="background:#7250ba;"
            :style="isLoading ? 'opacity:0.75;' : ''"
          >
            {{ isLoading ? t('auth.register.submitting') : t('auth.register.submit') }}
          </button>
        </div>
      </form>

      <!-- Footer -->
      <p class="mt-6 text-center text-[13px]" style="color:#6b6478;">
        {{ t('auth.register.have_account') }}
        <NuxtLink to="/login" class="font-semibold ml-1" style="color:#5d3fa0;">
          {{ t('auth.register.login_link') }}
        </NuxtLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { z } from 'zod'

definePageMeta({ layout: 'auth' })

const { t } = useI18n()
const { registerTenant } = useAuth()

const step = ref(1)
const isLoading = ref(false)
const errorMsg = ref('')
const focusField = ref('')
const showPass = ref(false)
const showConfirm = ref(false)

const steps = computed(() => [
  t('auth.register.step1'),
  t('auth.register.step2'),
  t('auth.register.step3'),
])

function stepStyle(s: number) {
  if (step.value > s) return 'background:#2f9e6f; border-color:#2f9e6f; color:#fff;'
  if (step.value === s) return 'background:#7250ba; border-color:#7250ba; color:#fff;'
  return 'background:#f8f7fb; border-color:#e3e0ea; color:#a39db0;'
}

function inputStyle(field: string) {
  const base = 'background:#fff; color:#27252c;'
  return focusField.value === field
    ? base + 'border:1px solid #7250ba; box-shadow:0 0 0 3px rgba(114,80,186,.13);'
    : base + 'border:1px solid #e3e0ea;'
}

function wrapStyle(field: string) {
  const base = 'background:#fff;'
  return focusField.value === field
    ? base + 'border:1px solid #7250ba; box-shadow:0 0 0 3px rgba(114,80,186,.13);'
    : base + 'border:1px solid #e3e0ea;'
}

const s1 = reactive({ full_name: '', email: '', password: '', confirm_password: '' })
const s1Errors = reactive({ full_name: '', email: '', password: '', confirm_password: '' })

const s2 = reactive({ organization_name: '', slug: '', industry: '', team_size: '' })
const s2Errors = reactive({ organization_name: '', slug: '' })

const industryOptions = ['Technology', 'Finance', 'Healthcare', 'Education', 'Retail', 'Manufacturing', 'Consulting', 'Lainnya']
const teamSizeOptions = ['1-10', '11-50', '51-200', '201-500', '500+']

const step1Schema = z.object({
  full_name: z.string().min(1, 'Nama wajib diisi'),
  email: z.string().email('Format email tidak valid'),
  password: z.string().min(8, 'Min 8 karakter').regex(/[a-zA-Z]/, 'Harus ada huruf').regex(/[0-9]/, 'Harus ada angka'),
  confirm_password: z.string().min(1, 'Konfirmasi kata sandi wajib diisi'),
}).refine(d => d.password === d.confirm_password, {
  message: 'Kata sandi tidak cocok',
  path: ['confirm_password'],
})

function goBack() {
  step.value = 1
}

function handleStep1() {
  s1Errors.full_name = ''
  s1Errors.email = ''
  s1Errors.password = ''
  s1Errors.confirm_password = ''
  const result = step1Schema.safeParse(s1)
  if (!result.success) {
    for (const issue of result.error.issues) {
      const field = issue.path[0] as keyof typeof s1Errors
      if (field in s1Errors) s1Errors[field] = issue.message
    }
    return
  }
  step.value = 2
}

const step2Schema = z.object({
  organization_name: z.string().min(1, 'Nama organisasi wajib diisi'),
  slug: z.string().min(3, 'Min 3 karakter').max(63, 'Max 63 karakter').regex(/^[a-z0-9][a-z0-9-]*[a-z0-9]$/, 'Hanya huruf kecil, angka, dan tanda hubung'),
})

async function handleStep2() {
  s2Errors.organization_name = ''
  s2Errors.slug = ''
  errorMsg.value = ''
  const result = step2Schema.safeParse(s2)
  if (!result.success) {
    for (const issue of result.error.issues) {
      const field = issue.path[0] as keyof typeof s2Errors
      if (field in s2Errors) s2Errors[field] = issue.message
    }
    return
  }
  isLoading.value = true
  try {
    await registerTenant({
      full_name: s1.full_name,
      email: s1.email,
      password: s1.password,
      organization_name: s2.organization_name,
      slug: s2.slug,
      industry: s2.industry || undefined,
      team_size: s2.team_size || undefined,
    })
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    errorMsg.value = t(`error.${e.code ?? 'unknown'}`, t('error.unknown'))
    if (e.code === 'AUTH_SLUG_TAKEN') step.value = 2
  }
  finally {
    isLoading.value = false
  }
}
</script>

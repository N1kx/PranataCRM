<template>
  <div class="space-y-6 max-w-3xl">
    <!-- Header -->
    <div class="flex items-center gap-3">
      <UButton
        icon="i-lucide-arrow-left"
        color="neutral"
        variant="ghost"
        to="/app/contacts"
        :aria-label="t('contacts.back_to_list')"
      />
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('contacts.edit') }}
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
        <AppButton color="error" variant="outline" size="xs" class="mt-2" @click="loadContact">
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

    <UCard v-else-if="contact">
      <ContactsForm :contact="contact" @saved="onSaved" @cancel="navigateTo('/app/contacts')" />
    </UCard>
  </div>
</template>

<script setup lang="ts">
import type { Contact } from '~/types/contacts'

definePageMeta({ layout: 'app', middleware: 'auth' })

const { t } = useI18n()
const { get } = useContacts()
const toast = useToast()
const route = useRoute()

const contactId = route.params.id as string
const contact = ref<Contact | null>(null)
const isLoading = ref(false)
const loadErrorCode = ref('')

async function loadContact() {
  isLoading.value = true
  loadErrorCode.value = ''
  try {
    contact.value = await get(contactId)
  }
  catch (err: unknown) {
    const e = err as { code?: string }
    loadErrorCode.value = e.code ?? 'unknown'
  }
  finally {
    isLoading.value = false
  }
}

onMounted(loadContact)

async function onSaved() {
  toast.add({ title: t('contacts.saved'), color: 'success', icon: 'i-lucide-check-circle' })
  await navigateTo('/app/contacts')
}
</script>

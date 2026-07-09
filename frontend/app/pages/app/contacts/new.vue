<template>
  <div class="space-y-6 max-w-3xl">
    <!-- Header -->
    <div class="flex items-center gap-3">
      <UButton
        icon="i-lucide-arrow-left"
        color="gray"
        variant="ghost"
        to="/app/contacts"
        :aria-label="t('contacts.back_to_list')"
      />
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('contacts.add') }}
      </h1>
    </div>

    <UCard>
      <ContactsForm @saved="onSaved" @cancel="navigateTo('/app/contacts')" />
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'app', middleware: 'auth' })

const { t } = useI18n()
const toast = useToast()

async function onSaved() {
  toast.add({ title: t('contacts.created'), color: 'green', icon: 'i-lucide-check-circle' })
  await navigateTo('/app/contacts')
}
</script>

<template>
  <aside class="flex flex-col h-full bg-gray-900 text-white w-[232px] shrink-0">
    <!-- Logo + TenantSwitcher -->
    <div class="p-4 border-b border-gray-800">
      <div class="flex items-center justify-between">
        <AppLogo icon-only class="mr-2" />
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold truncate">
            {{ tenantSlug || 'Workspace' }}
          </p>
          <p class="text-xs text-gray-400 capitalize">
            {{ user?.suite_role?.replace('_', ' ') || 'Free plan' }}
          </p>
        </div>
        <UIcon name="i-lucide-chevrons-up-down" class="text-gray-400 shrink-0" />
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto p-3 space-y-6">
      <!-- Workspace -->
      <div>
        <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2 mb-1">
          {{ t('nav.workspace') }}
        </p>
        <ul class="space-y-0.5">
          <AppNavItem to="/app" :label="t('nav.dashboard')" icon="i-lucide-layout-dashboard" exact />
          <AppNavItem to="/app/contacts" :label="t('nav.contacts')" icon="i-lucide-users" />
          <AppNavItem to="/app/companies" :label="t('nav.companies')" icon="i-lucide-building-2" />
          <AppNavItem to="/app/deals" :label="t('nav.deals')" icon="i-lucide-handshake" />
          <AppNavItem to="/app/activities" :label="t('nav.activities')" icon="i-lucide-calendar-check" />
        </ul>
      </div>

      <!-- Intelligence -->
      <div>
        <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2 mb-1">
          {{ t('nav.intelligence') }}
        </p>
        <ul class="space-y-0.5">
          <AppNavItem to="/app/ai" :label="t('nav.ai_insights')" icon="i-lucide-sparkles" />
          <AppNavItem to="/app/follow-up" :label="t('nav.follow_up')" icon="i-lucide-bell" />
          <!-- TODO: load effective permissions (usePermission().can('crm.reporting.view')) -->
          <AppNavItem to="/app/reporting" :label="t('nav.reporting')" icon="i-lucide-bar-chart-2" />
        </ul>
      </div>

      <!-- Settings — owner/admin only -->
      <div v-if="isOwnerOrAdmin">
        <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2 mb-1">
          {{ t('nav.settings') }}
        </p>
        <ul class="space-y-0.5">
          <AppNavItem to="/app/settings/team" :label="t('nav.team')" icon="i-lucide-users-round" />
          <AppNavItem to="/app/settings/roles" :label="t('nav.roles')" icon="i-lucide-shield-check" />
          <AppNavItem to="/app/settings/billing" :label="t('nav.billing')" icon="i-lucide-credit-card" />
        </ul>
      </div>
    </nav>

    <!-- UserChip + Logout -->
    <div class="p-3 border-t border-gray-800">
      <UDropdown :items="userMenuItems" :ui="{ item: { padding: 'px-3 py-2' } }">
        <button class="flex items-center gap-3 w-full rounded-lg px-2 py-2 hover:bg-gray-800 transition-colors">
          <UAvatar
            :alt="user?.full_name || '?'"
            size="sm"
            class="bg-violet-600 text-white"
          />
          <div class="flex-1 min-w-0 text-left">
            <p class="text-sm font-medium truncate">
              {{ user?.full_name || '—' }}
            </p>
            <p class="text-xs text-gray-400 truncate">
              {{ roleLabel }}
            </p>
          </div>
          <UIcon name="i-lucide-more-horizontal" class="text-gray-400" />
        </button>
      </UDropdown>
    </div>
  </aside>
</template>

<script setup lang="ts">
const { t } = useI18n()
const { user, isOwnerOrAdmin, tenantSlug, logout } = useAuth()

const roleLabel = computed(() => {
  const roleMap: Record<string, string> = {
    tenant_owner: 'Owner',
    tenant_admin: 'Admin',
    member: 'Member',
  }
  return roleMap[user.value?.suite_role ?? ''] ?? '—'
})

const userMenuItems = computed(() => [[
  {
    label: t('auth.logout'),
    icon: 'i-lucide-log-out',
    click: logout,
  },
]])
</script>

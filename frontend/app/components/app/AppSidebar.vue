<template>
  <aside
    class="flex flex-col h-full bg-gray-900 text-white shrink-0 transition-[width] duration-200"
    :class="collapsed ? 'w-16' : 'w-[232px]'"
  >
    <!-- Logo + TenantSwitcher -->
    <div class="p-4 border-b border-gray-800">
      <div class="flex items-center gap-2">
        <AppLogo icon-only class="shrink-0" />
        <div v-if="!collapsed" class="flex-1 min-w-0">
          <p class="text-sm font-semibold truncate">
            {{ tenantSlug || 'Workspace' }}
          </p>
          <p class="text-xs text-gray-400 capitalize">
            {{ user?.suite_role?.replace('_', ' ') || 'Free plan' }}
          </p>
        </div>
        <UButton
          v-if="!collapsed && collapsible"
          icon="i-lucide-panel-left-close"
          color="neutral"
          variant="ghost"
          size="xs"
          :aria-label="t('nav.collapse_sidebar')"
          @click="emit('toggle-collapse')"
        />
      </div>
      <UButton
        v-if="collapsed && collapsible"
        icon="i-lucide-panel-left-open"
        color="neutral"
        variant="ghost"
        size="xs"
        block
        class="mt-2"
        :aria-label="t('nav.expand_sidebar')"
        @click="emit('toggle-collapse')"
      />
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto p-3 space-y-6">
      <!-- Workspace -->
      <div>
        <p v-if="!collapsed" class="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2 mb-1">
          {{ t('nav.workspace') }}
        </p>
        <ul class="space-y-0.5">
          <AppNavItem to="/app" :label="t('nav.dashboard')" icon="i-lucide-layout-dashboard" exact :collapsed="collapsed" />
          <AppNavItem to="/app/contacts" :label="t('nav.contacts')" icon="i-lucide-users" :collapsed="collapsed" />
          <AppNavItem to="/app/companies" :label="t('nav.companies')" icon="i-lucide-building-2" :collapsed="collapsed" />
          <AppNavItem to="/app/deals" :label="t('nav.deals')" icon="i-lucide-handshake" :collapsed="collapsed" />
          <AppNavItem to="/app/activities" :label="t('nav.activities')" icon="i-lucide-calendar-check" :collapsed="collapsed" />
        </ul>
      </div>

      <!-- Intelligence -->
      <div>
        <p v-if="!collapsed" class="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2 mb-1">
          {{ t('nav.intelligence') }}
        </p>
        <ul class="space-y-0.5">
          <AppNavItem to="/app/ai" :label="t('nav.ai_insights')" icon="i-lucide-sparkles" :collapsed="collapsed" />
          <AppNavItem to="/app/follow-up" :label="t('nav.follow_up')" icon="i-lucide-bell" :collapsed="collapsed" />
          <!-- TODO: load effective permissions (usePermission().can('crm.reporting.view')) -->
          <AppNavItem to="/app/reporting" :label="t('nav.reporting')" icon="i-lucide-bar-chart-2" :collapsed="collapsed" />
        </ul>
      </div>

      <!-- Settings — owner/admin only -->
      <div v-if="isOwnerOrAdmin">
        <p v-if="!collapsed" class="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2 mb-1">
          {{ t('nav.settings') }}
        </p>
        <ul class="space-y-0.5">
          <AppNavItem to="/app/settings/team" :label="t('nav.team')" icon="i-lucide-users-round" :collapsed="collapsed" />
          <AppNavItem to="/app/settings/roles" :label="t('nav.roles')" icon="i-lucide-shield-check" :collapsed="collapsed" />
          <AppNavItem to="/app/settings/billing" :label="t('nav.billing')" icon="i-lucide-credit-card" :collapsed="collapsed" />
          <!-- Geo reference data (issue #26) is gated tighter than the rest
               of Settings — tenant_owner only, enforced server-side too
               (see admin_router.py's TODO on the interim role gate). -->
          <AppNavItem
            v-if="user?.suite_role === 'tenant_owner'"
            to="/app/settings/geo"
            :label="t('nav.geo')"
            icon="i-lucide-map-pin"
            :collapsed="collapsed"
          />
        </ul>
      </div>
    </nav>

    <!-- UserChip + Logout -->
    <div class="p-3 border-t border-gray-800">
      <UDropdownMenu :items="userMenuItems" :ui="{ item: 'px-3 py-2' }">
        <button
          class="flex items-center gap-3 w-full rounded-lg px-2 py-2 hover:bg-gray-800 transition-colors"
          :class="collapsed && 'justify-center'"
        >
          <UAvatar
            :alt="user?.full_name || '?'"
            size="sm"
            class="bg-violet-600 text-white shrink-0"
          />
          <template v-if="!collapsed">
            <div class="flex-1 min-w-0 text-left">
              <p class="text-sm font-medium truncate">
                {{ user?.full_name || '—' }}
              </p>
              <p class="text-xs text-gray-400 truncate">
                {{ roleLabel }}
              </p>
            </div>
            <UIcon name="i-lucide-more-horizontal" class="text-gray-400" />
          </template>
        </button>
      </UDropdownMenu>
    </div>
  </aside>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  /** Icon-only rail (desktop). */
  collapsed?: boolean
  /** Whether the collapse toggle button is shown - hidden on the mobile drawer copy. */
  collapsible?: boolean
}>(), {
  collapsed: false,
  collapsible: false,
})

const emit = defineEmits<{ 'toggle-collapse': [] }>()

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
    onSelect: logout,
  },
]])
</script>

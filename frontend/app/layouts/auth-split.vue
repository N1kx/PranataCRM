<template>
  <div class="min-h-screen flex">
    <!-- Left aside: dark brand panel -->
    <aside
      class="hidden lg:flex w-[480px] shrink-0 flex-col p-11 relative overflow-hidden"
      style="background: radial-gradient(120% 120% at 0% 0%, #2a1f44 0%, #1c1726 62%);"
    >
      <!-- Glow orb -->
      <div
        class="absolute -right-20 -bottom-20 w-80 h-80 rounded-full pointer-events-none"
        style="background: radial-gradient(circle, rgba(114,80,186,.28), transparent 70%);"
      />

      <AppLogo :size="34" dark class="relative z-10" />

      <div class="mt-auto relative z-10">
        <slot name="aside" />
      </div>
    </aside>

    <!-- Right: form area -->
    <div class="flex-1 flex flex-col min-h-screen" style="background:#f8f7fb;">
      <div class="flex justify-end px-6 py-4">
        <AppLangSwitcher />
      </div>
      <div class="flex-1 flex items-center justify-center p-8">
        <slot />
      </div>
    </div>
  </div>
</template>

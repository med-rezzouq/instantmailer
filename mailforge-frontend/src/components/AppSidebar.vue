<template>
  <aside
    :class="[
      'fixed top-0 left-0 h-full z-50 flex flex-col w-60',
      'bg-white dark:bg-[#1c1b19] border-r border-gray-200 dark:border-gray-800',
      'transition-transform duration-300 ease-in-out',
      'lg:translate-x-0',
      open ? 'translate-x-0' : '-translate-x-full',
    ]"
  >
    <div
      class="flex items-center justify-between gap-3 p-5 border-b border-gray-200 dark:border-gray-800"
    >
      <div class="flex items-center gap-3">
        <svg class="w-8 h-8 flex-shrink-0" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="#01696f" />
          <path
            d="M6 10L16 18L26 10"
            stroke="white"
            stroke-width="2"
            stroke-linecap="round"
          />
          <path
            d="M6 10H26V23C26 23.55 25.55 24 25 24H7C6.45 24 6 23.55 6 23V10Z"
            stroke="white"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <span class="font-bold text-xl tracking-tight">MailForge</span>
      </div>
      <button
        class="lg:hidden text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
        @click="$emit('close')"
      >
        <svg
          class="w-5 h-5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>

    <nav class="flex-1 p-3 flex flex-col gap-1 overflow-y-auto">
      <p class="nav-section-label">Main</p>
      <RouterLink
        v-for="item in mainNav"
        :key="item.to"
        :to="item.to"
        custom
        v-slot="{ isActive, navigate }"
      >
        <div
          :class="['nav-item', isActive && 'active']"
          @click="
            navigate();
            $emit('close');
          "
        >
          <component :is="item.icon" class="w-[18px] h-[18px] flex-shrink-0" />
          {{ item.label }}
        </div>
      </RouterLink>

      <p class="nav-section-label mt-2">Audience</p>
      <RouterLink
        v-for="item in audienceNav"
        :key="item.to"
        :to="item.to"
        custom
        v-slot="{ isActive, navigate }"
      >
        <div
          :class="['nav-item', isActive && 'active']"
          @click="
            navigate();
            $emit('close');
          "
        >
          <component :is="item.icon" class="w-[18px] h-[18px] flex-shrink-0" />
          {{ item.label }}
        </div>
      </RouterLink>

      <p class="nav-section-label mt-2">Insights</p>
      <RouterLink
        v-for="item in insightNav"
        :key="item.to"
        :to="item.to"
        custom
        v-slot="{ isActive, navigate }"
      >
        <div
          :class="['nav-item', isActive && 'active']"
          @click="
            navigate();
            $emit('close');
          "
        >
          <component :is="item.icon" class="w-[18px] h-[18px] flex-shrink-0" />
          {{ item.label }}
        </div>
      </RouterLink>

      <p class="nav-section-label mt-2">Settings</p>
      <RouterLink
        v-for="item in settingsNav"
        :key="item.to"
        :to="item.to"
        custom
        v-slot="{ isActive, navigate }"
      >
        <div
          :class="['nav-item', isActive && 'active']"
          @click="
            navigate();
            $emit('close');
          "
        >
          <component :is="item.icon" class="w-[18px] h-[18px] flex-shrink-0" />
          {{ item.label }}
        </div>
      </RouterLink>
    </nav>

    <div class="p-4 border-t border-gray-200 dark:border-gray-800">
      <p class="nav-section-label mb-2">Email Providers</p>
      <button
        v-for="p in providers"
        :key="p.id"
        :class="['provider-pill', p.connected && 'connected']"
        @click="connectProvider(p.id)"
      >
        <span class="dot"></span>
        <span v-html="p.icon"></span>
        {{ p.label }}
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "@/api";

defineProps({ open: Boolean });
defineEmits(["close"]);

const IconGrid = {
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>`,
};
const IconEdit = {
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
};
const IconSend = {
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13"/><path d="M22 2L15 22l-4-9-9-4 20-7z"/></svg>`,
};
const IconUsers = {
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
};
const IconTemplate = {
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>`,
};
const IconBarChart = {
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
};
const IconServer = {
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>`,
};

const mainNav = [
  { to: "/dashboard", label: "Dashboard", icon: IconGrid },
  { to: "/compose", label: "Compose", icon: IconEdit },
  { to: "/campaigns", label: "Campaigns", icon: IconSend },
  { to: "/campaignTracking", label: "Campaign Tracking", icon: IconBarChart },
];
const audienceNav = [
  { to: "/contacts", label: "Contacts", icon: IconUsers },
  { to: "/templates", label: "Templates", icon: IconTemplate },
];
const insightNav = [
  { to: "/analytics", label: "Analytics", icon: IconBarChart },
];
const settingsNav = [
  { to: "/smtp", label: "SMTP Servers", icon: IconServer },
  { to: "/tracking", label: "Tracking Domains", icon: IconServer },
];

const providers = ref([
  {
    id: "microsoft",
    label: "Microsoft 365",
    connected: false,
    icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M11.4 24H0V12.6h11.4V24zM24 24H12.6V12.6H24V24zM11.4 11.4H0V0h11.4v11.4zM24 11.4H12.6V0H24v11.4z"/></svg>',
  },
  {
    id: "google",
    label: "Google Workspace",
    connected: false,
    icon: '<svg width="14" height="14" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>',
  },
]);

onMounted(async () => {
  try {
    const { data } = await api.get("/oauth/status");
    if (data.microsoft) providers.value[0].connected = true;
    if (data.google) providers.value[1].connected = true;
  } catch (_) {}
});
async function connectProvider(id) {
  try {
    const { data } = await api.get(`/oauth/${id}/connect`);
    window.location.href = data.auth_url;
  } catch (e) {
    console.error(e);
  }
}
</script>

<style scoped>
.nav-section-label {
  @apply text-xs uppercase tracking-widest text-gray-400 dark:text-gray-600 font-semibold px-3 py-2;
}
.nav-item {
  @apply flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 cursor-pointer transition-all hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-100;
}
.nav-item.active {
  @apply bg-teal-50 dark:bg-teal-900/30 text-teal-700 dark:text-teal-400 font-semibold;
}
.provider-pill {
  @apply flex items-center gap-2 px-3 py-2 rounded-full text-xs font-semibold mb-2 w-full border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 transition-all hover:opacity-80;
}
.provider-pill.connected {
  @apply bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border-green-300 dark:border-green-700;
}
.dot {
  @apply w-1.5 h-1.5 rounded-full bg-current flex-shrink-0;
}
</style>

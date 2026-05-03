<template>
  <header
    class="sticky top-0 z-30 bg-white dark:bg-[#1c1b19] border-b border-gray-200 dark:border-gray-800 px-4 md:px-6 h-14 flex items-center justify-between gap-4"
  >
    <!-- Hamburger (mobile only) -->
    <button
      class="lg:hidden flex items-center justify-center w-9 h-9 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      @click="$emit('toggle-sidebar')"
      aria-label="Toggle menu"
    >
      <svg
        class="w-5 h-5"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <line x1="3" y1="6" x2="21" y2="6" />
        <line x1="3" y1="12" x2="21" y2="12" />
        <line x1="3" y1="18" x2="21" y2="18" />
      </svg>
    </button>

    <!-- Page title (mobile) -->
    <span class="lg:hidden font-bold text-sm flex-1">{{ currentPage }}</span>

    <div class="flex items-center gap-3 ml-auto">
      <!-- Theme toggle -->
      <button
        class="w-9 h-9 flex items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        @click="toggleTheme"
      >
        <svg
          v-if="isDark"
          class="w-4 h-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="12" cy="12" r="5" />
          <path
            d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
          />
        </svg>
        <svg
          v-else
          class="w-4 h-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      </button>

      <!-- Avatar -->
      <div
        class="w-8 h-8 rounded-full bg-teal-600 flex items-center justify-center text-white text-xs font-bold select-none"
      >
        {{ initials }}
      </div>

      <!-- Logout -->
      <button
        class="hidden md:flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
        @click="logout"
      >
        <svg
          class="w-4 h-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
        Logout
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed, inject } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

defineEmits(["toggle-sidebar"]);

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();
const isDark = inject("isDark");
const toggleTheme = inject("toggleTheme");

const initials = computed(() => {
  const u = auth.user;
  if (!u) return "?";
  if (u.name)
    return u.name
      .split(" ")
      .map((w) => w[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  return u.email?.[0]?.toUpperCase() || "?";
});

const pageNames = {
  dashboard: "Dashboard",
  campaigns: "Campaigns",
  compose: "Compose",
  contacts: "Contacts",
  templates: "Templates",
  analytics: "Analytics",
  smtp: "SMTP Servers",
};
const currentPage = computed(() => pageNames[route.name] || "MailForge");

function logout() {
  auth.logout();
  router.push("/login");
}
</script>

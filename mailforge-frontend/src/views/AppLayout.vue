<template>
  <div class="flex min-h-screen">
    <AppSidebar :open="sidebarOpen" @close="sidebarOpen = false" />

    <!-- Mobile overlay -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 bg-black/50 z-40 lg:hidden"
      @click="sidebarOpen = false"
    />

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0 lg:ml-60">
      <AppTopbar @toggle-sidebar="sidebarOpen = !sidebarOpen" />
      <main class="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import AppSidebar from "@/components/AppSidebar.vue";
import AppTopbar from "@/components/AppTopbar.vue";

const sidebarOpen = ref(false);
</script>

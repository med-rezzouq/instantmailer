<template>
  <div :class="isDark ? 'dark' : ''" class="min-h-screen bg-gray-50 dark:bg-[#171614] text-gray-900 dark:text-gray-100 font-body">
    <RouterView />
    <ToastContainer />
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import ToastContainer from '@/components/ToastContainer.vue'

const isDark = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)
provide('toggleTheme', () => { isDark.value = !isDark.value })
provide('isDark', isDark)
</script>

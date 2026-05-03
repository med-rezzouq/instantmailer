<template>
  <div class="fixed bottom-6 right-6 z-[500] flex flex-col gap-3 pointer-events-none">
    <TransitionGroup name="toast">
      <div v-for="t in toasts" :key="t.id"
        :class="['pointer-events-auto flex items-center gap-3 px-5 py-3 rounded-xl text-sm font-medium shadow-lg min-w-[240px] border', toastClass(t.type)]">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <polyline v-if="t.type==='success'" points="20 6 9 17 4 12"/>
          <template v-else-if="t.type==='error'"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></template>
          <template v-else><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></template>
        </svg>
        {{ t.msg }}
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useToastStore } from '@/stores/toast'
import { storeToRefs } from 'pinia'
const { toasts } = storeToRefs(useToastStore())
function toastClass(type) {
  if (type==='success') return 'bg-success-light text-success dark:bg-success/20 dark:text-success-dark border-success dark:border-success-dark'
  if (type==='error')   return 'bg-danger-light text-danger dark:bg-danger/20 dark:text-danger-dark border-danger dark:border-danger-dark'
  return 'bg-primary-light/60 text-primary dark:bg-primary/20 dark:text-primary-dark border-primary dark:border-primary-dark'
}
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all .25s ease; }
.toast-enter-from { opacity:0; transform: translateX(20px); }
.toast-leave-to   { opacity:0; transform: translateX(20px); }
</style>

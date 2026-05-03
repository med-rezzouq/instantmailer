<template>
  <div>
    <div class="mb-6"><div class="page-title">Analytics</div><div class="page-subtitle">Performance across all campaigns</div></div>
    <div class="grid grid-cols-3 gap-4 mb-8">
      <div v-for="s in stats" :key="s.label" class="card">
        <div class="text-xs uppercase tracking-wider font-semibold text-gray-500 dark:text-gray-400 mb-2">{{ s.label }}</div>
        <div v-if="loading" class="h-10 w-24 rounded bg-gray-200 dark:bg-gray-700 animate-pulse"></div>
        <div v-else class="font-display text-3xl font-bold" :style="`color:${s.color}`">{{ s.value }}</div>
      </div>
    </div>
    <div class="card">
      <div class="font-bold mb-4">Campaigns Performance</div>
      <div v-if="!campaigns.length" class="text-sm text-gray-400 dark:text-gray-600 py-4">No campaigns yet.</div>
      <div v-else class="overflow-x-auto rounded-xl border border-border dark:border-border-dark">
        <table class="w-full text-sm">
          <thead><tr class="bg-surface-off dark:bg-surface-dark-off">
            <th class="th">Campaign</th><th class="th">Provider</th><th class="th">Status</th><th class="th">Sent On</th>
          </tr></thead>
          <tbody>
            <tr v-for="c in campaigns" :key="c.id" class="border-b border-border dark:border-border-dark last:border-0 hover:bg-surface-off dark:hover:bg-surface-dark-off">
              <td class="td font-semibold">{{ c.name }}</td>
              <td class="td text-xs font-semibold" :style="c.provider==='microsoft'?'color:#01696f':'color:#4285F4'">{{ c.provider === 'microsoft' ? 'Microsoft' : 'Google' }}</td>
              <td class="td"><span :class="['badge','badge-'+c.status]">{{ c.status }}</span></td>
              <td class="td text-xs text-gray-500 dark:text-gray-400">{{ c.sent_at ? new Date(c.sent_at).toLocaleDateString() : '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import { useToastStore } from '@/stores/toast'
const toast = useToastStore()
const loading = ref(true); const campaigns = ref([])
const stats = ref([{ label: 'Avg Open Rate', value: '—', color: '#01696f' },{ label: 'Avg Click Rate', value: '—', color: '#437a22' },{ label: 'Total Sent', value: '—', color: '#da7101' }])
onMounted(async () => {
  try {
    const [s, c] = await Promise.all([api.get('/analytics/dashboard'), api.get('/campaigns?limit=50')])
    stats.value = [{ label: 'Avg Open Rate', value: s.data.avg_open_rate+'%', color: '#01696f' },{ label: 'Avg Click Rate', value: s.data.avg_click_rate+'%', color: '#437a22' },{ label: 'Total Sent', value: s.data.total_emails_sent.toLocaleString(), color: '#da7101' }]
    campaigns.value = c.data
  } catch(e) { toast.show('Failed to load analytics', 'error') } finally { loading.value = false }
})
</script>
<style scoped>
.th { @apply text-left px-4 py-3 text-xs uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400; }
.td { @apply px-4 py-3 align-middle; }
</style>

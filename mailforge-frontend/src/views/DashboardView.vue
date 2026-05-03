<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div><div class="page-title">Dashboard</div><div class="page-subtitle">Your email marketing at a glance</div></div>
      <RouterLink to="/compose" class="btn btn-primary"><svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>New Campaign</RouterLink>
    </div>

    <div class="grid grid-cols-5 gap-4 mb-8">
      <div v-for="k in kpis" :key="k.label" class="card">
        <div class="text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 font-semibold mb-2">{{ k.label }}</div>
        <div v-if="loading" class="h-7 w-20 rounded bg-gray-200 dark:bg-gray-700 animate-pulse"></div>
        <div v-else class="font-display text-2xl font-bold" :style="k.color ? `color:${k.color}` : ''">{{ k.value }}</div>
      </div>
    </div>

    <div class="card">
      <div class="font-bold mb-4">Recent Campaigns</div>
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 3" :key="i" class="h-10 rounded bg-gray-100 dark:bg-gray-800 animate-pulse"></div>
      </div>
      <CampaignsTable v-else :campaigns="recent" :compact="true" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import { useToastStore } from '@/stores/toast'
import CampaignsTable from '@/components/CampaignsTable.vue'

const toast = useToastStore()
const loading = ref(true)
const kpis = ref([
  { label: 'Campaigns', value: '—' }, { label: 'Contacts', value: '—' },
  { label: 'Emails Sent', value: '—' },
  { label: 'Avg Open Rate', value: '—', color: '#01696f' },
  { label: 'Avg Click Rate', value: '—', color: '#437a22' },
])
const recent = ref([])

onMounted(async () => {
  try {
    const [stats, campaigns] = await Promise.all([api.get('/analytics/dashboard'), api.get('/campaigns?limit=5')])
    const s = stats.data
    kpis.value = [
      { label: 'Campaigns', value: s.total_campaigns },
      { label: 'Contacts', value: s.total_contacts.toLocaleString() },
      { label: 'Emails Sent', value: s.total_emails_sent.toLocaleString() },
      { label: 'Avg Open Rate', value: s.avg_open_rate + '%', color: '#01696f' },
      { label: 'Avg Click Rate', value: s.avg_click_rate + '%', color: '#437a22' },
    ]
    recent.value = campaigns.data
  } catch(e) { toast.show('Failed to load dashboard: ' + (e.response?.data?.detail || e.message), 'error') }
  finally { loading.value = false }
})
</script>

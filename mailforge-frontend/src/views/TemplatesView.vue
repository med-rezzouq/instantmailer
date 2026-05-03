<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div><div class="page-title">Templates</div><div class="page-subtitle">Reusable email templates</div></div>
      <button class="btn btn-primary" @click="modal=true"><svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>New Template</button>
    </div>
    <div v-if="!templates.length" class="flex flex-col items-center text-center py-20 text-gray-400 dark:text-gray-600">
      <svg class="w-12 h-12 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
      <h3 class="text-gray-700 dark:text-gray-300 font-semibold mb-2">No templates yet</h3>
      <p class="text-sm max-w-xs mb-6">Create reusable email templates to speed up your campaigns</p>
      <button class="btn btn-primary" @click="modal=true">Create Template</button>
    </div>
    <div v-else class="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-5">
      <div v-for="t in templates" :key="t.id" class="card">
        <div class="text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 font-semibold mb-2">{{ t.category || 'General' }}</div>
        <div class="font-bold mb-1">{{ t.name }}</div>
        <div class="text-xs text-gray-400 dark:text-gray-600 mb-4">{{ new Date(t.created_at).toLocaleDateString() }}</div>
        <div class="flex gap-2">
          <button class="btn btn-primary btn-sm" @click="useInCompose(t.id)">Use</button>
          <button class="btn btn-danger btn-sm" @click="deleteTemplate(t.id)">Delete</button>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="modal" class="fixed inset-0 bg-black/60 z-[200] flex items-center justify-center p-4" @click.self="modal=false">
        <div class="bg-surface dark:bg-surface-dark border border-border dark:border-border-dark rounded-2xl p-8 w-full max-w-2xl shadow-2xl">
          <div class="flex items-center justify-between mb-6"><h2 class="font-bold">New Template</h2><button @click="modal=false">✕</button></div>
          <div class="mb-4"><label class="form-label">Template Name</label><input v-model="form.name" class="form-input" placeholder="My Newsletter Template"></div>
          <div class="mb-4"><label class="form-label">Category</label>
            <select v-model="form.category" class="form-input"><option v-for="c in categories" :key="c">{{ c }}</option></select>
          </div>
          <div class="mb-6"><label class="form-label">HTML Content</label><textarea v-model="form.html_content" class="form-input font-mono text-xs" style="min-height:200px" placeholder="<h1>Hello {{first_name}}</h1>"></textarea></div>
          <div class="flex gap-3 justify-end">
            <button class="btn btn-ghost" @click="modal=false">Cancel</button>
            <button class="btn btn-primary" @click="saveTemplate">Save Template</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore(); const router = useRouter()
const templates = ref([]); const modal = ref(false)
const categories = ['Newsletter','Promotional','Welcome','Re-engagement','Event','Other']
const form = ref({ name: '', category: 'Newsletter', html_content: '' })

onMounted(load)
async function load() { try { templates.value = (await api.get('/templates?limit=100')).data } catch(e) { toast.show('Failed to load templates', 'error') } }
async function saveTemplate() {
  try { await api.post('/templates', form.value); modal.value = false; toast.show('Template saved!', 'success'); load() }
  catch(e) { toast.show(e.response?.data?.detail || e.message, 'error') }
}
async function deleteTemplate(id) {
  if (!confirm('Delete?')) return
  try { await api.delete(`/templates/${id}`); toast.show('Deleted', 'success'); load() } catch(e) { toast.show(e.message, 'error') }
}
async function useInCompose(id) {
  try { const t = (await api.get(`/templates/${id}`)).data; router.push({ path: '/compose', query: { template: t.html_content } }) }
  catch(e) { toast.show('Error', 'error') }
}
</script>

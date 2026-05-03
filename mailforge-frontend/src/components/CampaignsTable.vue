<template>
  <div v-if="!campaigns.length" class="text-sm text-gray-500 dark:text-gray-400 py-4">No campaigns yet.</div>
  <div v-else class="overflow-x-auto rounded-xl border border-border dark:border-border-dark">
    <table class="w-full text-sm">
      <thead><tr class="bg-surface-off dark:bg-surface-dark-off">
        <th class="th">Name</th>
        <th v-if="!compact" class="th">Subject</th>
        <th class="th">Provider</th>
        <th class="th">Status</th>
        <th class="th">Sent</th>
        <th v-if="!compact" class="th">Actions</th>
      </tr></thead>
      <tbody>
        <tr v-for="c in campaigns" :key="c.id" class="hover:bg-surface-off dark:hover:bg-surface-dark-off border-b border-border dark:border-border-dark last:border-0">
          <td class="td font-semibold">{{ c.name }}</td>
          <td v-if="!compact" class="td text-gray-500 dark:text-gray-400">{{ c.subject }}</td>
          <td class="td"><span v-html="providerBadge(c.provider)"></span></td>
          <td class="td"><span :class="['badge', 'badge-' + c.status]">{{ c.status }}</span></td>
          <td class="td text-xs text-gray-500 dark:text-gray-400">{{ c.sent_at ? new Date(c.sent_at).toLocaleDateString() : '—' }}</td>
          <td v-if="!compact" class="td">
            <div class="flex gap-2">
              <button v-if="c.status==='draft'||c.status==='scheduled'" class="btn btn-primary btn-sm" @click="$emit('send', c.id)">Send</button>
              <button class="btn btn-ghost btn-sm" @click="$emit('stats', c)">Stats</button>
              <button class="btn btn-danger btn-sm" @click="$emit('delete', c.id)">Delete</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({ campaigns: Array, compact: Boolean })
defineEmits(['send', 'stats', 'delete'])
function providerBadge(p) {
  if (p==='microsoft') return '<span style="color:#01696f;font-size:12px;font-weight:600">Microsoft</span>'
  return '<span style="color:#4285F4;font-size:12px;font-weight:600">Google</span>'
}
</script>
<style scoped>
.th { @apply text-left px-4 py-3 text-xs uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400; }
.td { @apply px-4 py-3 align-middle; }
</style>

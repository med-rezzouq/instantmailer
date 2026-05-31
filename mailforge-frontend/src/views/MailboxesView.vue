<template>
  <div>
    <div class="page-title">Mailbox Connections</div>
    <div class="page-subtitle">
      Connect your Gmail / Office 365 accounts for warmup and reply detection
    </div>

    <div class="mt-4 flex gap-2">
      <button class="btn btn-primary" @click="connectGoogle">
        Connect Gmail
      </button>
      <button class="btn btn-secondary" @click="connectMicrosoft">
        Connect Office 365
      </button>
    </div>

    <div class="card mt-6">
      <div class="text-sm text-gray-500 mb-2">
        Connected mailboxes ({{ mailboxes.length }})
      </div>
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-surface-off">
            <th class="th">Provider</th>
            <th class="th">Email</th>
            <th class="th">Warmup</th>
            <th class="th">Last Sync</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!mailboxes.length">
            <td colspan="4" class="text-center py-6 text-gray-400">
              No mailboxes connected yet.
            </td>
          </tr>
          <tr v-for="m in mailboxes" :key="m.id" class="border-b">
            <td class="td">{{ m.provider }}</td>
            <td class="td">{{ m.email }}</td>
            <td class="td">
              <span v-if="m.warmup_enabled" class="badge badge-sent">On</span>
              <span v-else class="badge badge-muted">Off</span>
            </td>
            <td class="td">{{ formatDate(m.last_sync_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "@/api";
import { useToastStore } from "@/stores/toast";

const toast = useToastStore();
const mailboxes = ref([]);

onMounted(load);

async function load() {
  try {
    const res = await api.get("/mailboxes");
    mailboxes.value = res.data || [];
  } catch (e) {
    console.error(e);
    toast.show("Failed to load mailboxes", "error");
  }
}

async function connectGoogle() {
  try {
    const res = await api.get("/mailboxes/connect/google");
    window.location.href = res.data.auth_url;
  } catch (e) {
    console.error(e);
    toast.show("Failed to start Google OAuth", "error");
  }
}

async function connectMicrosoft() {
  try {
    const res = await api.get("/mailboxes/connect/microsoft");
    window.location.href = res.data.auth_url;
  } catch (e) {
    console.error(e);
    toast.show("Failed to start Microsoft OAuth", "error");
  }
}

function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}
</script>

<template>
  <div>
    <!-- HEADER -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <div class="page-title">Mailbox Connections</div>
        <div class="page-subtitle">
          {{ mailboxes.length }} connected mailboxes
        </div>
      </div>

      <div class="flex gap-3">
        <button class="btn btn-primary" @click="connectGoogle">
          Connect Gmail
        </button>
        <button class="btn btn-secondary" @click="connectMicrosoft">
          Connect Office 365
        </button>
      </div>
    </div>

    <!-- ERROR -->
    <div v-if="error" class="mb-4 text-red-600">
      {{ error }}
    </div>

    <!-- TABLE -->
    <div
      class="overflow-x-auto rounded-xl border border-border dark:border-border-dark"
    >
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-surface-off dark:bg-surface-dark-off">
            <th class="th">ID</th>
            <th class="th">Provider</th>
            <th class="th">Email</th>
            <th class="th">Display Name</th>
            <th class="th">Warmup</th>
            <th class="th">Last Sync</th>
            <th class="th">Linked OAuth App</th>
            <th class="th">Actions</th>
          </tr>
        </thead>

        <tbody>
          <tr v-if="loading">
            <td
              colspan="7"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              Loading...
            </td>
          </tr>

          <tr v-else-if="!mailboxes.length">
            <td
              colspan="7"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              No mailboxes connected yet.
            </td>
          </tr>

          <tr
            v-else
            v-for="m in mailboxes"
            :key="m.id"
            class="hover:bg-surface-off dark:hover:bg-surface-dark-off border-b border-border dark:border-border-dark last:border-0"
          >
            <td class="td text-gray-500 dark:text-gray-400 font-mono">
              {{ m.id }}
            </td>

            <td class="td">
              <span
                :class="[
                  'badge',
                  m.provider === 'google' ? 'badge-sent' : 'badge-muted',
                ]"
              >
                {{ providerLabel(m.provider) }}
              </span>
            </td>

            <td class="td">
              <div class="font-semibold">{{ m.email }}</div>
            </td>

            <td class="td text-gray-500 dark:text-gray-400">
              {{ m.display_name || "—" }}
            </td>

            <td class="td">
              <span
                :class="[
                  'badge',
                  m.warmup_enabled ? 'badge-sent' : 'badge-failed',
                ]"
              >
                {{ m.warmup_enabled ? "On" : "Off" }}
              </span>
            </td>

            <td class="td text-gray-500 dark:text-gray-400">
              {{ formatDate(m.last_sync_at) }}
            </td>

            <td class="td text-gray-500 dark:text-gray-400">
              {{ m.oauth_app_name || "—" }}
            </td>

            <td class="td">
              <div class="flex gap-2">
                <button
                  class="btn btn-danger btn-sm"
                  @click="deleteMailbox(m)"
                  :disabled="deletingId === m.id"
                >
                  {{ deletingId === m.id ? "Deleting..." : "Delete" }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import api from "@/api";
import { useToastStore } from "@/stores/toast";

const toast = useToastStore();

interface Mailbox {
  id: number;
  provider: string;
  email: string;
  display_name: string | null;
  warmup_enabled: boolean;
  last_sync_at: string | null;
  oauth_app_name: string | null;
}

const mailboxes = ref<Mailbox[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const deletingId = ref<number | null>(null);

onMounted(() => {
  load();
});

async function load() {
  loading.value = true;
  error.value = null;

  try {
    const res = await api.get("/mailboxes");
    mailboxes.value = res.data || [];
  } catch (e: any) {
    console.error(e);
    const message = e?.response?.data?.detail || "Failed to load mailboxes";
    error.value = message;
    toast.show(message, "error");
  } finally {
    loading.value = false;
  }
}

async function connectGoogle() {
  try {
    const res = await api.get("/mailboxes/connect/google");
    window.location.href = res.data.auth_url;
  } catch (e: any) {
    console.error(e);
    const message = e?.response?.data?.detail || "Failed to start Google OAuth";
    toast.show(message, "error");
  }
}

async function connectMicrosoft() {
  try {
    const res = await api.get("/mailboxes/connect/microsoft");
    window.location.href = res.data.auth_url;
  } catch (e: any) {
    console.error(e);
    const message =
      e?.response?.data?.detail || "Failed to start Microsoft OAuth";
    toast.show(message, "error");
  }
}

async function deleteMailbox(mailbox: Mailbox) {
  if (!confirm(`Delete mailbox "${mailbox.email}"?`)) return;

  deletingId.value = mailbox.id;

  try {
    await api.delete(`/mailboxes/${mailbox.id}`);
    mailboxes.value = mailboxes.value.filter((m) => m.id !== mailbox.id);
    toast.show("Mailbox deleted successfully", "success");
  } catch (e: any) {
    console.error(e);
    const message = e?.response?.data?.detail || "Failed to delete mailbox";
    error.value = message;
    toast.show(message, "error");
  } finally {
    deletingId.value = null;
  }
}

function providerLabel(provider: string) {
  if (provider === "google") return "Gmail";
  if (provider === "microsoft") return "Office 365";
  return provider;
}

function formatDate(value: string | null) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}
</script>

<style scoped>
.th {
  @apply text-left px-4 py-3 text-xs uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400;
}

.td {
  @apply px-4 py-3 align-middle;
}
</style>

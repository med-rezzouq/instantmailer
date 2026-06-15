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
        <button class="btn btn-primary" @click="openGoogleTaskModal">
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
              colspan="8"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              Loading...
            </td>
          </tr>

          <tr v-else-if="!mailboxes.length">
            <td
              colspan="8"
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

    <!-- GOOGLE CONNECT MODAL -->
    <Teleport to="body">
      <div
        v-if="googleTaskModalOpen"
        class="modal-overlay"
        @click.self="closeGoogleTaskModal"
      >
        <div class="modal max-w-lg">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-bold">Connect Gmail</h2>
            <button
              @click="closeGoogleTaskModal"
              class="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div class="mb-4">
            <label class="form-label">Select warmup task *</label>
            <select v-model="selectedTaskId" class="form-input">
              <option :value="null" disabled>Select task</option>
              <option
                v-for="task in googleEligibleTasks"
                :key="task.id"
                :value="task.id"
              >
                {{ task.name
                }}{{ task.oauth_app_name ? ` — ${task.oauth_app_name}` : "" }}
              </option>
            </select>
            <p class="text-xs text-gray-500 mt-1">
              The selected task decides which OAuth app will be used for Gmail
              connection.
            </p>
          </div>

          <div v-if="taskLoadError" class="mb-4 text-red-600 text-sm">
            {{ taskLoadError }}
          </div>

          <div
            v-if="
              googleTaskModalOpen && !googleEligibleTasks.length && !taskLoading
            "
            class="mb-4 text-sm text-gray-500"
          >
            No Google-compatible warmup tasks found. Create a warmup task with a
            Google OAuth app first.
          </div>

          <div class="flex gap-3 justify-end">
            <button class="btn btn-ghost" @click="closeGoogleTaskModal">
              Cancel
            </button>
            <button
              class="btn btn-primary"
              @click="connectGoogle"
              :disabled="
                !selectedTaskId ||
                connectingGoogle ||
                !googleEligibleTasks.length
              "
            >
              {{ connectingGoogle ? "Redirecting..." : "Continue with Google" }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
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
  oauth_app_id?: number | null;
  oauth_app_name: string | null;
}

interface WarmupTaskOption {
  id: number;
  name: string;
  oauth_app_id: number | null;
  oauth_app_name?: string | null;
}

const mailboxes = ref<Mailbox[]>([]);
const warmupTasks = ref<WarmupTaskOption[]>([]);
const loading = ref(false);
const taskLoading = ref(false);
const error = ref<string | null>(null);
const taskLoadError = ref<string | null>(null);
const deletingId = ref<number | null>(null);
const connectingGoogle = ref(false);

const googleTaskModalOpen = ref(false);
const selectedTaskId = ref<number | null>(null);

const googleEligibleTasks = computed(() =>
  warmupTasks.value.filter((task) => !!task.oauth_app_id),
);

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

async function loadWarmupTasks() {
  taskLoading.value = true;
  taskLoadError.value = null;

  try {
    const res = await api.get("/warmup-tasks");
    warmupTasks.value = (res.data || []).map((task: any) => ({
      id: task.id,
      name: task.name,
      oauth_app_id: task.oauth_app_id,
      oauth_app_name:
        task.oauth_app_name ??
        (task.oauth_app_id ? `OAuth App #${task.oauth_app_id}` : null),
    }));
  } catch (e: any) {
    console.error(e);
    warmupTasks.value = [];
    const message = e?.response?.data?.detail || "Failed to load warmup tasks";
    taskLoadError.value = message;
    toast.show(message, "error");
  } finally {
    taskLoading.value = false;
  }
}

async function openGoogleTaskModal() {
  selectedTaskId.value = null;
  googleTaskModalOpen.value = true;
  await loadWarmupTasks();
}

function closeGoogleTaskModal() {
  googleTaskModalOpen.value = false;
  selectedTaskId.value = null;
  taskLoadError.value = null;
}

async function connectGoogle() {
  if (!selectedTaskId.value) {
    toast.show("Please select a warmup task first", "error");
    return;
  }

  connectingGoogle.value = true;

  try {
    const res = await api.get("/mailboxes/connect/google", {
      params: { task_id: selectedTaskId.value },
    });
    window.location.href = res.data.auth_url;
  } catch (e: any) {
    console.error(e);
    const message = e?.response?.data?.detail || "Failed to start Google OAuth";
    toast.show(message, "error");
  } finally {
    connectingGoogle.value = false;
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

.modal-overlay {
  @apply fixed inset-0 bg-black/60 z-[200] flex items-center justify-center p-4;
}

.modal {
  @apply bg-surface dark:bg-surface-dark border border-border dark:border-border-dark rounded-2xl p-8 w-full shadow-2xl;
}
</style>

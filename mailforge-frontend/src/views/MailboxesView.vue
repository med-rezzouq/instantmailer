<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <div class="page-title">Mailbox Connections</div>
        <div class="page-subtitle">
          {{ mailboxes.length }} connected mailboxes
        </div>
      </div>

      <div class="flex gap-3">
        <button class="btn btn-primary" @click="openConnectModal">
          Connect Mailbox
        </button>
      </div>
    </div>

    <div v-if="error" class="mb-4 text-red-600">
      {{ error }}
    </div>

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
            <th class="th">Access Protocol</th>
            <th class="th">Warmup</th>
            <th class="th">Status</th>
            <th class="th">Last Sync</th>
            <th class="th">Linked OAuth App</th>
            <th class="th">Actions</th>
          </tr>
        </thead>

        <tbody>
          <tr v-if="loading">
            <td
              colspan="10"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              Loading...
            </td>
          </tr>

          <tr v-else-if="!mailboxes.length">
            <td
              colspan="10"
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
              <span :class="['badge', providerBadgeClass(m.provider)]">
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
                  m.access_protocol === 'oauth2' ? 'badge-sent' : 'badge-muted',
                ]"
              >
                {{ protocolLabel(m.access_protocol) }}
              </span>
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

            <td class="td">
              <span
                :class="['badge', m.is_active ? 'badge-sent' : 'badge-failed']"
              >
                {{ m.is_active ? "Active" : "Inactive" }}
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

    <Teleport to="body">
      <div
        v-if="connectModalOpen"
        class="modal-overlay"
        @click.self="closeConnectModal"
      >
        <div class="modal max-w-2xl">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-bold text-lg">Connect Mailbox</h2>
            <button
              @click="closeConnectModal"
              class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              ✕
            </button>
          </div>

          <div v-if="connectStep === 'choose-method'">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button class="choice-card" @click="selectMethod('oauth2')">
                <div class="font-semibold mb-1">OAuth2</div>
                <div class="text-sm text-gray-500 dark:text-gray-400">
                  Connect with provider authorization flow.
                </div>
              </button>

              <button class="choice-card" @click="selectMethod('imap')">
                <div class="font-semibold mb-1">IMAP / SMTP</div>
                <div class="text-sm text-gray-500 dark:text-gray-400">
                  Add mailbox manually with IMAP and SMTP settings.
                </div>
              </button>
            </div>
          </div>

          <div v-else-if="connectStep === 'choose-oauth-provider'">
            <div class="mb-4 text-sm text-gray-500 dark:text-gray-400">
              Select OAuth2 provider.
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button class="choice-card" @click="openGoogleTaskStep">
                <div class="font-semibold mb-1">Google</div>
                <div class="text-sm text-gray-500 dark:text-gray-400">
                  Gmail OAuth flow.
                </div>
              </button>

              <button class="choice-card" @click="openMicrosoftTaskStep">
                <div class="font-semibold mb-1">Microsoft</div>
                <div class="text-sm text-gray-500 dark:text-gray-400">
                  Office 365 / Outlook OAuth.
                </div>
              </button>

              <button class="choice-card" @click="openYahooTaskStep">
                <div class="font-semibold mb-1">Yahoo</div>
                <div class="text-sm text-gray-500 dark:text-gray-400">
                  Yahoo OAuth flow.
                </div>
              </button>
            </div>

            <div class="flex justify-end mt-6">
              <button
                class="btn btn-ghost"
                @click="connectStep = 'choose-method'"
              >
                Back
              </button>
            </div>
          </div>

          <div v-else-if="connectStep === 'google-task'">
            <div class="mb-4">
              <label class="form-label">Select warmup task *</label>
              <select v-model="selectedGoogleTaskId" class="form-input">
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
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                The selected task decides which OAuth app will be used for Gmail
                connection.
              </p>
            </div>

            <div
              v-if="taskLoading"
              class="mb-4 text-sm text-gray-500 dark:text-gray-400"
            >
              Loading tasks...
            </div>

            <div v-if="taskLoadError" class="mb-4 text-red-600 text-sm">
              {{ taskLoadError }}
            </div>

            <div
              v-if="!googleEligibleTasks.length && !taskLoading"
              class="mb-4 text-sm text-gray-500 dark:text-gray-400"
            >
              No Google-compatible warmup tasks found. Create a warmup task with
              a Google OAuth app first.
            </div>

            <div class="flex gap-3 justify-end">
              <button
                class="btn btn-ghost"
                @click="connectStep = 'choose-oauth-provider'"
              >
                Back
              </button>
              <button
                class="btn btn-primary"
                @click="connectGoogle"
                :disabled="
                  !selectedGoogleTaskId ||
                  connectingGoogle ||
                  !googleEligibleTasks.length
                "
              >
                {{
                  connectingGoogle ? "Redirecting..." : "Continue with Google"
                }}
              </button>
            </div>
          </div>

          <div v-else-if="connectStep === 'microsoft-task'">
            <div class="mb-4">
              <label class="form-label">Select warmup task *</label>
              <select v-model="selectedMicrosoftTaskId" class="form-input">
                <option :value="null" disabled>Select task</option>
                <option
                  v-for="task in microsoftEligibleTasks"
                  :key="task.id"
                  :value="task.id"
                >
                  {{ task.name
                  }}{{ task.oauth_app_name ? ` — ${task.oauth_app_name}` : "" }}
                </option>
              </select>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                The selected task decides which OAuth app will be used for
                Microsoft connection.
              </p>
            </div>

            <div
              v-if="taskLoading"
              class="mb-4 text-sm text-gray-500 dark:text-gray-400"
            >
              Loading tasks...
            </div>

            <div v-if="taskLoadError" class="mb-4 text-red-600 text-sm">
              {{ taskLoadError }}
            </div>

            <div
              v-if="!microsoftEligibleTasks.length && !taskLoading"
              class="mb-4 text-sm text-gray-500 dark:text-gray-400"
            >
              No Microsoft-compatible warmup tasks found. Create a warmup task
              with a Microsoft OAuth app first.
            </div>

            <div class="flex gap-3 justify-end">
              <button
                class="btn btn-ghost"
                @click="connectStep = 'choose-oauth-provider'"
              >
                Back
              </button>
              <button
                class="btn btn-primary"
                @click="connectMicrosoft"
                :disabled="
                  !selectedMicrosoftTaskId ||
                  connectingMicrosoft ||
                  !microsoftEligibleTasks.length
                "
              >
                {{
                  connectingMicrosoft
                    ? "Redirecting..."
                    : "Continue with Microsoft"
                }}
              </button>
            </div>
          </div>

          <div v-else-if="connectStep === 'yahoo-task'">
            <div class="mb-4">
              <label class="form-label">Select warmup task *</label>
              <select v-model="selectedYahooTaskId" class="form-input">
                <option :value="null" disabled>Select task</option>
                <option
                  v-for="task in yahooEligibleTasks"
                  :key="task.id"
                  :value="task.id"
                >
                  {{ task.name
                  }}{{ task.oauth_app_name ? ` — ${task.oauth_app_name}` : "" }}
                </option>
              </select>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                The selected task decides which OAuth app will be used for Yahoo
                connection.
              </p>
            </div>

            <div
              v-if="taskLoading"
              class="mb-4 text-sm text-gray-500 dark:text-gray-400"
            >
              Loading tasks...
            </div>

            <div v-if="taskLoadError" class="mb-4 text-red-600 text-sm">
              {{ taskLoadError }}
            </div>

            <div
              v-if="!yahooEligibleTasks.length && !taskLoading"
              class="mb-4 text-sm text-gray-500 dark:text-gray-400"
            >
              No Yahoo-compatible warmup tasks found. Create a warmup task with
              a Yahoo OAuth app first.
            </div>

            <div class="flex gap-3 justify-end">
              <button
                class="btn btn-ghost"
                @click="connectStep = 'choose-oauth-provider'"
              >
                Back
              </button>
              <button
                class="btn btn-primary"
                @click="connectYahoo"
                :disabled="
                  !selectedYahooTaskId ||
                  connectingYahoo ||
                  !yahooEligibleTasks.length
                "
              >
                {{ connectingYahoo ? "Redirecting..." : "Continue with Yahoo" }}
              </button>
            </div>
          </div>

          <div v-else-if="connectStep === 'imap-form'">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label class="form-label">Email *</label>
                <input
                  v-model="imapForm.email"
                  type="email"
                  class="form-input"
                  placeholder="user@example.com"
                />
              </div>

              <div>
                <label class="form-label">Display Name</label>
                <input
                  v-model="imapForm.display_name"
                  class="form-input"
                  placeholder="My mailbox"
                />
              </div>

              <div>
                <label class="form-label">IMAP Host *</label>
                <input
                  v-model="imapForm.imap_host"
                  class="form-input"
                  placeholder="imap.gmail.com"
                />
              </div>

              <div>
                <label class="form-label">IMAP Port *</label>
                <input
                  v-model.number="imapForm.imap_port"
                  type="number"
                  class="form-input"
                />
              </div>

              <div>
                <label class="form-label">SMTP Host *</label>
                <input
                  v-model="imapForm.smtp_host"
                  class="form-input"
                  placeholder="smtp.gmail.com"
                />
              </div>

              <div>
                <label class="form-label">SMTP Port *</label>
                <input
                  v-model.number="imapForm.smtp_port"
                  type="number"
                  class="form-input"
                />
              </div>

              <div>
                <label class="form-label">Username *</label>
                <input
                  v-model="imapForm.username"
                  class="form-input"
                  placeholder="usually same as email"
                />
              </div>

              <div>
                <label class="form-label">Password / App Password *</label>
                <input
                  v-model="imapForm.password"
                  type="password"
                  class="form-input"
                />
              </div>
            </div>

            <div class="flex flex-wrap gap-4 mb-6 text-sm">
              <label class="inline-flex items-center">
                <input
                  v-model="imapForm.imap_ssl"
                  type="checkbox"
                  class="mr-2"
                />
                IMAP SSL
              </label>

              <label class="inline-flex items-center">
                <input
                  v-model="imapForm.smtp_tls"
                  type="checkbox"
                  class="mr-2"
                />
                SMTP TLS
              </label>

              <label class="inline-flex items-center">
                <input
                  v-model="imapForm.warmup_enabled"
                  type="checkbox"
                  class="mr-2"
                />
                Enable warmup
              </label>

              <label class="inline-flex items-center">
                <input
                  v-model="imapForm.is_active"
                  type="checkbox"
                  class="mr-2"
                />
                Active
              </label>
            </div>

            <div class="flex gap-3 justify-end">
              <button
                class="btn btn-ghost"
                @click="connectStep = 'choose-method'"
              >
                Back
              </button>
              <button
                class="btn btn-primary"
                @click="createImapMailbox"
                :disabled="creatingImap"
              >
                {{ creatingImap ? "Adding..." : "Add Mailbox" }}
              </button>
            </div>
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
  user_id: number;
  provider: string;
  access_protocol: string;
  email: string;
  display_name: string | null;
  warmup_enabled: boolean;
  is_active: boolean;
  last_sync_at: string | null;
  created_at?: string;
  updated_at?: string;
  oauth_app_id?: number | null;
  oauth_app_name: string | null;
  imap_host?: string | null;
  imap_port?: number | null;
  imap_ssl?: boolean | null;
  smtp_host?: string | null;
  smtp_port?: number | null;
  smtp_tls?: boolean | null;
  username?: string | null;
}

interface WarmupTaskOption {
  id: number;
  name: string;
  oauth_app_id: number | null;
  oauth_app_name?: string | null;
  oauth_app_provider?: string | null;
}

type ConnectStep =
  | "choose-method"
  | "choose-oauth-provider"
  | "google-task"
  | "microsoft-task"
  | "yahoo-task"
  | "imap-form";

const mailboxes = ref<Mailbox[]>([]);
const warmupTasks = ref<WarmupTaskOption[]>([]);
const loading = ref(false);
const taskLoading = ref(false);
const error = ref<string | null>(null);
const taskLoadError = ref<string | null>(null);
const deletingId = ref<number | null>(null);

const connectingGoogle = ref(false);
const connectingMicrosoft = ref(false);
const connectingYahoo = ref(false);
const creatingImap = ref(false);

const connectModalOpen = ref(false);
const connectStep = ref<ConnectStep>("choose-method");

const selectedGoogleTaskId = ref<number | null>(null);
const selectedMicrosoftTaskId = ref<number | null>(null);
const selectedYahooTaskId = ref<number | null>(null);

const imapForm = ref({
  email: "",
  display_name: "",
  imap_host: "imap.gmail.com",
  imap_port: 993,
  imap_ssl: true,
  smtp_host: "smtp.gmail.com",
  smtp_port: 587,
  smtp_tls: true,
  username: "",
  password: "",
  warmup_enabled: false,
  is_active: true,
});

const googleEligibleTasks = computed(() =>
  warmupTasks.value.filter(
    (task) => !!task.oauth_app_id && task.oauth_app_provider === "google",
  ),
);

const microsoftEligibleTasks = computed(() =>
  warmupTasks.value.filter(
    (task) => !!task.oauth_app_id && task.oauth_app_provider === "microsoft",
  ),
);

const yahooEligibleTasks = computed(() =>
  warmupTasks.value.filter(
    (task) => !!task.oauth_app_id && task.oauth_app_provider === "yahoo",
  ),
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
    const message = e?.response?.data?.detail || "Failed to load mailboxes";
    error.value = message;
    toast.show(message, "error");
  } finally {
    loading.value = false;
  }
}

function resetImapForm() {
  imapForm.value = {
    email: "",
    display_name: "",
    imap_host: "imap.gmail.com",
    imap_port: 993,
    imap_ssl: true,
    smtp_host: "smtp.gmail.com",
    smtp_port: 587,
    smtp_tls: true,
    username: "",
    password: "",
    warmup_enabled: false,
    is_active: true,
  };
}

function resetTaskSelections() {
  selectedGoogleTaskId.value = null;
  selectedMicrosoftTaskId.value = null;
  selectedYahooTaskId.value = null;
}

function openConnectModal() {
  connectModalOpen.value = true;
  connectStep.value = "choose-method";
  error.value = null;
  taskLoadError.value = null;
  resetTaskSelections();
  resetImapForm();
}

function closeConnectModal() {
  connectModalOpen.value = false;
  connectStep.value = "choose-method";
  taskLoadError.value = null;
  resetTaskSelections();
}

function selectMethod(method: "oauth2" | "imap") {
  if (method === "oauth2") {
    connectStep.value = "choose-oauth-provider";
    return;
  }
  connectStep.value = "imap-form";
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
      oauth_app_provider:
        task.oauth_app_provider ?? task.oauth_provider ?? task.provider ?? null,
    }));
  } catch (e: any) {
    warmupTasks.value = [];
    const message = e?.response?.data?.detail || "Failed to load warmup tasks";
    taskLoadError.value = message;
    toast.show(message, "error");
  } finally {
    taskLoading.value = false;
  }
}

async function openGoogleTaskStep() {
  selectedGoogleTaskId.value = null;
  connectStep.value = "google-task";
  await loadWarmupTasks();
}

async function openMicrosoftTaskStep() {
  selectedMicrosoftTaskId.value = null;
  connectStep.value = "microsoft-task";
  await loadWarmupTasks();
}

async function openYahooTaskStep() {
  selectedYahooTaskId.value = null;
  connectStep.value = "yahoo-task";
  await loadWarmupTasks();
}

async function connectGoogle() {
  if (!selectedGoogleTaskId.value) {
    toast.show("Please select a Google warmup task first", "error");
    return;
  }

  connectingGoogle.value = true;
  try {
    const res = await api.get("/mailboxes/connect/google", {
      params: { task_id: selectedGoogleTaskId.value },
    });
    window.location.href = res.data.auth_url;
  } catch (e: any) {
    const message = e?.response?.data?.detail || "Failed to start Google OAuth";
    toast.show(message, "error");
  } finally {
    connectingGoogle.value = false;
  }
}

async function connectMicrosoft() {
  if (!selectedMicrosoftTaskId.value) {
    toast.show("Please select a Microsoft warmup task first", "error");
    return;
  }

  connectingMicrosoft.value = true;
  try {
    const res = await api.get("/mailboxes/connect/microsoft", {
      params: { task_id: selectedMicrosoftTaskId.value },
    });
    window.location.href = res.data.auth_url;
  } catch (e: any) {
    const message =
      e?.response?.data?.detail || "Failed to start Microsoft OAuth";
    toast.show(message, "error");
  } finally {
    connectingMicrosoft.value = false;
  }
}

async function connectYahoo() {
  if (!selectedYahooTaskId.value) {
    toast.show("Please select a Yahoo warmup task first", "error");
    return;
  }

  connectingYahoo.value = true;
  try {
    const res = await api.get("/mailboxes/connect/yahoo", {
      params: { task_id: selectedYahooTaskId.value },
    });
    window.location.href = res.data.auth_url;
  } catch (e: any) {
    const message = e?.response?.data?.detail || "Failed to start Yahoo OAuth";
    toast.show(message, "error");
  } finally {
    connectingYahoo.value = false;
  }
}

async function createImapMailbox() {
  if (
    !imapForm.value.email ||
    !imapForm.value.imap_host ||
    !imapForm.value.imap_port ||
    !imapForm.value.smtp_host ||
    !imapForm.value.smtp_port ||
    !imapForm.value.username ||
    !imapForm.value.password
  ) {
    toast.show(
      "Email, IMAP host, IMAP port, SMTP host, SMTP port, username and password are required",
      "error",
    );
    return;
  }

  creatingImap.value = true;
  try {
    const res = await api.post("/mailboxes/connect/imap", imapForm.value);
    mailboxes.value.unshift(res.data);
    toast.show("IMAP mailbox added!", "success");
    closeConnectModal();
    resetImapForm();
  } catch (e: any) {
    const msg = e?.response?.data?.detail || "Failed to create IMAP mailbox";
    error.value = msg;
    toast.show(msg, "error");
  } finally {
    creatingImap.value = false;
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
  if (provider === "yahoo") return "Yahoo";
  if (provider === "custom") return "Custom IMAP";
  return provider;
}

function protocolLabel(protocol: string) {
  if (protocol === "oauth2") return "OAuth2";
  if (protocol === "imap") return "IMAP";
  return protocol || "—";
}

function providerBadgeClass(provider: string) {
  if (provider === "google") return "badge-sent";
  if (provider === "microsoft") return "badge-muted";
  if (provider === "yahoo") return "badge-muted";
  if (provider === "custom") return "badge-muted";
  return "badge-muted";
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
  @apply bg-surface dark:bg-surface-dark border border-border dark:border-border-dark rounded-2xl p-8 w-full shadow-2xl max-h-[90vh] overflow-y-auto;
}

.choice-card {
  @apply rounded-xl border border-border dark:border-border-dark p-5 text-left hover:bg-surface-off dark:hover:bg-surface-dark-off transition;
}
</style>

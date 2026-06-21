<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <div class="page-title">Warmup Tasks</div>
        <div class="page-subtitle">{{ tasks.length }} tasks</div>
      </div>
      <div class="flex gap-3">
        <button class="btn btn-primary" @click="openCreateTypeModal">
          <svg
            class="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Add Warmup Task
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
            <th class="th">Name</th>
            <th class="th">Protocol</th>
            <th class="th">OAuth App</th>
            <th class="th">Mailboxes</th>
            <th class="th">Sender filter</th>
            <th class="th">Actions Enabled</th>
            <th class="th">Delay</th>
            <th class="th">Status</th>
            <th class="th">Run logs</th>
            <th class="th">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td
              colspan="11"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              Loading...
            </td>
          </tr>

          <tr v-else-if="!tasks.length">
            <td
              colspan="11"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              No warmup tasks yet. Add your first one above.
            </td>
          </tr>

          <tr
            v-else
            v-for="t in tasks"
            :key="t.id"
            class="hover:bg-surface-off dark:hover:bg-surface-dark-off border-b border-border dark:border-border-dark last:border-0"
          >
            <td class="td text-gray-500 dark:text-gray-400">
              {{ t.id }}
            </td>

            <td class="td">
              <div class="font-semibold">{{ t.name }}</div>
            </td>

            <td class="td">
              <span
                class="badge"
                :class="t.protocol === 'oauth' ? 'badge-sent' : 'badge-failed'"
              >
                {{ t.protocol === "oauth" ? "OAuth2" : "IMAP" }}
              </span>
            </td>

            <td class="td">
              <div class="text-sm">
                {{
                  t.protocol === "oauth" ? oauthAppLabel(t.oauth_app_id) : "—"
                }}
              </div>
            </td>

            <td class="td">
              <div class="text-sm">
                <span
                  v-if="!t.mailbox_ids.length"
                  class="text-gray-400 dark:text-gray-600"
                >
                  No mailboxes
                </span>
                <div v-else class="flex flex-col gap-0.5">
                  <span v-for="id in t.mailbox_ids" :key="id" class="truncate">
                    • {{ mailboxLabel(id, t) }}
                  </span>
                </div>
              </div>
            </td>

            <td class="td">
              <div class="text-xs text-gray-500">
                <span v-if="t.allowed_sender">
                  From: <span class="font-mono">{{ t.allowed_sender }}</span>
                </span>
                <span v-else class="text-gray-400">Any sender</span>
              </div>
            </td>

            <td class="td text-xs">
              <div class="flex flex-wrap gap-1">
                <span v-if="t.do_move_to_inbox" class="badge badge-sent">
                  Move to inbox
                </span>
                <span v-if="t.do_open" class="badge badge-sent">Open</span>
                <span v-if="t.do_add_to_favorites" class="badge badge-sent">
                  Favourites
                </span>
                <span v-if="t.do_mark_as_primary" class="badge badge-sent">
                  Mark as important
                </span>
                <span v-if="t.do_reply" class="badge badge-sent">Reply</span>
                <span v-if="t.do_campaign_reply" class="badge badge-sent">
                  Campaign reply
                </span>
                <span v-if="t.do_detect_reply_event" class="badge badge-sent">
                  Detect reply
                </span>
              </div>
            </td>

            <td class="td tabular-nums">
              {{ t.delay_seconds }} {{ t.delay_unit }}
            </td>

            <td class="td">
              <span
                :class="['badge', t.is_active ? 'badge-sent' : 'badge-failed']"
              >
                {{ t.is_active ? "Active" : "Paused" }}
              </span>
            </td>

            <td class="td">
              <RouterLink
                :to="`/warmup/taskrun/${t.id}`"
                class="inline-flex items-center rounded-md border border-border px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-surface-off dark:border-border-dark dark:text-gray-200 dark:hover:bg-surface-dark-off"
              >
                View run logs
              </RouterLink>
            </td>

            <td class="td">
              <div class="flex gap-2">
                <button class="btn btn-ghost btn-sm" @click="openEditModal(t)">
                  Edit
                </button>
                <button class="btn btn-danger btn-sm" @click="deleteTask(t)">
                  Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Teleport to="body">
      <div
        v-if="createTypeModalOpen"
        class="modal-overlay"
        @click.self="closeCreateTypeModal"
      >
        <div class="modal max-w-lg">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-bold">Choose Task Type</h2>
            <button
              @click="closeCreateTypeModal"
              class="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button class="protocol-card" @click="startCreateTask('oauth')">
              <div class="text-lg font-semibold mb-1">OAuth2 Task</div>
              <div class="text-sm text-gray-500">
                For Gmail / Microsoft / Yahoo OAuth mailboxes with API-based
                actions.
              </div>
            </button>

            <button class="protocol-card" @click="startCreateTask('imap')">
              <div class="text-lg font-semibold mb-1">IMAP Task</div>
              <div class="text-sm text-gray-500">
                For IMAP mailboxes. You can create the task without assigning
                mailboxes first.
              </div>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="modalOpen" class="modal-overlay" @click.self="closeModal">
        <div class="modal max-w-2xl">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-bold">
              {{ editingTask ? "Edit Warmup Task" : "Add Warmup Task" }}
            </h2>
            <button
              @click="closeModal"
              class="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div class="mb-4">
            <label class="form-label">Protocol</label>
            <div class="flex gap-2">
              <span
                class="badge"
                :class="
                  form.protocol === 'oauth' ? 'badge-sent' : 'badge-failed'
                "
              >
                {{ form.protocol === "oauth" ? "OAuth2" : "IMAP" }}
              </span>
            </div>
            <p v-if="editingTask" class="text-xs text-gray-500 mt-1">
              Protocol cannot be changed after task creation.
            </p>
          </div>

          <div class="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label class="form-label">Task Name *</label>
              <input
                v-model="form.name"
                class="form-input"
                placeholder="Warmup for Sales Inbox"
              />
            </div>

            <div v-if="form.protocol === 'oauth'">
              <label class="form-label">OAuth App *</label>
              <select
                v-model="form.oauth_app_id"
                class="form-input"
                :disabled="!!editingTask"
                @change="onOauthAppChanged"
              >
                <option :value="null" disabled>Select OAuth app</option>
                <option
                  v-for="app in oauthAppsForForm"
                  :key="app.id"
                  :value="app.id"
                >
                  {{ oauthOptionLabel(app) }}
                </option>
              </select>
              <p class="text-xs text-gray-500 mt-1">
                OAuth app is assigned once when the task is created and cannot
                be changed later.
              </p>
            </div>

            <div v-else>
              <label class="form-label">IMAP Mailboxes</label>
              <div class="text-xs text-gray-500 mt-2">
                You can leave this empty now and attach mailboxes later.
              </div>
            </div>

            <div>
              <label class="form-label">Mailboxes</label>
              <select
                v-model="form.mailbox_ids"
                class="form-input"
                multiple
                size="6"
                :disabled="
                  form.protocol === 'oauth' ? !form.oauth_app_id : false
                "
              >
                <option
                  v-for="m in availableMailboxesForForm"
                  :key="m.id"
                  :value="m.id"
                >
                  {{ m.email
                  }}{{ m.display_name ? ` (${m.display_name})` : "" }}
                </option>
              </select>
              <p class="text-xs text-gray-500 mt-1">
                Only mailboxes not already assigned to another task are shown.
                When editing, this task’s current mailboxes remain available.
              </p>
              <p
                v-if="!availableMailboxesForForm.length"
                class="text-xs text-amber-600 mt-1"
              >
                No available mailboxes for this selection yet.
              </p>
            </div>

            <div>
              <label class="form-label">
                Delay Between Actions (seconds) *
              </label>
              <input
                v-model.number="form.delay_seconds"
                type="number"
                min="10"
                class="form-input"
              />
            </div>

            <div class="flex flex-col justify-end gap-2">
              <label class="inline-flex items-center">
                <input v-model="form.is_active" type="checkbox" class="mr-2" />
                Task active
              </label>
            </div>
          </div>

          <div class="mb-4">
            <label class="form-label">Allowed sender (optional)</label>
            <input
              v-model="form.allowed_sender"
              class="form-input"
              placeholder="sender@example.com"
            />
            <p class="text-xs text-gray-500 mt-1">
              Only emails from this address will be used for warmup. Leave empty
              to accept any sender.
            </p>
          </div>

          <div class="mb-4">
            <div class="font-semibold mb-2 text-sm">Warmup actions</div>
            <div class="grid grid-cols-2 gap-3 text-sm">
              <label class="inline-flex items-center">
                <input
                  v-model="form.do_move_to_inbox"
                  type="checkbox"
                  class="mr-2"
                />
                Move warmup emails to inbox
              </label>

              <label class="inline-flex items-center">
                <input v-model="form.do_open" type="checkbox" class="mr-2" />
                Open warmup emails
              </label>

              <label class="inline-flex items-center">
                <input
                  v-model="form.do_add_to_favorites"
                  type="checkbox"
                  class="mr-2"
                />
                Add to favourites / starred
              </label>

              <label class="inline-flex items-center">
                <input
                  v-model="form.do_mark_as_primary"
                  type="checkbox"
                  class="mr-2"
                />
                Mark as important
              </label>

              <label
                v-if="form.protocol === 'oauth'"
                class="inline-flex items-center"
              >
                <input v-model="form.do_reply" type="checkbox" class="mr-2" />
                Send reply
              </label>

              <label
                v-if="form.protocol === 'oauth'"
                class="inline-flex items-center"
              >
                <input
                  v-model="form.do_campaign_reply"
                  type="checkbox"
                  class="mr-2"
                />
                Campaign reply
              </label>

              <label class="inline-flex items-center">
                <input
                  v-model="form.do_detect_reply_event"
                  type="checkbox"
                  class="mr-2"
                />
                Detect reply event
              </label>
            </div>

            <p
              v-if="form.protocol === 'imap'"
              class="text-xs text-gray-500 mt-2"
            >
              IMAP tasks can use open, move to inbox, starred, and reply
              detection. Reply sending actions remain OAuth-only.
            </p>
          </div>

          <div
            class="mb-6"
            v-if="
              form.protocol === 'oauth' &&
              (form.do_reply || form.do_campaign_reply)
            "
          >
            <label class="form-label">Reply message</label>
            <textarea
              v-model="form.reply_message"
              class="form-input"
              rows="3"
              placeholder="Thanks for your email! Looking forward to staying in touch."
            />
          </div>

          <div class="flex gap-3 justify-end">
            <button class="btn btn-ghost" @click="closeModal">Cancel</button>
            <button class="btn btn-primary" @click="saveTask">
              {{ editingTask ? "Save Changes" : "Add Task" }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { RouterLink } from "vue-router";
import api from "@/api";
import { useToastStore } from "@/stores/toast";

const toast = useToastStore();

type WarmupProtocol = "oauth" | "imap";
type WarmupDelayUnit = "seconds" | "minutes" | "hours";

interface MailboxOption {
  id: number;
  email: string;
  display_name: string | null;
  provider?: string | null;
  oauth_app_id?: number | null;
  access_protocol?: string | null;
}

interface OAuthAppOption {
  id: number;
  name: string | null;
  client_id: string | null;
  provider: string | null;
}

interface WarmupTask {
  id: number;
  name: string;
  protocol: WarmupProtocol;
  oauth_app_id: number | null;
  oauth_app_name?: string | null;
  oauth_app_provider?: string | null;
  mailbox_ids: number[];
  do_move_to_inbox: boolean;
  do_open: boolean;
  do_add_to_favorites: boolean;
  do_mark_as_primary: boolean;
  do_reply: boolean;
  do_campaign_reply: boolean;
  do_detect_reply_event: boolean;
  reply_message: string | null;
  delay_seconds: number;
  delay_unit: WarmupDelayUnit;
  allowed_sender: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const tasks = ref<WarmupTask[]>([]);
const mailboxes = ref<MailboxOption[]>([]);
const allOauthApps = ref<OAuthAppOption[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

const modalOpen = ref(false);
const createTypeModalOpen = ref(false);
const editingTask = ref<WarmupTask | null>(null);

const form = ref({
  name: "",
  protocol: "oauth" as WarmupProtocol,
  oauth_app_id: null as number | null,
  mailbox_ids: [] as number[],
  do_move_to_inbox: true,
  do_open: true,
  do_add_to_favorites: false,
  do_mark_as_primary: false,
  do_reply: true,
  do_campaign_reply: false,
  do_detect_reply_event: false,
  reply_message: "Thanks for your email!",
  delay_seconds: 60,
  delay_unit: "seconds" as WarmupDelayUnit,
  allowed_sender: "" as string | null,
  is_active: true,
});

const mailboxDirectory = computed(() => {
  const map = new Map<number, MailboxOption>();
  for (const m of mailboxes.value) {
    map.set(m.id, m);
  }
  return map;
});

const oauthAppsForForm = computed(() => {
  if (form.value.protocol !== "oauth") return [];

  if (!editingTask.value) return allOauthApps.value;

  const currentId = editingTask.value.oauth_app_id;
  const found = allOauthApps.value.find((x) => x.id === currentId);

  if (found) return allOauthApps.value;
  if (currentId == null) return allOauthApps.value;

  return [
    ...allOauthApps.value,
    {
      id: currentId,
      name: `Assigned app #${currentId}`,
      client_id: null,
      provider: null,
    },
  ];
});

const usedMailboxIds = computed(() => {
  const ids = new Set<number>();

  for (const task of tasks.value) {
    if (editingTask.value && task.id === editingTask.value.id) continue;
    for (const mailboxId of task.mailbox_ids || []) {
      ids.add(mailboxId);
    }
  }

  return ids;
});

const currentEditingMailboxIds = computed(() => {
  return new Set<number>(editingTask.value?.mailbox_ids || []);
});

const availableMailboxesForForm = computed(() => {
  return mailboxes.value.filter((mailbox) => {
    if (currentEditingMailboxIds.value.has(mailbox.id)) return true;
    return !usedMailboxIds.value.has(mailbox.id);
  });
});

function oauthOptionLabel(app: OAuthAppOption) {
  const provider = app.provider ? `[${app.provider}] ` : "";
  const name = app.name?.trim() || "Unnamed OAuth App";
  return `${provider}${name}${app.client_id ? ` - ${app.client_id}` : ""}`;
}

function oauthAppLabel(oauthAppId: number | null) {
  if (!oauthAppId) return "—";
  const app = allOauthApps.value.find((x) => x.id === oauthAppId);
  if (!app) return `OAuth App #${oauthAppId}`;
  return oauthOptionLabel(app);
}

function defaultForm() {
  return {
    name: "",
    protocol: "oauth" as WarmupProtocol,
    oauth_app_id: null as number | null,
    mailbox_ids: [] as number[],
    do_move_to_inbox: true,
    do_open: true,
    do_add_to_favorites: false,
    do_mark_as_primary: false,
    do_reply: true,
    do_campaign_reply: false,
    do_detect_reply_event: false,
    reply_message: "Thanks for your email!",
    delay_seconds: 60,
    delay_unit: "seconds" as WarmupDelayUnit,
    allowed_sender: "" as string | null,
    is_active: true,
  };
}

function resetForm() {
  form.value = defaultForm();
  mailboxes.value = [];
  editingTask.value = null;
  error.value = null;
}

function applyProtocolDefaults(protocol: WarmupProtocol) {
  form.value.protocol = protocol;
  form.value.mailbox_ids = [];

  if (protocol === "oauth") {
    form.value.oauth_app_id = null;
    form.value.do_reply = true;
    form.value.do_campaign_reply = false;
    form.value.do_detect_reply_event = false;
    form.value.reply_message =
      form.value.reply_message || "Thanks for your email!";
  } else {
    form.value.oauth_app_id = null;
    form.value.do_reply = false;
    form.value.do_campaign_reply = false;
    form.value.do_detect_reply_event = false;
    form.value.reply_message = null;
  }
}

function openCreateTypeModal() {
  createTypeModalOpen.value = true;
}

function closeCreateTypeModal() {
  createTypeModalOpen.value = false;
}

async function startCreateTask(protocol: WarmupProtocol) {
  closeCreateTypeModal();
  resetForm();
  applyProtocolDefaults(protocol);

  if (protocol === "oauth") {
    await loadAvailableOauthApps();
    mailboxes.value = [];
  } else {
    await loadImapMailboxes();
  }

  modalOpen.value = true;
}

async function openEditModal(task: WarmupTask) {
  error.value = null;
  editingTask.value = task;

  form.value = {
    name: task.name,
    protocol: task.protocol,
    oauth_app_id: task.oauth_app_id,
    mailbox_ids: [...task.mailbox_ids],
    do_move_to_inbox: task.do_move_to_inbox,
    do_open: task.do_open,
    do_add_to_favorites: task.do_add_to_favorites,
    do_mark_as_primary: task.do_mark_as_primary,
    do_reply: task.do_reply,
    do_campaign_reply: task.do_campaign_reply,
    do_detect_reply_event: task.do_detect_reply_event,
    reply_message: task.reply_message || "",
    delay_seconds: task.delay_seconds,
    delay_unit: task.delay_unit,
    allowed_sender: task.allowed_sender || "",
    is_active: task.is_active,
  };

  if (task.protocol === "oauth") {
    await loadAvailableOauthApps();
    if (task.oauth_app_id) {
      await loadMailboxesByOauthApp(task.oauth_app_id);
    } else {
      mailboxes.value = [];
    }
  } else {
    await loadImapMailboxes();
  }

  modalOpen.value = true;
}

function closeModal() {
  modalOpen.value = false;
  resetForm();
}

function mailboxLabel(id: number, task?: WarmupTask) {
  const m = mailboxDirectory.value.get(id);
  if (m) {
    return m.display_name ? `${m.email} (${m.display_name})` : m.email;
  }

  if (task?.protocol === "oauth" && task.oauth_app_id) {
    return `Mailbox ${id}`;
  }

  return `Mailbox ${id}`;
}

async function loadAvailableOauthApps() {
  try {
    const res = await api.get("/warmup-tasks/available-oauth-apps");
    allOauthApps.value = res.data || [];
  } catch (e: any) {
    console.error(e);
    toast.show("Failed to load OAuth apps", "error");
  }
}

async function loadMailboxesByOauthApp(oauthAppId: number) {
  try {
    const res = await api.get(
      `/warmup-tasks/mailboxes-by-oauth-app/${oauthAppId}`,
    );
    mailboxes.value = res.data || [];
  } catch (e: any) {
    console.error(e);
    mailboxes.value = [];
    toast.show("Failed to load mailboxes for selected OAuth app", "error");
  }
}

async function loadImapMailboxes() {
  try {
    const res = await api.get("/mailboxes");
    mailboxes.value = (res.data || []).filter((m: MailboxOption) => {
      const provider = (m.provider || "").toLowerCase();
      const accessProtocol = (m.access_protocol || "").toLowerCase();

      return (
        accessProtocol === "imap" ||
        provider === "imap" ||
        (!m.oauth_app_id &&
          provider !== "google" &&
          provider !== "microsoft" &&
          provider !== "yahoo")
      );
    });
  } catch (e: any) {
    console.error(e);
    mailboxes.value = [];
    toast.show("Failed to load IMAP mailboxes", "error");
  }
}

async function onOauthAppChanged() {
  if (form.value.protocol !== "oauth") return;

  form.value.mailbox_ids = [];

  if (!form.value.oauth_app_id) {
    mailboxes.value = [];
    return;
  }

  await loadMailboxesByOauthApp(form.value.oauth_app_id);
}

async function loadTasks() {
  loading.value = true;
  error.value = null;

  try {
    const res = await api.get("/warmup-tasks");
    tasks.value = res.data || [];
  } catch (e: any) {
    console.error(e);
    error.value = "Failed to load warmup tasks";
    toast.show(e.response?.data?.detail || error.value, "error");
  } finally {
    loading.value = false;
  }
}

function buildBasePayload() {
  return {
    name: form.value.name.trim(),
    mailbox_ids: [...form.value.mailbox_ids],
    do_move_to_inbox: form.value.do_move_to_inbox,
    do_open: form.value.do_open,
    do_add_to_favorites: form.value.do_add_to_favorites,
    do_mark_as_primary: form.value.do_mark_as_primary,
    do_reply: form.value.protocol === "oauth" ? form.value.do_reply : false,
    do_campaign_reply:
      form.value.protocol === "oauth" ? form.value.do_campaign_reply : false,
    do_detect_reply_event: form.value.do_detect_reply_event,
    reply_message:
      form.value.protocol === "oauth" &&
      (form.value.do_reply || form.value.do_campaign_reply)
        ? (form.value.reply_message || "").trim() || null
        : null,
    delay_seconds: form.value.delay_seconds,
    delay_unit: form.value.delay_unit,
    allowed_sender: form.value.allowed_sender?.trim()
      ? form.value.allowed_sender.trim()
      : null,
    is_active: form.value.is_active,
  };
}

function buildCreatePayload() {
  if (form.value.protocol === "oauth") {
    return {
      ...buildBasePayload(),
      protocol: "oauth" as const,
      oauth_app_id: form.value.oauth_app_id,
    };
  }

  return {
    ...buildBasePayload(),
    protocol: "imap" as const,
    oauth_app_id: null,
  };
}

function buildUpdatePayload() {
  return {
    ...buildBasePayload(),
  };
}

async function saveTask() {
  error.value = null;

  if (!form.value.name.trim()) {
    toast.show("Task name is required", "error");
    return;
  }

  if (
    form.value.protocol === "oauth" &&
    !form.value.oauth_app_id &&
    !editingTask.value
  ) {
    toast.show("Please select an OAuth app", "error");
    return;
  }

  if (form.value.protocol === "imap" && form.value.oauth_app_id) {
    toast.show("IMAP tasks cannot have an OAuth app", "error");
    return;
  }

  if (form.value.delay_seconds <= 0) {
    toast.show("Delay must be positive", "error");
    return;
  }

  try {
    if (editingTask.value) {
      const payload = buildUpdatePayload();
      const res = await api.put(
        `/warmup-tasks/${editingTask.value.id}`,
        payload,
      );

      const idx = tasks.value.findIndex((t) => t.id === editingTask.value?.id);
      if (idx !== -1) {
        tasks.value[idx] = res.data;
      } else {
        await loadTasks();
      }

      toast.show("Warmup task updated!", "success");
    } else {
      const payload = buildCreatePayload();
      console.log("CREATE warmup payload", JSON.stringify(payload, null, 2));
      const res = await api.post("/warmup-tasks", payload);
      tasks.value.push(res.data);
      toast.show("Warmup task created!", "success");
      await loadAvailableOauthApps();
    }

    closeModal();
  } catch (e: any) {
    console.error(e);
    const msg = e.response?.data?.detail || "Failed to save warmup task";
    error.value = msg;
    toast.show(msg, "error");
  }
}

async function deleteTask(task: WarmupTask) {
  if (!confirm(`Delete warmup task "${task.name}"?`)) return;

  try {
    await api.delete(`/warmup-tasks/${task.id}`);
    tasks.value = tasks.value.filter((t) => t.id !== task.id);
    toast.show("Warmup task deleted", "success");
    await loadAvailableOauthApps();
  } catch (e: any) {
    console.error(e);
    const msg = e.response?.data?.detail || "Failed to delete warmup task";
    error.value = msg;
    toast.show(msg, "error");
  }
}

onMounted(async () => {
  await loadAvailableOauthApps();
  await loadTasks();
});
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
.protocol-card {
  @apply text-left rounded-2xl border border-border dark:border-border-dark p-5 hover:bg-surface-off dark:hover:bg-surface-dark-off transition;
}
</style>

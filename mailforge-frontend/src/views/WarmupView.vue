<template>
  <div>
    <!-- HEADER -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <div class="page-title">Warmup Tasks</div>
        <div class="page-subtitle">{{ tasks.length }} tasks</div>
      </div>
      <div class="flex gap-3">
        <button class="btn btn-primary" @click="openCreateModal">
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
            <th class="th">Name</th>
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
              colspan="9"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              Loading...
            </td>
          </tr>

          <tr v-else-if="!tasks.length">
            <td
              colspan="9"
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
              <div class="text-sm">
                <span
                  v-if="!t.mailbox_ids.length"
                  class="text-gray-400 dark:text-gray-600"
                >
                  No mailboxes
                </span>
                <div v-else class="flex flex-col gap-0.5">
                  <span v-for="id in t.mailbox_ids" :key="id" class="truncate">
                    • {{ mailboxLabel(id) }}
                  </span>
                </div>
              </div>
            </td>

            <td class="td">
              <div class="text-xs text-gray-500">
                <span v-if="t.allowed_sender">
                  From: <span class="font-mono">{{ t.allowed_sender }}</span>
                </span>
                <span v-else class="text-gray-400"> Any sender </span>
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
                  Mark as primary
                </span>
                <span v-if="t.do_reply" class="badge badge-sent">Reply</span>
                <span v-if="t.do_campaign_reply" class="badge badge-sent">
                  Campaign reply
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

    <!-- CREATE / EDIT MODAL -->
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

          <div class="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label class="form-label">Task Name *</label>
              <input
                v-model="form.name"
                class="form-input"
                placeholder="Warmup for Sales Inbox"
              />
            </div>

            <div>
              <label class="form-label">Mailboxes *</label>
              <select
                v-model="form.mailbox_ids"
                class="form-input"
                multiple
                size="4"
              >
                <option v-for="m in mailboxes" :key="m.id" :value="m.id">
                  {{ m.email }}
                  {{ m.display_name ? `(${m.display_name})` : "" }}
                </option>
              </select>
              <p class="text-xs text-gray-500 mt-1">
                Hold Ctrl / Cmd to select multiple mailboxes.
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
                Mark as primary
              </label>
              <label class="inline-flex items-center">
                <input v-model="form.do_reply" type="checkbox" class="mr-2" />
                Send reply
              </label>
              <label class="inline-flex items-center">
                <input
                  v-model="form.do_campaign_reply"
                  type="checkbox"
                  class="mr-2"
                />
                Campaign reply
              </label>
            </div>
          </div>

          <div class="mb-6" v-if="form.do_reply || form.do_campaign_reply">
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
import { ref, onMounted } from "vue";
import { RouterLink } from "vue-router";
import api from "@/api";
import { useToastStore } from "@/stores/toast";

const toast = useToastStore();

interface MailboxOption {
  id: number;
  email: string;
  display_name: string | null;
}

type WarmupDelayUnit = "seconds" | "minutes" | "hours";

interface WarmupTask {
  id: number;
  name: string;
  mailbox_ids: number[];
  do_move_to_inbox: boolean;
  do_open: boolean;
  do_add_to_favorites: boolean;
  do_mark_as_primary: boolean;
  do_reply: boolean;
  do_campaign_reply: boolean;
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
const loading = ref(false);
const error = ref<string | null>(null);

const modalOpen = ref(false);
const editingTask = ref<WarmupTask | null>(null);

const form = ref({
  name: "",
  mailbox_ids: [] as number[],
  do_move_to_inbox: true,
  do_open: true,
  do_add_to_favorites: false,
  do_mark_as_primary: false,
  do_reply: true,
  do_campaign_reply: false,
  reply_message: "Thanks for your email!",
  delay_seconds: 60,
  delay_unit: "seconds" as WarmupDelayUnit,
  allowed_sender: "" as string | null,
  is_active: true,
});

function resetForm() {
  form.value = {
    name: "",
    mailbox_ids: [],
    do_move_to_inbox: true,
    do_open: true,
    do_add_to_favorites: false,
    do_mark_as_primary: false,
    do_reply: true,
    do_campaign_reply: false,
    reply_message: "Thanks for your email!",
    delay_seconds: 60,
    delay_unit: "seconds",
    allowed_sender: "",
    is_active: true,
  };
  editingTask.value = null;
}

function openCreateModal() {
  resetForm();
  modalOpen.value = true;
}

function openEditModal(task: WarmupTask) {
  editingTask.value = task;
  form.value = {
    name: task.name,
    mailbox_ids: [...task.mailbox_ids],
    do_move_to_inbox: task.do_move_to_inbox,
    do_open: task.do_open,
    do_add_to_favorites: task.do_add_to_favorites,
    do_mark_as_primary: task.do_mark_as_primary,
    do_reply: task.do_reply,
    do_campaign_reply: task.do_campaign_reply,
    reply_message: task.reply_message || "",
    delay_seconds: task.delay_seconds,
    delay_unit: task.delay_unit,
    allowed_sender: task.allowed_sender || "",
    is_active: task.is_active,
  };
  modalOpen.value = true;
}

function closeModal() {
  modalOpen.value = false;
}

function mailboxLabel(id: number) {
  const m = mailboxes.value.find((x) => x.id === id);
  if (!m) return `Mailbox ${id}`;
  return m.display_name ? `${m.email} (${m.display_name})` : m.email;
}

async function loadMailboxes() {
  try {
    const res = await api.get("/mailboxes/warmup-options");
    mailboxes.value = res.data;
  } catch (e: any) {
    console.error(e);
    toast.show("Failed to load mailboxes", "error");
  }
}

async function loadTasks() {
  loading.value = true;
  error.value = null;
  try {
    const res = await api.get("/warmup-tasks");
    tasks.value = res.data;
  } catch (e: any) {
    console.error(e);
    error.value = "Failed to load warmup tasks";
    toast.show(e.response?.data?.detail || error.value, "error");
  } finally {
    loading.value = false;
  }
}

async function saveTask() {
  if (!form.value.name.trim()) {
    toast.show("Task name is required", "error");
    return;
  }
  if (!form.value.mailbox_ids.length) {
    toast.show("Please select at least one mailbox", "error");
    return;
  }
  if (form.value.delay_seconds <= 0) {
    toast.show("Delay must be positive", "error");
    return;
  }

  const payload = {
    ...form.value,
    allowed_sender: form.value.allowed_sender?.trim()
      ? form.value.allowed_sender.trim()
      : null,
    reply_message:
      form.value.do_reply || form.value.do_campaign_reply
        ? form.value.reply_message
        : null,
  };

  try {
    if (editingTask.value) {
      const res = await api.put(
        `/warmup-tasks/${editingTask.value.id}`,
        payload,
      );
      const idx = tasks.value.findIndex((t) => t.id === editingTask.value?.id);
      if (idx !== -1) tasks.value[idx] = res.data;
      toast.show("Warmup task updated!", "success");
    } else {
      const res = await api.post("/warmup-tasks", payload);
      tasks.value.push(res.data);
      toast.show("Warmup task created!", "success");
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
  } catch (e: any) {
    console.error(e);
    const msg = e.response?.data?.detail || "Failed to delete warmup task";
    error.value = msg;
    toast.show(msg, "error");
  }
}

onMounted(async () => {
  await loadMailboxes();
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
</style>

<template>
  <div>
    <!-- HEADER -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <div class="page-title">IMAP Mailboxes</div>
        <div class="page-subtitle">{{ mailboxes.length }} mailboxes</div>
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
          Add IMAP Mailbox
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
            <th class="th">Display name</th>
            <th class="th">Email</th>
            <th class="th">IMAP</th>
            <th class="th">SMTP</th>
            <th class="th">Warmup</th>
            <th class="th">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td
              colspan="6"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              Loading...
            </td>
          </tr>
          <tr v-else-if="!mailboxes.length">
            <td
              colspan="6"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              No IMAP mailboxes yet. Add your first one above.
            </td>
          </tr>
          <tr
            v-else
            v-for="m in mailboxes"
            :key="m.id"
            class="hover:bg-surface-off dark:hover:bg-surface-dark-off border-b border-border dark:border-border-dark last:border-0"
          >
            <td class="td text-gray-500 dark:text-gray-400">
              {{ m.id }}
            </td>
            <td class="td text-xs text-gray-400 dark:text-gray-500">
              {{ m.display_name }}
            </td>
            <td class="td">
              <div class="font-semibold">{{ m.email }}</div>
            </td>
            <td class="td text-xs">
              {{ m.imap_host }}:{{ m.imap_port }}
              <span class="text-gray-500">
                (SSL: {{ m.imap_ssl ? "yes" : "no" }})
              </span>
            </td>
            <td class="td text-xs">
              {{ m.smtp_host }}:{{ m.smtp_port }}
              <span class="text-gray-500">
                (TLS: {{ m.smtp_tls ? "yes" : "no" }})
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
              <button
                class="btn btn-danger btn-sm"
                @click="removeMailbox(m.id)"
              >
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- CREATE MODAL -->
    <Teleport to="body">
      <div
        v-if="createModal"
        class="modal-overlay"
        @click.self="closeCreateModal"
      >
        <div class="modal">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-bold">Add IMAP Mailbox</h2>
            <button
              @click="closeCreateModal"
              class="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div class="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label class="form-label">Email *</label>
              <input
                v-model="form.email"
                type="email"
                class="form-input"
                placeholder="user@example.com"
              />
            </div>
            <div>
              <label class="form-label">Display Name</label>
              <input
                v-model="form.display_name"
                class="form-input"
                placeholder="My Gmail, Sales Inbox..."
              />
            </div>

            <div>
              <label class="form-label">IMAP Host *</label>
              <input
                v-model="form.imap_host"
                class="form-input"
                placeholder="imap.gmail.com"
              />
            </div>
            <div>
              <label class="form-label">IMAP Port *</label>
              <input
                v-model.number="form.imap_port"
                type="number"
                class="form-input"
              />
            </div>

            <div>
              <label class="form-label">SMTP Host *</label>
              <input
                v-model="form.smtp_host"
                class="form-input"
                placeholder="smtp.gmail.com"
              />
            </div>
            <div>
              <label class="form-label">SMTP Port *</label>
              <input
                v-model.number="form.smtp_port"
                type="number"
                class="form-input"
              />
            </div>

            <div>
              <label class="form-label">Username *</label>
              <input
                v-model="form.username"
                class="form-input"
                placeholder="usually same as email"
              />
            </div>
            <div>
              <label class="form-label">Password / App Password *</label>
              <input
                v-model="form.password"
                type="password"
                class="form-input"
                placeholder="App password if 2FA enabled"
              />
            </div>
          </div>

          <div class="flex gap-4 mb-6 text-sm">
            <label class="inline-flex items-center">
              <input v-model="form.imap_ssl" type="checkbox" class="mr-2" />
              IMAP SSL
            </label>
            <label class="inline-flex items-center">
              <input v-model="form.smtp_tls" type="checkbox" class="mr-2" />
              SMTP TLS
            </label>
            <label class="inline-flex items-center">
              <input
                v-model="form.warmup_enabled"
                type="checkbox"
                class="mr-2"
              />
              Enable warmup
            </label>
          </div>

          <div class="flex gap-3 justify-end">
            <button class="btn btn-ghost" @click="closeCreateModal">
              Cancel
            </button>
            <button class="btn btn-primary" @click="createMailbox">
              Add Mailbox
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import api from "@/api";
import { useToastStore } from "@/stores/toast";

const toast = useToastStore();

interface MailboxOption {
  id: number;
  email: string;
  display_name: string | null;
}

const mailboxes = ref<MailboxOption[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

// modal state
const createModal = ref(false);

// form state
const form = ref({
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

function resetForm() {
  form.value = {
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

function openCreateModal() {
  resetForm();
  createModal.value = true;
}

function closeCreateModal() {
  createModal.value = false;
}

async function loadMailboxes() {
  loading.value = true;
  error.value = null;
  try {
    const res = await api.get("/imap-mailboxes");
    mailboxes.value = res.data;
  } catch (e: any) {
    console.error(e);
    error.value = "Failed to load IMAP mailboxes";
    toast.show(e.response?.data?.detail || error.value, "error");
  } finally {
    loading.value = false;
  }
}

async function createMailbox() {
  if (!form.value.email || !form.value.imap_host || !form.value.smtp_host) {
    toast.show("Email, IMAP host and SMTP host are required", "error");
    return;
  }
  try {
    const res = await api.post("/imap-mailboxes", form.value);
    mailboxes.value.push(res.data);
    toast.show("IMAP mailbox added!", "success");
    closeCreateModal();
  } catch (e: any) {
    console.error(e);
    const msg = e.response?.data?.detail || "Failed to create IMAP mailbox";
    error.value = msg;
    toast.show(msg, "error");
  }
}

async function removeMailbox(id: number) {
  if (!confirm("Delete this IMAP mailbox?")) return;
  try {
    await api.delete(`/imap-mailboxes/${id}`);
    mailboxes.value = mailboxes.value.filter((m) => m.id !== id);
    toast.show("Mailbox deleted", "success");
  } catch (e: any) {
    console.error(e);
    const msg = e.response?.data?.detail || "Failed to delete IMAP mailbox";
    error.value = msg;
    toast.show(msg, "error");
  }
}

onMounted(loadMailboxes);
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
  @apply bg-surface dark:bg-surface-dark border border-border dark:border-border-dark rounded-2xl p-8 w-full max-w-xl shadow-2xl;
}
</style>

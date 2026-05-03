<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <div class="page-title">SMTP Servers</div>
        <div class="page-subtitle">Manage your custom SMTP configurations</div>
      </div>
      <button class="btn btn-primary" @click="openModal()">
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
        Add SMTP Server
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-if="!configs.length"
      class="flex flex-col items-center text-center py-20 text-gray-400 dark:text-gray-600"
    >
      <svg
        class="w-12 h-12 mb-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <path d="M8 21h8M12 17v4" />
      </svg>
      <h3 class="text-gray-700 dark:text-gray-300 font-semibold mb-2">
        No SMTP servers yet
      </h3>
      <p class="text-sm max-w-xs mb-6">
        Add a custom SMTP server to send emails through your own mail provider
      </p>
      <button class="btn btn-primary" @click="openModal()">
        Add SMTP Server
      </button>
    </div>

    <!-- Table -->
    <div
      v-else
      class="overflow-x-auto rounded-xl border border-border dark:border-border-dark"
    >
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-surface-off dark:bg-surface-dark-off">
            <th class="th">Name</th>
            <th class="th">Host</th>
            <th class="th">Port</th>
            <th class="th">Username</th>
            <th class="th">Security</th>
            <th class="th">Status</th>
            <th class="th">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="c in configs"
            :key="c.id"
            class="border-b border-border dark:border-border-dark last:border-0 hover:bg-surface-off dark:hover:bg-surface-dark-off"
          >
            <td class="td font-semibold">{{ c.name }}</td>
            <td class="td font-mono text-xs text-gray-500 dark:text-gray-400">
              {{ c.host }}
            </td>
            <td class="td tabular-nums">{{ c.port }}</td>
            <td class="td text-gray-500 dark:text-gray-400">
              {{ c.username }}
            </td>
            <td class="td">
              <span
                class="badge"
                :class="
                  c.use_ssl
                    ? 'badge-sent'
                    : c.use_tls
                      ? 'badge-sending'
                      : 'badge-draft'
                "
              >
                {{ c.use_ssl ? "SSL" : c.use_tls ? "TLS" : "None" }}
              </span>
            </td>
            <td class="td">
              <span
                class="badge"
                :class="c.is_active ? 'badge-sent' : 'badge-failed'"
              >
                {{ c.is_active ? "Active" : "Inactive" }}
              </span>
            </td>
            <td class="td">
              <div class="flex gap-2">
                <button
                  class="btn btn-ghost btn-sm"
                  @click="testConfig(c)"
                  :disabled="testing === c.id"
                >
                  <svg
                    v-if="testing === c.id"
                    class="animate-spin w-3 h-3"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                  </svg>
                  {{ testing === c.id ? "Testing..." : "Test" }}
                </button>
                <button class="btn btn-ghost btn-sm" @click="openModal(c)">
                  Edit
                </button>
                <button
                  class="btn btn-danger btn-sm"
                  @click="deleteConfig(c.id)"
                >
                  Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <Teleport to="body">
      <div
        v-if="modal"
        class="fixed inset-0 bg-black/60 z-[200] flex items-center justify-center p-4"
        @click.self="modal = false"
      >
        <div
          class="bg-surface dark:bg-surface-dark border border-border dark:border-border-dark rounded-2xl p-8 w-full max-w-lg shadow-2xl"
        >
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-bold">
              {{ editing ? "Edit SMTP Server" : "Add SMTP Server" }}
            </h2>
            <button
              @click="modal = false"
              class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              ✕
            </button>
          </div>

          <div class="mb-4">
            <label class="form-label">Display Name *</label>
            <input
              v-model="form.name"
              class="form-input"
              placeholder="e.g. Company Mail"
            />
          </div>
          <div class="grid grid-cols-[1fr_100px] gap-3 mb-4">
            <div>
              <label class="form-label">SMTP Host *</label>
              <input
                v-model="form.host"
                class="form-input font-mono"
                placeholder="smtp.gmail.com"
              />
            </div>
            <div>
              <label class="form-label">Port</label>
              <input
                v-model.number="form.port"
                class="form-input font-mono"
                type="number"
                placeholder="587"
              />
            </div>
          </div>
          <div class="mb-4">
            <label class="form-label">Username *</label>
            <input
              v-model="form.username"
              class="form-input"
              placeholder="you@company.com"
            />
          </div>
          <div class="mb-4">
            <label class="form-label">{{
              editing ? "New Password (leave blank to keep)" : "Password *"
            }}</label>
            <input
              v-model="form.password"
              class="form-input"
              type="password"
              placeholder="••••••••"
            />
          </div>
          <div class="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label class="form-label">From Email</label>
              <input
                v-model="form.from_email"
                class="form-input"
                placeholder="noreply@company.com"
              />
            </div>
            <div>
              <label class="form-label">From Name</label>
              <input
                v-model="form.from_name"
                class="form-input"
                placeholder="Company Name"
              />
            </div>
          </div>
          <div class="flex gap-6 mb-6">
            <label class="flex items-center gap-2 cursor-pointer text-sm">
              <input type="checkbox" v-model="form.use_tls" class="rounded" />
              Use TLS (STARTTLS)
            </label>
            <label class="flex items-center gap-2 cursor-pointer text-sm">
              <input type="checkbox" v-model="form.use_ssl" class="rounded" />
              Use SSL
            </label>
          </div>

          <div class="flex gap-3 justify-end">
            <button class="btn btn-ghost" @click="modal = false">Cancel</button>
            <button
              class="btn btn-primary"
              @click="saveConfig"
              :disabled="saving"
            >
              {{ saving ? "Saving..." : editing ? "Update" : "Add Server" }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "@/api";
import { useToastStore } from "@/stores/toast";

const toast = useToastStore();
const configs = ref([]);
const modal = ref(false);
const editing = ref(null);
const saving = ref(false);
const testing = ref(null);

const defaultForm = () => ({
  name: "",
  host: "",
  port: 587,
  username: "",
  password: "",
  use_tls: true,
  use_ssl: false,
  from_email: "",
  from_name: "",
});
const form = ref(defaultForm());

onMounted(load);

async function load() {
  try {
    configs.value = (await api.get("/smtp")).data;
  } catch (e) {
    toast.show("Failed to load SMTP configs", "error");
  }
}

function openModal(config = null) {
  editing.value = config;
  form.value = config
    ? {
        name: config.name,
        host: config.host,
        port: config.port,
        username: config.username,
        password: "",
        use_tls: config.use_tls,
        use_ssl: config.use_ssl,
        from_email: config.from_email || "",
        from_name: config.from_name || "",
      }
    : defaultForm();
  modal.value = true;
}

async function saveConfig() {
  if (!form.value.name || !form.value.host || !form.value.username) {
    toast.show("Name, host and username are required", "error");
    return;
  }
  if (!editing.value && !form.value.password) {
    toast.show("Password is required", "error");
    return;
  }
  saving.value = true;
  try {
    const payload = { ...form.value };
    if (!payload.password) delete payload.password;
    if (editing.value) await api.put(`/smtp/${editing.value.id}`, payload);
    else await api.post("/smtp", payload);
    toast.show(
      editing.value ? "Server updated! ✅" : "Server added! ✅",
      "success",
    );
    modal.value = false;
    load();
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  } finally {
    saving.value = false;
  }
}

async function testConfig(config) {
  testing.value = config.id;
  try {
    const { data } = await api.post(`/smtp/${config.id}/test`);
    toast.show(data.message, "success");
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  } finally {
    testing.value = null;
  }
}

async function deleteConfig(id) {
  if (!confirm("Delete this SMTP server?")) return;
  try {
    await api.delete(`/smtp/${id}`);
    toast.show("Deleted", "success");
    load();
  } catch (e) {
    toast.show(e.message, "error");
  }
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

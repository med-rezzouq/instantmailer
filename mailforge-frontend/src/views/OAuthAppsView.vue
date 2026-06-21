<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <div class="page-title">OAuth Apps</div>
        <div class="page-subtitle">{{ oauthApps.length }} oauth apps</div>
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
          Add OAuth App
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
            <th class="th">App Name</th>
            <th class="th">Client ID</th>
            <th class="th">Project ID</th>
            <th class="th">Owner Email</th>
            <th class="th">Max Mailboxes</th>
            <th class="th">Secret</th>
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

          <tr v-else-if="!oauthApps.length">
            <td
              colspan="9"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              No OAuth apps yet. Add your first one above.
            </td>
          </tr>

          <tr
            v-else
            v-for="app in oauthApps"
            :key="app.id"
            class="hover:bg-surface-off dark:hover:bg-surface-dark-off border-b border-border dark:border-border-dark last:border-0"
          >
            <td class="td text-gray-500 dark:text-gray-400">{{ app.id }}</td>

            <td class="td">
              <span class="badge badge-muted">
                {{ app.provider }}
              </span>
            </td>

            <td class="td">
              <div class="font-semibold">{{ app.name }}</div>
            </td>

            <td class="td text-xs text-gray-500 dark:text-gray-400 break-all">
              {{ app.client_id }}
            </td>

            <td class="td text-xs text-gray-500 dark:text-gray-400 break-all">
              {{ app.project_id || "—" }}
            </td>

            <td class="td text-xs text-gray-500 dark:text-gray-400 break-all">
              {{ app.owner_email || "—" }}
            </td>

            <td class="td text-sm font-medium">
              {{ app.max_mailboxes }}
            </td>

            <td class="td text-xs text-gray-500 dark:text-gray-400">
              {{ app.client_secret_masked || "••••••••" }}
            </td>

            <td class="td">
              <div class="flex gap-2">
                <button
                  class="btn btn-secondary btn-sm"
                  @click="openEditModal(app)"
                >
                  Edit
                </button>
                <button
                  class="btn btn-danger btn-sm"
                  @click="removeOAuthApp(app.id)"
                >
                  Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Teleport to="body">
      <div v-if="modalOpen" class="modal-overlay" @click.self="closeModal">
        <div class="modal">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-bold">
              {{ editingId ? "Edit OAuth App" : "Add OAuth App" }}
            </h2>
            <button
              @click="closeModal"
              class="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div class="grid grid-cols-2 gap-4 mb-6">
            <div class="col-span-2">
              <label class="form-label">Provider *</label>
              <select
                v-model="form.provider"
                class="form-input"
                :disabled="!!editingId"
              >
                <option value="google">Google</option>
                <option value="microsoft">Microsoft</option>
                <option value="yahoo">Yahoo</option>
                <option value="aol">AOL</option>
              </select>
              <p v-if="editingId" class="text-xs text-gray-500 mt-1">
                Provider cannot be changed after creation.
              </p>
            </div>

            <div class="col-span-2">
              <label class="form-label">App Name *</label>
              <input
                v-model="form.name"
                class="form-input"
                placeholder="My Google App"
              />
            </div>

            <div class="col-span-2">
              <label class="form-label">Owner Email</label>
              <input
                v-model="form.owner_email"
                type="email"
                class="form-input"
                placeholder="owner@gmail.com"
              />
            </div>

            <div class="col-span-2">
              <label class="form-label">Client ID *</label>
              <input
                v-model="form.client_id"
                class="form-input"
                placeholder="Paste client ID"
              />
            </div>

            <div class="col-span-2">
              <label class="form-label">
                Client Secret {{ editingId ? "" : "*" }}
              </label>
              <input
                v-model="form.client_secret"
                type="password"
                class="form-input"
                :placeholder="
                  editingId
                    ? 'Leave blank to keep current secret'
                    : 'Paste client secret'
                "
              />
            </div>

            <div class="col-span-2">
              <label class="form-label">Max Mailboxes *</label>
              <input
                v-model.number="form.max_mailboxes"
                type="number"
                min="1"
                class="form-input"
                :disabled="!!editingId"
                placeholder="2"
              />
              <p class="text-xs text-gray-500 mt-1">
                {{
                  editingId
                    ? "Mailbox limit is set when the OAuth app is created and cannot be changed later."
                    : "Set the maximum number of mailboxes that can be linked to this OAuth app."
                }}
              </p>
            </div>
          </div>

          <div class="flex gap-3 justify-end">
            <button class="btn btn-ghost" @click="closeModal">Cancel</button>
            <button
              class="btn btn-primary"
              @click="submitForm"
              :disabled="saving"
            >
              {{
                saving
                  ? "Saving..."
                  : editingId
                    ? "Save Changes"
                    : "Add OAuth App"
              }}
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

type Provider = "google" | "microsoft" | "yahoo" | "aol";

interface OAuthApp {
  id: number;
  provider: Provider;
  name: string;
  client_id: string;
  client_secret_masked?: string | null;
  project_id?: string | null;
  owner_email?: string | null;
  max_mailboxes: number;
}

const oauthApps = ref<OAuthApp[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

const modalOpen = ref(false);
const editingId = ref<number | null>(null);

const form = ref({
  provider: "google" as Provider,
  name: "",
  owner_email: "",
  client_id: "",
  client_secret: "",
  max_mailboxes: 2,
});

function resetForm() {
  form.value = {
    provider: "google",
    name: "",
    owner_email: "",
    client_id: "",
    client_secret: "",
    max_mailboxes: 2,
  };
}

function openCreateModal() {
  editingId.value = null;
  resetForm();
  modalOpen.value = true;
}

function openEditModal(app: OAuthApp) {
  editingId.value = app.id;
  form.value = {
    provider: app.provider,
    name: app.name,
    owner_email: app.owner_email || "",
    client_id: app.client_id,
    client_secret: "",
    max_mailboxes: app.max_mailboxes,
  };
  modalOpen.value = true;
}

function closeModal() {
  modalOpen.value = false;
  editingId.value = null;
  resetForm();
}

async function loadOAuthApps() {
  loading.value = true;
  error.value = null;
  try {
    const res = await api.get("/oauthapps");
    oauthApps.value = res.data || [];
  } catch (e: any) {
    console.error(e);
    error.value = "Failed to load OAuth apps";
    toast.show(e.response?.data?.detail || error.value, "error");
  } finally {
    loading.value = false;
  }
}

const saving = ref(false);

async function submitForm() {
  if (!form.value.provider || !form.value.name || !form.value.client_id) {
    toast.show("Provider, app name and client ID are required", "error");
    return;
  }

  if (!editingId.value && !form.value.client_secret) {
    toast.show("Client secret is required", "error");
    return;
  }

  if (
    !editingId.value &&
    (!form.value.max_mailboxes || form.value.max_mailboxes < 1)
  ) {
    toast.show("Max mailboxes must be at least 1", "error");
    return;
  }

  saving.value = true;
  error.value = null;

  try {
    const payload: any = {
      provider: form.value.provider,
      name: form.value.name,
      owner_email: form.value.owner_email || null,
      client_id: form.value.client_id,
    };

    if (form.value.client_secret) {
      payload.client_secret = form.value.client_secret;
    }

    if (!editingId.value) {
      payload.max_mailboxes = form.value.max_mailboxes;
    }

    if (editingId.value) {
      const res = await api.put(`/oauthapps/${editingId.value}`, payload);
      const idx = oauthApps.value.findIndex((x) => x.id === editingId.value);
      if (idx !== -1) oauthApps.value[idx] = res.data;
      toast.show("OAuth app updated", "success");
    } else {
      const res = await api.post("/oauthapps", payload);
      oauthApps.value.unshift(res.data);
      toast.show("OAuth app created", "success");
    }

    closeModal();
  } catch (e: any) {
    console.error("OAuth save error:", e?.response?.data || e);
    const msg =
      typeof e?.response?.data?.detail === "string"
        ? e.response.data.detail
        : "Failed to save OAuth app";
    error.value = msg;
    toast.show(msg, "error");
  } finally {
    saving.value = false;
  }
}

async function removeOAuthApp(id: number) {
  if (!confirm("Delete this OAuth app?")) return;
  try {
    await api.delete(`/oauthapps/${id}`);
    oauthApps.value = oauthApps.value.filter((x) => x.id !== id);
    toast.show("OAuth app deleted", "success");
  } catch (e: any) {
    console.error(e);
    const msg = e.response?.data?.detail || "Failed to delete OAuth app";
    error.value = msg;
    toast.show(msg, "error");
  }
}

onMounted(loadOAuthApps);
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

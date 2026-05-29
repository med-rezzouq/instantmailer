<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <div class="page-title">Tracking Domains</div>
        <div class="page-subtitle">{{ domains.length }} domains</div>
      </div>
      <div class="flex gap-3">
        <button class="btn btn-primary" @click="openAddModal">
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
          Add Tracking Domain
        </button>
      </div>
    </div>

    <div
      class="overflow-x-auto rounded-xl border border-border dark:border-border-dark"
    >
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-surface-off dark:bg-surface-dark-off">
            <th class="th">ID</th>
            <th class="th">Tracking Domain</th>
            <th class="th">Campaign Usage</th>
            <th class="th">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!domains.length">
            <td
              colspan="4"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              No tracking domains yet. Add your first tracking domain above.
            </td>
          </tr>
          <tr
            v-for="d in domains"
            :key="d.id"
            class="hover:bg-surface-off dark:hover:bg-surface-dark-off border-b border-border dark:border-border-dark last:border-0"
          >
            <td class="td text-gray-500 dark:text-gray-400">
              {{ d.id }}
            </td>
            <td class="td font-mono">
              {{ d.domain }}
            </td>
            <td class="td">
              <!-- for now just show comma-separated IDs if present; backend can later fill this -->
              <span v-if="d.campaign_ids && d.campaign_ids.length">
                {{ d.campaign_ids.join(", ") }}
              </span>
              <span v-else class="text-gray-400 dark:text-gray-600"> — </span>
            </td>
            <td class="td">
              <div class="flex gap-2">
                <button class="btn btn-ghost btn-sm" @click="openEditModal(d)">
                  Edit
                </button>
                <button class="btn btn-danger btn-sm" @click="deleteDomain(d)">
                  Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add / Edit Modal (shared) -->
    <Teleport to="body">
      <div v-if="modalOpen" class="modal-overlay" @click.self="closeModal">
        <div class="modal">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-bold">
              {{ editing ? "Edit Tracking Domain" : "Add Tracking Domain" }}
            </h2>
            <button
              @click="closeModal"
              class="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div class="mb-6">
            <label class="form-label">Tracking Domain URL *</label>
            <input
              v-model="form.domain"
              class="form-input"
              placeholder="https://track.example.com"
            />
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Must start with https:// and be a valid domain URL.
            </p>
          </div>

          <div v-if="error" class="mb-4 text-sm text-red-500">
            {{ error }}
          </div>

          <div class="flex gap-3 justify-end">
            <button class="btn btn-ghost" @click="closeModal">Cancel</button>
            <button class="btn btn-primary" @click="saveDomain">
              {{ editing ? "Save Changes" : "Add Domain" }}
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

const domains = ref([]); // [{id, domain, campaign_ids: []}]
const modalOpen = ref(false);
const editing = ref(false);
const currentId = ref(null);
const form = ref({
  domain: "",
});
const error = ref("");

// simple https://domain.tld[/...] validator
function isValidTrackingDomain(value) {
  if (!value) return false;
  if (!value.startsWith("https://")) return false;
  try {
    const url = new URL(value);
    // must have at least something like example.com
    return !!url.hostname && url.protocol === "https:";
  } catch {
    return false;
  }
}
async function load() {
  try {
    const res = await api.get("/tracking/domains");
    console.log("LOAD DOMAINS", res.data);
    domains.value = res.data;
  } catch (e) {
    console.error("LOAD ERROR", e.response || e);
    toast.show("Failed to load tracking domains", "error");
  }
}

onMounted(load);

function openAddModal() {
  editing.value = false;
  currentId.value = null;
  form.value = { domain: "" };
  error.value = "";
  modalOpen.value = true;
}

function openEditModal(domain) {
  editing.value = true;
  currentId.value = domain.id;
  form.value = { domain: domain.domain };
  error.value = "";
  modalOpen.value = true;
}

function closeModal() {
  modalOpen.value = false;
}

async function saveDomain() {
  error.value = "";
  if (!isValidTrackingDomain(form.value.domain)) {
    console.log("Invalid domain:", form.value.domain);
    error.value = "Please enter a valid https://domain.tld URL.";
    return;
  }

  try {
    let res;
    if (editing.value && currentId.value !== null) {
      res = await api.put(`/tracking/domains/${currentId.value}`, {
        domain: form.value.domain,
      });
    } else {
      res = await api.post("/tracking/domains", {
        domain: form.value.domain,
      });
    }
    console.log("SAVE OK", res.data);

    modalOpen.value = false;
    await load();
  } catch (e) {
    console.error("SAVE ERROR", e.response || e);
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}

async function deleteDomain(domain) {
  if (!confirm(`Delete tracking domain "${domain.domain}"?`)) return;
  try {
    await api.delete(`/tracking/domains/${domain.id}`);
    toast.show("Tracking domain deleted", "success");
    await load();
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
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
.modal-overlay {
  @apply fixed inset-0 bg-black/60 z-[200] flex items-center justify-center p-4;
}
.modal {
  @apply bg-surface dark:bg-surface-dark border border-border dark:border-border-dark rounded-2xl p-8 w-full max-w-lg shadow-2xl;
}
</style>

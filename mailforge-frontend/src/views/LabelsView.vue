<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <div class="page-title">Labels</div>
        <div class="page-subtitle">{{ labels.length }} labels</div>
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
          Add Label
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
            <th class="th">Label</th>
            <th class="th">Description</th>
            <th class="th">Created</th>
            <th class="th">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td
              colspan="5"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              Loading...
            </td>
          </tr>

          <tr v-else-if="!labels.length">
            <td
              colspan="5"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              No labels yet. Add your first label above.
            </td>
          </tr>

          <tr
            v-else
            v-for="label in labels"
            :key="label.id"
            class="hover:bg-surface-off dark:hover:bg-surface-dark-off border-b border-border dark:border-border-dark last:border-0"
          >
            <td class="td text-gray-500 dark:text-gray-400">
              {{ label.id }}
            </td>
            <td class="td font-semibold">
              {{ label.name }}
            </td>
            <td class="td text-gray-500 dark:text-gray-400">
              {{ label.description || "—" }}
            </td>
            <td class="td text-gray-500 dark:text-gray-400">
              {{ formatDate(label.created_at) }}
            </td>
            <td class="td">
              <div class="flex gap-2">
                <button
                  class="btn btn-ghost btn-sm"
                  @click="openEditModal(label)"
                >
                  Edit
                </button>
                <button
                  class="btn btn-danger btn-sm"
                  @click="deleteLabel(label)"
                >
                  Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Modal -->
    <Teleport to="body">
      <div v-if="addModal" class="modal-overlay" @click.self="closeAddModal">
        <div class="modal">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-bold">Add Label</h2>
            <button
              @click="closeAddModal"
              class="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div class="mb-4">
            <label class="form-label">Label Name *</label>
            <input
              v-model="newLabel.name"
              class="form-input"
              placeholder="Prospect"
            />
          </div>

          <div class="mb-6">
            <label class="form-label">Description</label>
            <textarea
              v-model="newLabel.description"
              class="form-input"
              rows="4"
              placeholder="Optional description..."
            />
          </div>

          <div class="flex gap-3 justify-end">
            <button class="btn btn-ghost" @click="closeAddModal">Cancel</button>
            <button class="btn btn-primary" @click="addLabel">Add Label</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Edit Modal -->
    <Teleport to="body">
      <div v-if="editModal" class="modal-overlay" @click.self="closeEditModal">
        <div class="modal">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-bold">Edit Label</h2>
            <button
              @click="closeEditModal"
              class="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div class="mb-4">
            <label class="form-label">Label Name *</label>
            <input
              v-model="editLabel.name"
              class="form-input"
              placeholder="Prospect"
            />
          </div>

          <div class="mb-6">
            <label class="form-label">Description</label>
            <textarea
              v-model="editLabel.description"
              class="form-input"
              rows="4"
              placeholder="Optional description..."
            />
          </div>

          <div class="flex gap-3 justify-end">
            <button class="btn btn-ghost" @click="closeEditModal">
              Cancel
            </button>
            <button class="btn btn-primary" @click="updateLabel">Save</button>
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

const labels = ref([]);
const loading = ref(false);

const addModal = ref(false);
const editModal = ref(false);

const newLabel = ref({
  name: "",
  description: "",
});

const editLabel = ref({
  id: null,
  name: "",
  description: "",
});

onMounted(() => {
  loadLabels();
});

async function loadLabels() {
  loading.value = true;
  try {
    const res = await api.get("/labels");
    labels.value = res.data;
  } catch (e) {
    toast.show(e.response?.data?.detail || "Failed to load labels", "error");
  } finally {
    loading.value = false;
  }
}

function openAddModal() {
  newLabel.value = {
    name: "",
    description: "",
  };
  addModal.value = true;
}

function closeAddModal() {
  addModal.value = false;
}

async function addLabel() {
  if (!newLabel.value.name.trim()) {
    toast.show("Label name is required", "error");
    return;
  }

  try {
    await api.post("/labels", {
      name: newLabel.value.name.trim(),
      description: newLabel.value.description?.trim() || null,
    });
    toast.show("Label added!", "success");
    closeAddModal();
    await loadLabels();
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}

function openEditModal(label) {
  editLabel.value = {
    id: label.id,
    name: label.name || "",
    description: label.description || "",
  };
  editModal.value = true;
}

function closeEditModal() {
  editModal.value = false;
}

async function updateLabel() {
  if (!editLabel.value.name.trim()) {
    toast.show("Label name is required", "error");
    return;
  }

  try {
    await api.put(`/labels/${editLabel.value.id}`, {
      name: editLabel.value.name.trim(),
      description: editLabel.value.description?.trim() || null,
    });
    toast.show("Label updated!", "success");
    closeEditModal();
    await loadLabels();
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}

async function deleteLabel(label) {
  if (!confirm(`Delete label "${label.name}"?`)) return;

  try {
    await api.delete(`/labels/${label.id}`);
    toast.show("Label deleted", "success");
    await loadLabels();
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString();
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

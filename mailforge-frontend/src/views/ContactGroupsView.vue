<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <div class="page-title">Contact Groups</div>
        <div class="page-subtitle">{{ groups.length }} groups</div>
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
          Add Group
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
            <th class="th">Name</th>
            <th class="th">Contacts</th>
            <th class="th">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!groups.length">
            <td
              colspan="4"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              No groups yet. Add your first group above.
            </td>
          </tr>
          <tr
            v-for="g in groups"
            :key="g.id"
            class="hover:bg-surface-off dark:hover:bg-surface-dark-off border-b border-border dark:border-border-dark last:border-0"
          >
            <td class="td text-gray-500 dark:text-gray-400">
              {{ g.id }}
            </td>
            <td class="td font-semibold">
              <RouterLink
                :to="`/contacts/${g.id}`"
                class="text-primary hover:underline"
              >
                {{ g.name }}
              </RouterLink>
            </td>
            <td class="td tabular-nums">
              {{ g.contact_count ?? "—" }}
            </td>
            <td class="td">
              <div class="flex gap-2">
                <button class="btn btn-ghost btn-sm" @click="openEditModal(g)">
                  Edit
                </button>
                <button class="btn btn-danger btn-sm" @click="deleteGroup(g)">
                  Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Group Modal -->
    <Teleport to="body">
      <div v-if="addModal" class="modal-overlay" @click.self="closeAddModal">
        <div class="modal">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-bold">Add Group</h2>
            <button
              @click="closeAddModal"
              class="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <div class="mb-6">
            <label class="form-label">Group Name *</label>
            <input
              v-model="newGroup.name"
              class="form-input"
              placeholder="Default, Prospects, Customers..."
            />
          </div>
          <div class="flex gap-3 justify-end">
            <button class="btn btn-ghost" @click="closeAddModal">Cancel</button>
            <button class="btn btn-primary" @click="addGroup">Add Group</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Edit Group Modal -->
    <Teleport to="body">
      <div v-if="editModal" class="modal-overlay" @click.self="closeEditModal">
        <div class="modal">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-bold">Edit Group</h2>
            <button
              @click="closeEditModal"
              class="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <div class="mb-6">
            <label class="form-label">Group Name *</label>
            <input
              v-model="editGroup.name"
              class="form-input"
              placeholder="Group name"
            />
          </div>
          <div class="flex gap-3 justify-end">
            <button class="btn btn-ghost" @click="closeEditModal">
              Cancel
            </button>
            <button class="btn btn-primary" @click="updateGroup">Save</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { RouterLink } from "vue-router";
import api from "@/api";
import { useToastStore } from "@/stores/toast";

const toast = useToastStore();

const groups = ref([]);

const addModal = ref(false);
const editModal = ref(false);

const newGroup = ref({
  name: "",
});

const editGroup = ref({
  id: null,
  name: "",
});

onMounted(load);

async function load() {
  try {
    const res = await api.get("/contacts/groups");
    groups.value = res.data;
  } catch (e) {
    toast.show("Failed to load groups", "error");
  }
}

function openAddModal() {
  newGroup.value = { name: "" };
  addModal.value = true;
}

function closeAddModal() {
  addModal.value = false;
}

async function addGroup() {
  if (!newGroup.value.name.trim()) {
    toast.show("Group name is required", "error");
    return;
  }
  try {
    await api.post("/contacts/groups", newGroup.value);
    toast.show("Group added!", "success");
    addModal.value = false;
    newGroup.value = { name: "" };
    load();
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}

function openEditModal(group) {
  editGroup.value = {
    id: group.id,
    name: group.name,
  };
  editModal.value = true;
}

function closeEditModal() {
  editModal.value = false;
}

async function updateGroup() {
  if (!editGroup.value.name.trim()) {
    toast.show("Group name is required", "error");
    return;
  }
  try {
    await api.put(`/contacts/groups/${editGroup.value.id}`, {
      name: editGroup.value.name,
    });
    toast.show("Group updated!", "success");
    editModal.value = false;
    load();
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}

async function deleteGroup(group) {
  if (!confirm(`Delete group "${group.name}"?`)) return;
  try {
    await api.delete(`/contacts/groups/${group.id}`);
    toast.show("Group deleted", "success");
    load();
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

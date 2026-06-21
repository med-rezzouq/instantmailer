<template>
  <div>
    <!-- ========== GROUPS VIEW (no groupId) ========== -->
    <div v-if="!groupId">
      <div class="flex items-center justify-between mb-6">
        <div>
          <div class="page-title">Contact Groups</div>
          <div class="page-subtitle">{{ groups.length }} groups</div>
        </div>
        <div class="flex gap-3">
          <button class="btn btn-primary" @click="openAddGroupModal">
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

      <!-- Normal groups table -->
      <div
        class="overflow-x-auto rounded-xl border border-border dark:border-border-dark"
      >
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-surface-off dark:bg-surface-dark-off">
              <th class="th">ID</th>
              <th class="th">Name</th>
              <th class="th">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!normalGroups.length">
              <td
                colspan="3"
                class="text-center py-12 text-gray-400 dark:text-gray-600"
              >
                No groups yet. Add your first group above.
              </td>
            </tr>

            <tr
              v-for="g in normalGroups"
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
              <td class="td">
                <div class="flex gap-2">
                  <button
                    class="btn btn-ghost btn-sm"
                    @click="openEditGroupModal(g)"
                  >
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

      <!-- Protected groups table -->
      <div v-if="systemGroups.length" class="mt-8">
        <div class="page-subtitle mb-3">Protected Groups</div>

        <div
          class="overflow-x-auto rounded-xl border border-border dark:border-border-dark"
        >
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-surface-off dark:bg-surface-dark-off">
                <th class="th">ID</th>
                <th class="th">Name</th>
                <th class="th">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="g in systemGroups"
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
                <td class="td">
                  <span class="text-xs text-gray-400 dark:text-gray-500">
                    Protected
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Add Group Modal -->
      <Teleport to="body">
        <div
          v-if="addGroupModal"
          class="modal-overlay"
          @click.self="closeAddGroupModal"
        >
          <div class="modal">
            <div class="flex items-center justify-between mb-6">
              <h2 class="font-bold">Add Group</h2>
              <button
                @click="closeAddGroupModal"
                class="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div class="mb-4">
              <label class="form-label">Group Name *</label>
              <input
                v-model="newGroup.name"
                class="form-input"
                placeholder="Default, Prospects, Customers..."
              />
            </div>

            <div class="mb-6">
              <label class="flex items-center gap-3 cursor-pointer">
                <input
                  v-model="newGroup.is_system"
                  type="checkbox"
                  class="h-4 w-4 rounded border-border dark:border-border-dark"
                />
                <span class="text-sm text-gray-600 dark:text-gray-300">
                  Is system group
                </span>
              </label>
            </div>

            <div class="flex gap-3 justify-end">
              <button class="btn btn-ghost" @click="closeAddGroupModal">
                Cancel
              </button>
              <button class="btn btn-primary" @click="addGroup">
                Add Group
              </button>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- Edit Group Modal -->
      <Teleport to="body">
        <div
          v-if="editGroupModal"
          class="modal-overlay"
          @click.self="closeEditGroupModal"
        >
          <div class="modal">
            <div class="flex items-center justify-between mb-6">
              <h2 class="font-bold">Edit Group</h2>
              <button
                @click="closeEditGroupModal"
                class="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div class="mb-4">
              <label class="form-label">Group Name *</label>
              <input
                v-model="editGroup.name"
                class="form-input"
                placeholder="Group name"
              />
            </div>

            <div class="mb-6">
              <label class="flex items-center gap-3 cursor-pointer">
                <input
                  v-model="editGroup.is_system"
                  type="checkbox"
                  class="h-4 w-4 rounded border-border dark:border-border-dark"
                  :disabled="editGroupLocked"
                />
                <span class="text-sm text-gray-600 dark:text-gray-300">
                  Is system group
                </span>
              </label>
            </div>

            <div class="flex gap-3 justify-end">
              <button class="btn btn-ghost" @click="closeEditGroupModal">
                Cancel
              </button>
              <button
                class="btn btn-primary"
                @click="updateGroup"
                :disabled="editGroupLocked"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      </Teleport>
    </div>

    <!-- ========== CONTACTS VIEW (groupId present) ========== -->
    <div v-else>
      <div class="flex items-center justify-between mb-6">
        <div>
          <div class="page-title">
            Contacts
            <span v-if="groupId" class="text-sm text-gray-400 ml-2">
              (Group: {{ currentGroupName || groupId }})
            </span>
          </div>
          <div class="page-subtitle">{{ contacts.length }} contacts</div>
        </div>
        <div class="flex gap-3">
          <button
            class="btn btn-ghost"
            @click="importModal = true"
            :disabled="!groupId"
          >
            Import CSV
          </button>
          <button
            class="btn btn-primary"
            @click="openAddContactModal"
            :disabled="!groupId"
            :title="
              groupId ? 'Add contact to this group' : 'Select a group first'
            "
          >
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
            Add Contact
          </button>
        </div>
      </div>

      <div class="flex gap-4 mb-5 flex-wrap items-center">
        <div class="relative flex-1 min-w-[200px] max-w-xs">
          <svg
            class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4 pointer-events-none"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            v-model="search"
            @input="loadContacts"
            class="form-input pl-9"
            placeholder="Search contacts..."
            :disabled="!groupId"
          />
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
              <th class="th">Email</th>
              <th class="th">Opens</th>
              <th class="th">Status</th>
              <th class="th">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!contacts.length">
              <td
                colspan="6"
                class="text-center py-12 text-gray-400 dark:text-gray-600"
              >
                No contacts in this group yet. Add your first contact above.
              </td>
            </tr>

            <tr
              v-for="c in contacts"
              :key="c.id"
              class="hover:bg-surface-off dark:hover:bg-surface-dark-off border-b border-border dark:border-border-dark last:border-0"
            >
              <td class="td text-gray-500 dark:text-gray-400">{{ c.id }}</td>
              <td class="td font-semibold">
                {{
                  [c.first_name, c.last_name].filter(Boolean).join(" ") || "—"
                }}
              </td>
              <td class="td text-gray-500 dark:text-gray-400">
                {{ c.email }}
              </td>
              <td class="td tabular-nums">{{ c.open_count }}</td>
              <td class="td">
                <span
                  :class="[
                    'badge',
                    c.is_subscribed ? 'badge-sent' : 'badge-failed',
                  ]"
                >
                  {{ c.is_subscribed ? "Active" : "Unsubscribed" }}
                </span>
              </td>
              <td class="td">
                <button
                  v-if="canDeleteContact(c)"
                  class="btn btn-danger btn-sm"
                  @click="deleteContact(c.id)"
                >
                  Delete
                </button>
                <span v-else class="text-xs text-gray-400 dark:text-gray-500">
                  Protected
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Add Contact Modal -->
      <Teleport to="body">
        <div
          v-if="addModal"
          class="modal-overlay"
          @click.self="closeAddContactModal"
        >
          <div class="modal">
            <div class="flex items-center justify-between mb-6">
              <h2 class="font-bold">Add Contact</h2>
              <button
                @click="closeAddContactModal"
                class="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label class="form-label">First Name</label>
                <input
                  v-model="newContact.first_name"
                  class="form-input"
                  placeholder="John"
                />
              </div>
              <div>
                <label class="form-label">Last Name</label>
                <input
                  v-model="newContact.last_name"
                  class="form-input"
                  placeholder="Doe"
                />
              </div>
            </div>
            <div class="mb-6">
              <label class="form-label">Email *</label>
              <input
                v-model="newContact.email"
                class="form-input"
                type="email"
                placeholder="john@example.com"
              />
            </div>
            <div class="flex gap-3 justify-end">
              <button class="btn btn-ghost" @click="closeAddContactModal">
                Cancel
              </button>
              <button class="btn btn-primary" @click="addContact">
                Add Contact
              </button>
            </div>
          </div>
        </div>
      </Teleport>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";
import api from "@/api";
import { useToastStore } from "@/stores/toast";

const toast = useToastStore();
const route = useRoute();

const groups = ref([]);
const addGroupModal = ref(false);
const editGroupModal = ref(false);

const newGroup = ref({
  name: "",
  is_system: false,
});

const editGroup = ref({
  id: null,
  name: "",
  is_system: false,
});

const contacts = ref([]);
const search = ref("");
const addModal = ref(false);
const importModal = ref(false);

const groupId = ref(null);

const newContact = ref({
  first_name: "",
  last_name: "",
  email: "",
  group_id: null,
  is_system: false,
});

const normalGroups = computed(() => groups.value.filter((g) => !g.is_system));
const systemGroups = computed(() => groups.value.filter((g) => g.is_system));

const currentGroup = computed(
  () =>
    groups.value.find((g) => Number(g.id) === Number(groupId.value)) || null,
);

const currentGroupName = computed(() => currentGroup.value?.name || "");
const editGroupLocked = computed(() => !!editGroup.value.is_system);

const contactGroupMap = computed(() => {
  const map = {};
  groups.value.forEach((g) => {
    map[g.id] = g;
  });
  return map;
});

const canDeleteContact = (contact) => {
  if (contact.is_system) return false;
  const group = contactGroupMap.value[contact.group_id];
  return !group?.is_system;
};

function syncGroupFromRoute() {
  const raw = route.params.groupId;
  const parsed = raw ? Number(raw) : NaN;
  groupId.value = Number.isNaN(parsed) ? null : parsed;
  newContact.value.group_id = groupId.value;
  newContact.value.is_system = !!currentGroup.value?.is_system;
}

onMounted(async () => {
  syncGroupFromRoute();
  await load();
});

watch(
  () => route.params.groupId,
  async () => {
    syncGroupFromRoute();
    await load();
  },
);

async function load() {
  await loadGroups();

  if (groupId.value) {
    await loadContacts();
  } else {
    contacts.value = [];
  }

  newContact.value.group_id = groupId.value;
  newContact.value.is_system = !!currentGroup.value?.is_system;
}

async function loadGroups() {
  try {
    const res = await api.get("/contacts/groups");
    groups.value = res.data;
  } catch (e) {
    toast.show("Failed to load groups", "error");
  }
}

function openAddGroupModal() {
  newGroup.value = { name: "", is_system: false };
  addGroupModal.value = true;
}

function closeAddGroupModal() {
  addGroupModal.value = false;
}

async function addGroup() {
  const name = newGroup.value.name.trim();

  if (!name) {
    toast.show("Group name is required", "error");
    return;
  }

  try {
    await api.post("/contacts/groups", {
      name,
      is_system: newGroup.value.is_system,
    });
    toast.show("Group added!", "success");
    closeAddGroupModal();
    await loadGroups();
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}

function openEditGroupModal(group) {
  if (group.is_system) {
    toast.show("Protected groups cannot be edited", "error");
    return;
  }

  editGroup.value = {
    id: group.id,
    name: group.name,
    is_system: !!group.is_system,
  };
  editGroupModal.value = true;
}

function closeEditGroupModal() {
  editGroupModal.value = false;
}

async function updateGroup() {
  const name = editGroup.value.name.trim();

  if (!name) {
    toast.show("Group name is required", "error");
    return;
  }

  try {
    await api.put(`/contacts/groups/${editGroup.value.id}`, {
      name,
      is_system: editGroup.value.is_system,
    });
    toast.show("Group updated!", "success");
    closeEditGroupModal();
    await loadGroups();
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}

async function deleteGroup(group) {
  if (group.is_system) {
    toast.show("Protected groups cannot be deleted", "error");
    return;
  }

  if (!confirm(`Delete group "${group.name}"?`)) return;

  try {
    await api.delete(`/contacts/groups/${group.id}`);
    toast.show("Group deleted", "success");
    await loadGroups();
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}

async function loadContacts() {
  if (!groupId.value) {
    contacts.value = [];
    return;
  }

  try {
    const params = new URLSearchParams();
    params.set("limit", "200");
    params.set("group_id", String(groupId.value));

    if (search.value) {
      params.set("search", search.value);
    }

    const res = await api.get(`/contacts?${params.toString()}`);
    contacts.value = res.data;
  } catch (e) {
    toast.show("Failed to load contacts", "error");
  }
}

function openAddContactModal() {
  if (!groupId.value) {
    toast.show("Select a group first", "error");
    return;
  }

  newContact.value = {
    first_name: "",
    last_name: "",
    email: "",
    group_id: groupId.value,
    is_system: !!currentGroup.value?.is_system,
  };
  addModal.value = true;
}

function closeAddContactModal() {
  addModal.value = false;
}

async function addContact() {
  const email = newContact.value.email?.trim();

  if (!email) {
    toast.show("Email is required", "error");
    return;
  }

  if (!groupId.value) {
    toast.show("Select a group first", "error");
    return;
  }

  newContact.value.group_id = groupId.value;
  newContact.value.is_system = !!currentGroup.value?.is_system;

  try {
    await api.post("/contacts", {
      email,
      first_name: newContact.value.first_name?.trim() || null,
      last_name: newContact.value.last_name?.trim() || null,
      group_id: newContact.value.group_id,
      is_system: newContact.value.is_system,
    });

    toast.show("Contact added!", "success");
    closeAddContactModal();

    newContact.value = {
      first_name: "",
      last_name: "",
      email: "",
      group_id: groupId.value,
      is_system: !!currentGroup.value?.is_system,
    };

    await loadContacts();
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}

async function deleteContact(id) {
  const contact = contacts.value.find((c) => c.id === id);
  if (!contact) {
    toast.show("Contact not found", "error");
    return;
  }

  if (contact.is_system) {
    toast.show("Cannot delete protected contacts", "error");
    return;
  }

  const group = contactGroupMap.value[contact.group_id];
  if (group?.is_system) {
    toast.show("Cannot delete contacts from protected groups", "error");
    return;
  }

  if (!confirm("Delete this contact?")) return;

  try {
    await api.delete(`/contacts/${id}`);
    toast.show("Deleted", "success");
    await loadContacts();
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

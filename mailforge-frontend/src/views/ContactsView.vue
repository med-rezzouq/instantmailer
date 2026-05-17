<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <div class="page-title">Contacts</div>
        <div class="page-subtitle">{{ contacts.length }} contacts</div>
      </div>
      <div class="flex gap-3">
        <button class="btn btn-ghost" @click="importModal = true">
          Import CSV
        </button>
        <button class="btn btn-primary" @click="addModal = true">
          <svg
            class="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" /></svg
          >Add Contact
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
          @input="load"
          class="form-input pl-9"
          placeholder="Search contacts..."
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
            <!-- 6 columns now (ID + 5 others) -->
            <td
              colspan="6"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              No contacts yet. Add your first contact above.
            </td>
          </tr>
          <tr
            v-for="c in contacts"
            :key="c.id"
            class="hover:bg-surface-off dark:hover:bg-surface-dark-off border-b border-border dark:border-border-dark last:border-0"
          >
            <td class="td text-gray-500 dark:text-gray-400">{{ c.id }}</td>
            <td class="td font-semibold">
              {{ [c.first_name, c.last_name].filter(Boolean).join(" ") || "—" }}
            </td>
            <td class="td text-gray-500 dark:text-gray-400">{{ c.email }}</td>
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
                class="btn btn-danger btn-sm"
                @click="deleteContact(c.id)"
              >
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Modal -->
    <Teleport to="body">
      <div v-if="addModal" class="modal-overlay" @click.self="addModal = false">
        <div class="modal">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-bold">Add Contact</h2>
            <button
              @click="addModal = false"
              class="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label class="form-label">First Name</label
              ><input
                v-model="newContact.first_name"
                class="form-input"
                placeholder="John"
              />
            </div>
            <div>
              <label class="form-label">Last Name</label
              ><input
                v-model="newContact.last_name"
                class="form-input"
                placeholder="Doe"
              />
            </div>
          </div>
          <div class="mb-6">
            <label class="form-label">Email *</label
            ><input
              v-model="newContact.email"
              class="form-input"
              type="email"
              placeholder="john@example.com"
            />
          </div>
          <div class="flex gap-3 justify-end">
            <button class="btn btn-ghost" @click="addModal = false">
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
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "@/api";
import { useToastStore } from "@/stores/toast";

const toast = useToastStore();
const contacts = ref([]);
const search = ref("");
const addModal = ref(false);
const importModal = ref(false);
const newContact = ref({ first_name: "", last_name: "", email: "" });

onMounted(load);
async function load() {
  try {
    contacts.value = (
      await api.get(
        `/contacts?limit=200&search=${encodeURIComponent(search.value)}`,
      )
    ).data;
  } catch (e) {
    toast.show("Failed to load contacts", "error");
  }
}
async function addContact() {
  if (!newContact.value.email) {
    toast.show("Email is required", "error");
    return;
  }
  try {
    await api.post("/contacts", newContact.value);
    toast.show("Contact added!", "success");
    addModal.value = false;
    newContact.value = { first_name: "", last_name: "", email: "" };
    load();
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}
async function deleteContact(id) {
  if (!confirm("Delete this contact?")) return;
  try {
    await api.delete(`/contacts/${id}`);
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
.modal-overlay {
  @apply fixed inset-0 bg-black/60 z-[200] flex items-center justify-center p-4;
}
.modal {
  @apply bg-surface dark:bg-surface-dark border border-border dark:border-border-dark rounded-2xl p-8 w-full max-w-lg shadow-2xl;
}
</style>

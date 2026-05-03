<template>
  <div>
    <div
      class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6"
    >
      <div>
        <div class="page-title">Campaigns</div>
        <div class="page-subtitle">
          All your email campaigns and sequence activity
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button class="btn btn-ghost" @click="load" :disabled="loading">
          <svg
            :class="['w-4 h-4', loading ? 'animate-spin' : '']"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M21 12a9 9 0 1 1-2.64-6.36" />
          </svg>
          Refresh
        </button>

        <RouterLink to="/compose" class="btn btn-primary">
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
          New Campaign
        </RouterLink>
      </div>
    </div>

    <!-- Top stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
      <div class="card">
        <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
          Total Campaigns
        </div>
        <div class="text-2xl font-bold tabular-nums">
          {{ campaigns.length }}
        </div>
      </div>

      <div class="card">
        <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Running</div>
        <div
          class="text-2xl font-bold text-blue-600 dark:text-blue-400 tabular-nums"
        >
          {{ runningCount }}
        </div>
      </div>

      <div class="card">
        <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
          Emails in Sequences
        </div>
        <div
          class="text-2xl font-bold text-primary dark:text-primary-dark tabular-nums"
        >
          {{ totalSequenceEmails }}
        </div>
      </div>

      <div class="card">
        <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
          Total Opens
        </div>
        <div
          class="text-2xl font-bold text-amber-600 dark:text-amber-400 tabular-nums"
        >
          {{ totalOpens }}
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="card mb-4">
      <div class="grid grid-cols-1 md:grid-cols-[1fr_180px_180px] gap-3">
        <div>
          <label class="form-label">Search</label>
          <input
            v-model="search"
            class="form-input"
            placeholder="Search by campaign name or subject..."
          />
        </div>

        <div>
          <label class="form-label">Status</label>
          <select v-model="statusFilter" class="form-input">
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="scheduled">Scheduled</option>
            <option value="running">Running</option>
            <option value="paused">Paused</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        <div>
          <label class="form-label">Provider</label>
          <select v-model="providerFilter" class="form-input">
            <option value="">All providers</option>
            <option value="powermta">PowerMTA</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Desktop table -->
    <div class="card hidden lg:block overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="text-left border-b border-border dark:border-border-dark">
            <th
              class="py-3 px-3 text-xs font-semibold text-gray-500 dark:text-gray-400"
            >
              Campaign
            </th>
            <th
              class="py-3 px-3 text-xs font-semibold text-gray-500 dark:text-gray-400"
            >
              Status
            </th>
            <th
              class="py-3 px-3 text-xs font-semibold text-gray-500 dark:text-gray-400"
            >
              Sequence
            </th>
            <th
              class="py-3 px-3 text-xs font-semibold text-gray-500 dark:text-gray-400"
            >
              Follow-ups
            </th>
            <th
              class="py-3 px-3 text-xs font-semibold text-gray-500 dark:text-gray-400"
            >
              PowerMTA
            </th>
            <th
              class="py-3 px-3 text-xs font-semibold text-gray-500 dark:text-gray-400"
            >
              Opens
            </th>
            <th
              class="py-3 px-3 text-xs font-semibold text-gray-500 dark:text-gray-400"
            >
              Created
            </th>
            <th
              class="py-3 px-3 text-xs font-semibold text-gray-500 dark:text-gray-400 text-right"
            >
              Actions
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-if="loading">
            <td
              colspan="8"
              class="py-10 text-center text-sm text-gray-400 dark:text-gray-500"
            >
              Loading campaigns...
            </td>
          </tr>

          <tr v-else-if="!filteredCampaigns.length">
            <td
              colspan="8"
              class="py-10 text-center text-sm text-gray-400 dark:text-gray-500"
            >
              No campaigns found
            </td>
          </tr>

          <tr
            v-for="c in filteredCampaigns"
            :key="c.id"
            class="border-b border-border dark:border-border-dark last:border-b-0 hover:bg-surface-off dark:hover:bg-surface-dark-off transition-colors"
          >
            <td class="py-4 px-3 min-w-[240px]">
              <div class="font-semibold text-sm">
                {{ c.name || "Untitled campaign" }}
              </div>
              <div
                class="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[280px]"
              >
                {{ c.subject || "No subject" }}
              </div>
            </td>

            <td class="py-4 px-3">
              <span
                :class="statusBadgeClass(c.status)"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
              >
                <span
                  class="w-1.5 h-1.5 rounded-full bg-current opacity-80"
                ></span>
                {{ normalizeText(c.status || "draft") }}
              </span>
            </td>

            <td class="py-4 px-3">
              <div class="flex flex-col gap-1">
                <span
                  :class="sequenceBadgeClass(c)"
                  class="inline-flex w-fit items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
                >
                  {{ getSequenceLabel(c) }}
                </span>
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  {{ getTotalEmails(c) }} email{{
                    getTotalEmails(c) > 1 ? "s" : ""
                  }}
                </span>
              </div>
            </td>

            <td class="py-4 px-3">
              <div class="text-sm font-semibold tabular-nums">
                {{ getFollowupCount(c) }}
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400">
                configured
              </div>
            </td>

            <td class="py-4 px-3">
              <div class="flex flex-col gap-1">
                <span
                  :class="powermtaBadgeClass(c)"
                  class="inline-flex w-fit items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
                >
                  {{ getPowerMtaLabel(c) }}
                </span>
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  {{ getProviderName(c) }}
                </span>
              </div>
            </td>

            <td class="py-4 px-3">
              <div class="flex items-center gap-2">
                <span class="text-sm font-semibold tabular-nums">{{
                  getOpenCount(c)
                }}</span>
                <span
                  :class="openLabelClass(c)"
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium"
                >
                  {{ getOpenLabel(c) }}
                </span>
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400">
                {{ getOpenRate(c) }}% open rate
              </div>
            </td>

            <td class="py-4 px-3">
              <div class="text-sm">{{ formatDate(c.created_at) }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">
                {{ formatTimeAgo(c.created_at) }}
              </div>
            </td>

            <td class="py-4 px-3">
              <div class="flex items-center justify-end gap-2">
                <button
                  class="btn btn-ghost btn-sm"
                  @click="viewStats(c)"
                  title="View stats"
                >
                  Stats
                </button>

                <button
                  v-if="canSend(c)"
                  class="btn btn-primary btn-sm"
                  @click="sendCampaign(c.id)"
                >
                  Send
                </button>

                <button
                  class="btn btn-ghost btn-sm text-red-500 hover:text-red-600"
                  @click="deleteCampaign(c.id)"
                >
                  Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile cards -->
    <div class="lg:hidden space-y-3">
      <div v-if="loading" class="card text-sm text-gray-400 dark:text-gray-500">
        Loading campaigns...
      </div>

      <div
        v-else-if="!filteredCampaigns.length"
        class="card text-sm text-gray-400 dark:text-gray-500"
      >
        No campaigns found
      </div>

      <div v-for="c in filteredCampaigns" :key="c.id" class="card">
        <div class="flex items-start justify-between gap-3 mb-3">
          <div class="min-w-0">
            <div class="font-semibold text-sm truncate">
              {{ c.name || "Untitled campaign" }}
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400 truncate">
              {{ c.subject || "No subject" }}
            </div>
          </div>

          <span
            :class="statusBadgeClass(c.status)"
            class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium shrink-0"
          >
            <span class="w-1.5 h-1.5 rounded-full bg-current opacity-80"></span>
            {{ normalizeText(c.status || "draft") }}
          </span>
        </div>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div class="rounded-lg bg-surface-off dark:bg-surface-dark-off p-3">
            <div class="text-[11px] text-gray-500 dark:text-gray-400 mb-1">
              Sequence
            </div>
            <div
              :class="sequenceBadgeClass(c)"
              class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium"
            >
              {{ getSequenceLabel(c) }}
            </div>
            <div class="text-xs mt-1 text-gray-500 dark:text-gray-400">
              {{ getFollowupCount(c) }} follow-ups
            </div>
          </div>

          <div class="rounded-lg bg-surface-off dark:bg-surface-dark-off p-3">
            <div class="text-[11px] text-gray-500 dark:text-gray-400 mb-1">
              PowerMTA
            </div>
            <div
              :class="powermtaBadgeClass(c)"
              class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium"
            >
              {{ getPowerMtaLabel(c) }}
            </div>
            <div class="text-xs mt-1 text-gray-500 dark:text-gray-400">
              {{ getProviderName(c) }}
            </div>
          </div>

          <div class="rounded-lg bg-surface-off dark:bg-surface-dark-off p-3">
            <div class="text-[11px] text-gray-500 dark:text-gray-400 mb-1">
              Opens
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm font-semibold tabular-nums">{{
                getOpenCount(c)
              }}</span>
              <span
                :class="openLabelClass(c)"
                class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium"
              >
                {{ getOpenLabel(c) }}
              </span>
            </div>
            <div class="text-xs mt-1 text-gray-500 dark:text-gray-400">
              {{ getOpenRate(c) }}% rate
            </div>
          </div>

          <div class="rounded-lg bg-surface-off dark:bg-surface-dark-off p-3">
            <div class="text-[11px] text-gray-500 dark:text-gray-400 mb-1">
              Created
            </div>
            <div class="text-sm">{{ formatDate(c.created_at) }}</div>
            <div class="text-xs mt-1 text-gray-500 dark:text-gray-400">
              {{ formatTimeAgo(c.created_at) }}
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button class="btn btn-ghost btn-sm flex-1" @click="viewStats(c)">
            Stats
          </button>
          <button
            v-if="canSend(c)"
            class="btn btn-primary btn-sm flex-1"
            @click="sendCampaign(c.id)"
          >
            Send
          </button>
          <button
            class="btn btn-ghost btn-sm text-red-500"
            @click="deleteCampaign(c.id)"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import api from "@/api";
import { useToastStore } from "@/stores/toast";

const toast = useToastStore();

const campaigns = ref([]);
const loading = ref(false);
const search = ref("");
const statusFilter = ref("");
const providerFilter = ref("");

onMounted(load);

async function load() {
  loading.value = true;
  try {
    campaigns.value = (await api.get("/campaigns?limit=100")).data;
  } catch (e) {
    toast.show("Failed to load campaigns", "error");
  } finally {
    loading.value = false;
  }
}

const filteredCampaigns = computed(() => {
  return campaigns.value.filter((c) => {
    const q = search.value.trim().toLowerCase();
    const matchesSearch =
      !q ||
      (c.name || "").toLowerCase().includes(q) ||
      (c.subject || "").toLowerCase().includes(q);

    const matchesStatus =
      !statusFilter.value ||
      (c.status || "").toLowerCase() === statusFilter.value;
    const matchesProvider =
      !providerFilter.value ||
      getProviderName(c).toLowerCase() === providerFilter.value;

    return matchesSearch && matchesStatus && matchesProvider;
  });
});

const runningCount = computed(
  () =>
    campaigns.value.filter((c) =>
      ["running", "sending", "in_progress"].includes(
        (c.status || "").toLowerCase(),
      ),
    ).length,
);

const totalSequenceEmails = computed(() =>
  campaigns.value.reduce((sum, c) => sum + getTotalEmails(c), 0),
);

const totalOpens = computed(() =>
  campaigns.value.reduce((sum, c) => sum + getOpenCount(c), 0),
);

function getFollowupCount(c) {
  if (Array.isArray(c.followups)) return c.followups.length;
  if (Array.isArray(c.steps)) return Math.max(c.steps.length - 1, 0);
  if (typeof c.followup_count === "number") return c.followup_count;
  if (typeof c.steps_count === "number") return Math.max(c.steps_count - 1, 0);
  return 0;
}

function getTotalEmails(c) {
  return 1 + getFollowupCount(c);
}

function getProviderName(c) {
  return c.provider || c.mail_provider || "powermta";
}

function getSequenceLabel(c) {
  const count = getFollowupCount(c);
  if (count <= 0) return "Single email";
  if (count === 1) return "2-step sequence";
  return `${count + 1}-step sequence`;
}

function getPowerMtaLabel(c) {
  const status = (c.status || "").toLowerCase();

  if (["running", "sending", "in_progress"].includes(status))
    return "Launching";
  if (["completed", "sent"].includes(status)) return "Delivered";
  if (["paused"].includes(status)) return "Paused";
  if (["failed", "error"].includes(status)) return "Issue";
  return "Ready";
}

function getOpenCount(c) {
  if (typeof c.opens_count === "number") return c.opens_count;
  if (typeof c.opens === "number") return c.opens;
  if (typeof c.total_opens === "number") return c.total_opens;
  if (typeof c.open_count === "number") return c.open_count;
  return 0;
}

function getRecipientsCount(c) {
  if (typeof c.recipients_count === "number") return c.recipients_count;
  if (typeof c.contacts_count === "number") return c.contacts_count;
  if (typeof c.sent_count === "number") return c.sent_count;
  return 0;
}

function getOpenRate(c) {
  const opens = getOpenCount(c);
  const recipients = getRecipientsCount(c);
  if (!recipients) return 0;
  return Math.round((opens / recipients) * 100);
}

function getOpenLabel(c) {
  const opens = getOpenCount(c);
  const rate = getOpenRate(c);

  if (opens === 0) return "Cold";
  if (rate >= 50 || opens >= 50) return "Hot";
  if (rate >= 20 || opens >= 10) return "Warm";
  return "Low";
}

function canSend(c) {
  const status = (c.status || "").toLowerCase();
  return ["draft", "scheduled", "paused"].includes(status);
}

function normalizeText(v) {
  return String(v || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (m) => m.toUpperCase());
}

function statusBadgeClass(status) {
  const s = (status || "").toLowerCase();

  if (["running", "sending", "in_progress"].includes(s)) {
    return "text-blue-700 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20";
  }
  if (["completed", "sent"].includes(s)) {
    return "text-green-700 bg-green-50 dark:text-green-400 dark:bg-green-900/20";
  }
  if (["paused"].includes(s)) {
    return "text-amber-700 bg-amber-50 dark:text-amber-400 dark:bg-amber-900/20";
  }
  if (["failed", "error"].includes(s)) {
    return "text-red-700 bg-red-50 dark:text-red-400 dark:bg-red-900/20";
  }

  return "text-gray-700 bg-gray-100 dark:text-gray-300 dark:bg-gray-800";
}

function sequenceBadgeClass(c) {
  const count = getFollowupCount(c);

  if (count >= 3)
    return "text-primary bg-primary/10 dark:text-primary-dark dark:bg-primary-dark/20";
  if (count >= 1)
    return "text-blue-700 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20";
  return "text-gray-700 bg-gray-100 dark:text-gray-300 dark:bg-gray-800";
}

function powermtaBadgeClass(c) {
  const label = getPowerMtaLabel(c);

  if (label === "Launching")
    return "text-blue-700 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20";
  if (label === "Delivered")
    return "text-green-700 bg-green-50 dark:text-green-400 dark:bg-green-900/20";
  if (label === "Paused")
    return "text-amber-700 bg-amber-50 dark:text-amber-400 dark:bg-amber-900/20";
  if (label === "Issue")
    return "text-red-700 bg-red-50 dark:text-red-400 dark:bg-red-900/20";
  return "text-primary bg-primary/10 dark:text-primary-dark dark:bg-primary-dark/20";
}

function openLabelClass(c) {
  const label = getOpenLabel(c);

  if (label === "Hot")
    return "text-green-700 bg-green-50 dark:text-green-400 dark:bg-green-900/20";
  if (label === "Warm")
    return "text-amber-700 bg-amber-50 dark:text-amber-400 dark:bg-amber-900/20";
  if (label === "Low")
    return "text-blue-700 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20";
  return "text-gray-700 bg-gray-100 dark:text-gray-300 dark:bg-gray-800";
}

function formatDate(value) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleDateString();
  } catch {
    return "—";
  }
}

function formatTimeAgo(value) {
  if (!value) return "Unknown";
  const d = new Date(value);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

async function sendCampaign(id) {
  if (!confirm("Send this campaign?")) return;
  try {
    await api.post(`/campaigns/${id}/send`);
    toast.show("Campaign sending!", "success");
    load();
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}

async function deleteCampaign(id) {
  if (!confirm("Delete this campaign?")) return;
  try {
    await api.delete(`/campaigns/${id}`);
    toast.show("Deleted", "success");
    load();
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}

function viewStats(c) {
  alert(`Stats for "${c.name}" — coming soon`);
}
</script>

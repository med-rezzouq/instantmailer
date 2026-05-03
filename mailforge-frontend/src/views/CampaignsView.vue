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
            <option value="microsoft">Microsoft</option>
            <option value="google">Google</option>
          </select>
        </div>
      </div>
    </div>

    <CampaignsTable
      :campaigns="filteredCampaigns"
      :loading="loading"
      @send="sendCampaign"
      @delete="deleteCampaign"
      @stats="viewStats"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import CampaignsTable from "@/components/CampaignsTable.vue";
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

function getOpenCount(c) {
  if (typeof c.opens_count === "number") return c.opens_count;
  if (typeof c.opens === "number") return c.opens;
  if (typeof c.total_opens === "number") return c.total_opens;
  if (typeof c.open_count === "number") return c.open_count;
  return 0;
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
